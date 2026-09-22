"""Rate limiting, caching and retry behaviour.

The SEC asks for no more than 10 requests per second and blocks IP addresses
that ignore it. "We are polite" is not a control; a token bucket with a test is.

Most of these tests drive an injected clock rather than the wall clock, so they
assert the arithmetic exactly and run instantly. One test does use real time,
because a bucket that is correct on a fake clock and never actually sleeps is
still broken.
"""

from __future__ import annotations

import asyncio
import time

import httpx
import pytest

from edgar_mcp.client import (
    COMPANY_TICKERS_URL,
    MAX_REQUESTS_PER_SECOND,
    ResponseCache,
    SECClient,
    TokenBucket,
)
from edgar_mcp.errors import RateLimitError, UpstreamUnavailableError


class FakeClock:
    """A monotonic clock the test advances by hand."""

    def __init__(self) -> None:
        """Start at zero."""
        self.now = 0.0

    def __call__(self) -> float:
        """Return the current fake time.

        Returns:
            Seconds since the clock was created.
        """
        return self.now

    def advance(self, seconds: float) -> None:
        """Move the clock forward.

        Args:
            seconds: How far to advance.
        """
        self.now += seconds


# --------------------------------------------------------------------------- #
# The bucket
# --------------------------------------------------------------------------- #


def test_bucket_starts_full_and_drains() -> None:
    clock = FakeClock()
    bucket = TokenBucket(rate=10, capacity=5, time_fn=clock)
    assert bucket.tokens == 5
    for _ in range(5):
        assert bucket.try_acquire() is True
    assert bucket.try_acquire() is False


def test_bucket_refills_at_exactly_the_configured_rate() -> None:
    clock = FakeClock()
    bucket = TokenBucket(rate=10, capacity=5, time_fn=clock)
    for _ in range(5):
        bucket.try_acquire()
    clock.advance(0.3)  # 3 tokens at 10/s
    assert bucket.tokens == pytest.approx(3.0)
    clock.advance(10.0)  # would be 100 tokens, but capacity is 5
    assert bucket.tokens == pytest.approx(5.0)


def test_time_until_available_is_the_exact_shortfall() -> None:
    clock = FakeClock()
    bucket = TokenBucket(rate=10, capacity=2, time_fn=clock)
    bucket.try_acquire()
    bucket.try_acquire()
    assert bucket.time_until_available(1) == pytest.approx(0.1)
    assert bucket.time_until_available(2) == pytest.approx(0.2)
    clock.advance(0.05)
    assert bucket.time_until_available(1) == pytest.approx(0.05)


def test_requesting_more_than_capacity_is_an_error_not_a_hang() -> None:
    bucket = TokenBucket(rate=10, capacity=2)
    with pytest.raises(ValueError, match="capacity"):
        bucket.time_until_available(3)


def test_a_bucket_cannot_be_configured_faster_than_the_sec_allows() -> None:
    with pytest.raises(ValueError, match="10"):
        SECClient(requests_per_second=50)


def test_bucket_actually_sleeps_on_the_real_clock() -> None:
    # 20 requests through a 1-token bucket at 20/s must take at least the 19
    # refill intervals. Slack of one interval absorbs scheduler jitter.
    async def drain() -> float:
        bucket = TokenBucket(rate=20, capacity=1)
        started = time.monotonic()
        for _ in range(20):
            await bucket.acquire()
        return time.monotonic() - started

    elapsed = asyncio.run(drain())
    assert elapsed >= 18 / 20


def test_concurrent_callers_share_one_budget() -> None:
    # Ten coroutines racing through a 5-token bucket must still be limited: the
    # five that miss the burst wait for a refill. Without the lock, all ten
    # would observe the same free tokens and proceed at once.
    async def race() -> float:
        bucket = TokenBucket(rate=10, capacity=5)
        started = time.monotonic()
        await asyncio.gather(*(bucket.acquire() for _ in range(10)))
        return time.monotonic() - started

    elapsed = asyncio.run(race())
    assert elapsed >= 0.4


def test_client_defaults_to_the_sec_ceiling() -> None:
    client = SECClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))
    assert client.bucket.rate == MAX_REQUESTS_PER_SECOND


# --------------------------------------------------------------------------- #
# The cache
# --------------------------------------------------------------------------- #


def test_a_repeated_url_is_served_from_disk(tmp_path, sec_client: SECClient) -> None:
    async def fetch_twice() -> None:
        await sec_client.company_tickers()
        await sec_client.company_tickers()

    asyncio.run(fetch_twice())
    assert sec_client.request_count == 1
    assert sec_client.cache_hits == 1


def test_no_cache_client_refetches_every_time(tmp_path) -> None:
    client = SECClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"0": {"cik_str": 1, "ticker": "A", "title": "A"}})
        ),
        cache_dir=tmp_path / ".cache",
        use_cache=False,
    )

    async def fetch_twice() -> None:
        await client.company_tickers()
        await client.company_tickers()

    asyncio.run(fetch_twice())
    assert client.request_count == 2
    assert client.cache_hits == 0
    assert not (tmp_path / ".cache").exists()


def test_cache_key_is_the_whole_url(tmp_path) -> None:
    cache = ResponseCache(tmp_path / ".cache")
    cache.put("https://example.test/a?q=1", {"v": 1})
    assert cache.get("https://example.test/a?q=1") == {"v": 1}
    assert cache.get("https://example.test/a?q=2") is None


def test_expired_cache_entries_are_a_miss(tmp_path) -> None:
    cache = ResponseCache(tmp_path / ".cache", ttl_seconds=0.05)
    cache.put(COMPANY_TICKERS_URL, {"v": 1})
    assert cache.get(COMPANY_TICKERS_URL) == {"v": 1}
    time.sleep(0.06)
    assert cache.get(COMPANY_TICKERS_URL) is None


def test_a_corrupt_cache_file_is_a_miss_not_a_crash(tmp_path) -> None:
    cache = ResponseCache(tmp_path / ".cache")
    path = cache.path_for(COMPANY_TICKERS_URL)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ this is not json", encoding="utf-8")
    assert cache.get(COMPANY_TICKERS_URL) is None


# --------------------------------------------------------------------------- #
# Retries
# --------------------------------------------------------------------------- #


def _counting_transport(statuses: list[int]) -> tuple[httpx.MockTransport, list[int]]:
    """Build a transport that returns each status in turn.

    Args:
        statuses: Status codes to return, one per request. The last one repeats.

    Returns:
        The transport and a list that records how many calls were made.
    """
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        index = min(len(calls), len(statuses) - 1)
        calls.append(index)
        status = statuses[index]
        if status == 200:
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(status, json={"error": status})

    return httpx.MockTransport(handler), calls


def test_a_429_is_retried_and_then_succeeds(tmp_path) -> None:
    transport, calls = _counting_transport([429, 429, 200])
    client = SECClient(
        transport=transport,
        cache_dir=tmp_path / ".cache",
        backoff_base=0.001,
        burst=10,
    )
    body = asyncio.run(client.get_json("https://data.sec.gov/test.json"))
    assert body == {"ok": True}
    assert len(calls) == 3


def test_a_persistent_429_becomes_a_typed_rate_limit_error(tmp_path) -> None:
    transport, _ = _counting_transport([429])
    client = SECClient(
        transport=transport,
        cache_dir=tmp_path / ".cache",
        max_retries=2,
        backoff_base=0.001,
        burst=10,
    )
    with pytest.raises(RateLimitError) as excinfo:
        asyncio.run(client.get_json("https://data.sec.gov/test.json"))
    assert excinfo.value.status_code == 429
    assert "rate limit" in excinfo.value.suggestion.lower()


def test_a_503_is_retried_then_reported_as_unavailable(tmp_path) -> None:
    transport, calls = _counting_transport([503])
    client = SECClient(
        transport=transport,
        cache_dir=tmp_path / ".cache",
        max_retries=2,
        backoff_base=0.001,
        burst=10,
    )
    with pytest.raises(UpstreamUnavailableError):
        asyncio.run(client.get_json("https://data.sec.gov/test.json"))
    assert len(calls) == 3


def test_retry_after_header_is_honoured(tmp_path) -> None:
    transport = httpx.MockTransport(
        lambda r: httpx.Response(429, headers={"Retry-After": "2.5"}, json={})
    )
    client = SECClient(transport=transport, cache_dir=tmp_path / ".cache")
    response = httpx.Response(429, headers={"Retry-After": "2.5"})
    assert client._retry_delay(response, 0) == pytest.approx(2.5)
    # A nonsense header falls back to exponential backoff rather than crashing.
    assert client._retry_delay(httpx.Response(429, headers={"Retry-After": "soon"}), 1) > 0


def test_failed_responses_are_never_cached(tmp_path) -> None:
    transport, _ = _counting_transport([503])
    client = SECClient(
        transport=transport,
        cache_dir=tmp_path / ".cache",
        max_retries=0,
        backoff_base=0.001,
    )
    with pytest.raises(UpstreamUnavailableError):
        asyncio.run(client.get_json("https://data.sec.gov/test.json"))
    assert client.cache.get("https://data.sec.gov/test.json") is None


def test_the_user_agent_is_set_on_every_request(tmp_path) -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("user-agent", ""))
        return httpx.Response(200, json={})

    client = SECClient(
        user_agent="Arnav arnavhpd@gmail.com",
        transport=httpx.MockTransport(handler),
        cache_dir=tmp_path / ".cache",
        use_cache=False,
    )

    async def fetch() -> None:
        await client.get_json("https://data.sec.gov/a.json")
        await client.get_json("https://data.sec.gov/b.json")

    asyncio.run(fetch())
    assert seen == ["Arnav arnavhpd@gmail.com"] * 2
