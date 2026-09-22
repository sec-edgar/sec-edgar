"""The single HTTP path to SEC EDGAR.

Everything that talks to sec.gov goes through :class:`SECClient`. That is not
tidiness for its own sake — three requirements only hold if there is exactly
one place they can be enforced:

* **User-Agent.** The SEC returns ``403 Forbidden`` to any request that does
  not identify a human being. The header is set in :meth:`SECClient._headers`
  and nowhere else in this repository.
* **Rate limit.** The SEC asks for no more than 10 requests per second. This is
  enforced with a token bucket, not with ``sleep`` calls sprinkled at call
  sites, because a comparison across five companies fans out into a dozen
  concurrent requests and politeness does not survive concurrency.
* **Cache.** Every response is written to disk keyed by a hash of the URL. Eval
  runs are otherwise neither reproducible nor cheap, and a 25-question set run
  three times is roughly 900 HTTP requests against a public service.

Endpoints used, all of them free and unauthenticated:

* ``https://www.sec.gov/files/company_tickers.json`` — ticker to CIK map
* ``https://data.sec.gov/submissions/CIK##########.json`` — filing history
* ``https://data.sec.gov/api/xbrl/companyconcept/CIK##########/{taxonomy}/{tag}.json``
* ``https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json``
* ``https://efts.sec.gov/LATEST/search-index`` — full-text search backend
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

from .errors import (
    NotFoundError,
    RateLimitError,
    SECError,
    UpstreamUnavailableError,
)

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

#: SEC requires "<name> <email>". A request without it gets a 403, every time.
#: Override with EDGAR_MCP_USER_AGENT. This default is the repository owner's.
DEFAULT_USER_AGENT = "Arnav arnavhpd@gmail.com"

#: SEC's published ceiling is 10 requests/second. We do not run at the ceiling.
MAX_REQUESTS_PER_SECOND = 10.0

#: Burst size. Small enough that a fan-out cannot spend a whole second of
#: budget in one instant, large enough that sequential calls are not stalled.
DEFAULT_BURST = 5.0

COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
COMPANY_CONCEPT_URL = (
    "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{tag}.json"
)
COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

#: The JSON backend behind https://www.sec.gov/edgar/search/. It is not part of
#: SEC's documented API surface and its response shape has changed before, so
#: filings.search_full_text parses it defensively.
FULL_TEXT_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_RETRIES = 4

#: Statuses worth retrying. 429 is throttling; 503 and friends are EDGAR
#: maintenance windows, which are frequent and short.
RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


# --------------------------------------------------------------------------- #
# Rate limiting
# --------------------------------------------------------------------------- #


class TokenBucket:
    """A token bucket that caps sustained throughput at ``rate`` per second.

    Tokens accumulate continuously at ``rate`` per second up to ``capacity``.
    Taking a token costs one; when the bucket is empty a caller waits exactly
    long enough for one to refill. Sustained rate can therefore never exceed
    ``rate``, while a short burst up to ``capacity`` is allowed.

    The clock and the sleep function are injectable so the timing behaviour can
    be tested deterministically instead of by measuring wall time.

    Attributes:
        rate: Tokens added per second.
        capacity: Maximum tokens the bucket holds.
    """

    def __init__(
        self,
        rate: float = MAX_REQUESTS_PER_SECOND,
        capacity: float | None = None,
        *,
        time_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        """Create a bucket that starts full.

        Args:
            rate: Sustained requests per second. Must be positive.
            capacity: Burst size. Defaults to ``rate``.
            time_fn: Monotonic clock, injectable for tests.

        Raises:
            ValueError: If ``rate`` or ``capacity`` is not positive.
        """
        if rate <= 0:
            raise ValueError("rate must be positive")
        capacity = rate if capacity is None else capacity
        if capacity <= 0:
            raise ValueError("capacity must be positive")

        self.rate = float(rate)
        self.capacity = float(capacity)
        self._tokens = float(capacity)
        self._time_fn = time_fn
        self._updated_at = time_fn()
        # Created lazily and rebuilt if the event loop changes. An asyncio.Lock
        # binds to the loop that first awaits it, and this object is built at
        # import time, outside any loop.
        self._lock: asyncio.Lock | None = None
        self._lock_loop: asyncio.AbstractEventLoop | None = None

    @property
    def tokens(self) -> float:
        """Current token count, after accounting for elapsed time."""
        self._refill()
        return self._tokens

    def _refill(self) -> None:
        """Add the tokens that have accrued since the last check."""
        now = self._time_fn()
        elapsed = now - self._updated_at
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            self._updated_at = now

    def try_acquire(self, tokens: float = 1.0) -> bool:
        """Take tokens if they are available right now.

        Args:
            tokens: How many to take.

        Returns:
            True if the tokens were taken, False if the bucket was short.
        """
        self._refill()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

    def time_until_available(self, tokens: float = 1.0) -> float:
        """Seconds to wait before ``tokens`` can be taken.

        Args:
            tokens: How many tokens the caller wants.

        Returns:
            A non-negative wait in seconds. Zero when the tokens are ready.

        Raises:
            ValueError: If ``tokens`` exceeds the bucket's capacity, which
                would otherwise wait forever.
        """
        if tokens > self.capacity:
            raise ValueError(
                f"cannot request {tokens} tokens from a bucket of capacity {self.capacity}"
            )
        self._refill()
        if self._tokens >= tokens:
            return 0.0
        return (tokens - self._tokens) / self.rate

    async def acquire(self, tokens: float = 1.0) -> None:
        """Wait until ``tokens`` are available, then take them.

        The lock serialises waiters so two coroutines cannot both observe the
        same free token and both proceed.

        Args:
            tokens: How many tokens to take.
        """
        loop = asyncio.get_running_loop()
        if self._lock is None or self._lock_loop is not loop:
            self._lock = asyncio.Lock()
            self._lock_loop = loop
        async with self._lock:
            while True:
                wait = self.time_until_available(tokens)
                if wait <= 0:
                    self._tokens -= tokens
                    return
                await asyncio.sleep(wait)


# --------------------------------------------------------------------------- #
# On-disk cache
# --------------------------------------------------------------------------- #


class ResponseCache:
    """A flat on-disk cache of SEC responses, keyed by a hash of the URL.

    Deliberately not a database. One JSON file per URL, in ``.cache/``, holding
    the body plus the URL and fetch time so a human can read a cache entry and
    tell what it is and how stale it is.

    Attributes:
        directory: Where cache files are written.
        ttl_seconds: Entries older than this are treated as missing. Zero
            disables expiry.
        enabled: When False, every read misses and no write happens.
    """

    def __init__(
        self,
        directory: str | Path = ".cache",
        *,
        ttl_seconds: float = 0.0,
        enabled: bool = True,
    ) -> None:
        """Configure the cache.

        Args:
            directory: Cache directory. Created on first write.
            ttl_seconds: Expiry in seconds; 0 means entries never expire.
            enabled: Set False for ``--no-cache``.
        """
        self.directory = Path(directory)
        self.ttl_seconds = float(ttl_seconds)
        self.enabled = enabled

    def path_for(self, url: str) -> Path:
        """Return the cache file path for a URL.

        Args:
            url: The absolute request URL, including any query string.

        Returns:
            Path to the JSON file that would hold this URL's response.
        """
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
        return self.directory / f"{digest}.json"

    def get(self, url: str) -> Any | None:
        """Read a cached body.

        Args:
            url: The request URL.

        Returns:
            The cached body, or None on a miss, an expired entry, or a
            corrupted file. A corrupted file is a miss, never an error.
        """
        if not self.enabled:
            return None
        path = self.path_for(url)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if self.ttl_seconds > 0:
            age = time.time() - float(raw.get("fetched_at", 0))
            if age > self.ttl_seconds:
                logger.debug("cache entry expired (%.0fs old): %s", age, url)
                return None
        return raw.get("body")

    def put(self, url: str, body: Any) -> None:
        """Write a response body to the cache.

        A cache write failure is logged and swallowed. Losing the cache is
        slow; failing the user's question because the disk is full is worse.

        Args:
            url: The request URL.
            body: The parsed JSON body or the raw text.
        """
        if not self.enabled:
            return
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            payload = {"url": url, "fetched_at": time.time(), "body": body}
            self.path_for(url).write_text(
                json.dumps(payload, separators=(",", ":")), encoding="utf-8"
            )
        except OSError as exc:
            logger.warning("could not write cache entry for %s: %s", url, exc)


# --------------------------------------------------------------------------- #
# The client
# --------------------------------------------------------------------------- #


class SECClient:
    """Async HTTP client for SEC EDGAR with rate limiting, caching and retries.

    Attributes:
        user_agent: The exact ``User-Agent`` sent on every request.
        cache: The on-disk response cache.
        bucket: The shared token bucket.
    """

    def __init__(
        self,
        user_agent: str | None = None,
        *,
        cache: ResponseCache | None = None,
        cache_dir: str | Path | None = None,
        use_cache: bool = True,
        cache_ttl_seconds: float | None = None,
        requests_per_second: float = MAX_REQUESTS_PER_SECOND,
        burst: float = DEFAULT_BURST,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        transport: httpx.AsyncBaseTransport | None = None,
        backoff_base: float = 0.5,
        sleep_fn: Callable[[float], Any] | None = None,
    ) -> None:
        """Build a client.

        Args:
            user_agent: Overrides ``EDGAR_MCP_USER_AGENT`` and the default.
            cache: A pre-built cache. Overrides ``cache_dir``/``use_cache``.
            cache_dir: Cache directory; defaults to ``EDGAR_MCP_CACHE_DIR``.
            use_cache: False is the ``--no-cache`` behaviour.
            cache_ttl_seconds: Entry expiry; defaults to
                ``EDGAR_MCP_CACHE_TTL_SECONDS``, and 0 means never expire.
            requests_per_second: Sustained cap. Never set above 10.
            burst: Token bucket capacity.
            timeout: Per-request timeout in seconds.
            max_retries: Attempts after the first for retryable statuses.
            transport: Injected httpx transport; tests pass a MockTransport.
            backoff_base: First backoff delay; doubles each attempt.
            sleep_fn: Injected async sleep, for tests.

        Raises:
            ValueError: If ``requests_per_second`` exceeds the SEC ceiling.
        """
        if requests_per_second > MAX_REQUESTS_PER_SECOND:
            raise ValueError(
                f"requests_per_second must not exceed {MAX_REQUESTS_PER_SECOND}; "
                "the SEC asks for 10/second and blocks IPs that ignore it"
            )

        self.user_agent = user_agent or os.environ.get(
            "EDGAR_MCP_USER_AGENT", DEFAULT_USER_AGENT
        )
        if cache is not None:
            self.cache = cache
        else:
            env_no_cache = os.environ.get("EDGAR_MCP_NO_CACHE", "0") == "1"
            ttl = (
                cache_ttl_seconds
                if cache_ttl_seconds is not None
                else float(os.environ.get("EDGAR_MCP_CACHE_TTL_SECONDS", "0") or 0)
            )
            self.cache = ResponseCache(
                cache_dir or os.environ.get("EDGAR_MCP_CACHE_DIR", ".cache"),
                ttl_seconds=ttl,
                enabled=use_cache and not env_no_cache,
            )

        self.bucket = TokenBucket(requests_per_second, burst)
        self._timeout = timeout
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._transport = transport
        self._sleep = sleep_fn or asyncio.sleep
        self._client: httpx.AsyncClient | None = None
        self.request_count = 0
        self.cache_hits = 0

    # -- plumbing ---------------------------------------------------------- #

    def _headers(self) -> dict[str, str]:
        """Return the headers sent on every SEC request.

        This is the only place the User-Agent is set. If a request 403s, this
        method is the first and usually the last place to look.

        Returns:
            The header dict.
        """
        return {
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
        }

    async def _http(self) -> httpx.AsyncClient:
        """Return the lazily created httpx client.

        Returns:
            A live ``httpx.AsyncClient``.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                headers=self._headers(),
                transport=self._transport,
                follow_redirects=True,
            )
        return self._client

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> SECClient:
        """Enter the async context manager.

        Returns:
            This client.
        """
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        """Close the client on context exit.

        Args:
            *exc_info: Standard exception triple, unused.
        """
        await self.aclose()

    # -- fetching ---------------------------------------------------------- #

    async def _fetch(self, url: str, *, as_json: bool) -> Any:
        """Fetch a URL through the cache, the rate limiter and the retry loop.

        Args:
            url: Absolute URL to fetch.
            as_json: Parse the body as JSON when True, return text when False.

        Returns:
            The parsed JSON body or the response text.

        Raises:
            NotFoundError: On a 404.
            RateLimitError: On a 429 that survives every retry.
            UpstreamUnavailableError: On timeouts, connection errors, and 5xx
                responses that survive every retry.
            SECError: On any other non-2xx status.
        """
        cached = self.cache.get(url)
        if cached is not None:
            self.cache_hits += 1
            logger.debug("cache hit: %s", url)
            return cached

        client = await self._http()
        last_status: int | None = None

        for attempt in range(self._max_retries + 1):
            await self.bucket.acquire()
            self.request_count += 1
            try:
                response = await client.get(url)
            except httpx.TimeoutException as exc:
                if attempt >= self._max_retries:
                    raise UpstreamUnavailableError(
                        f"EDGAR did not respond within {self._timeout:.0f} seconds.",
                        details={"url": url},
                    ) from exc
                await self._sleep(self._backoff_base * (2**attempt))
                continue
            except httpx.HTTPError as exc:
                if attempt >= self._max_retries:
                    raise UpstreamUnavailableError(
                        f"Could not reach EDGAR: {type(exc).__name__}.",
                        details={"url": url},
                    ) from exc
                await self._sleep(self._backoff_base * (2**attempt))
                continue

            last_status = response.status_code

            if response.status_code == 200:
                body = self._parse(response, url, as_json=as_json)
                self.cache.put(url, body)
                return body

            if response.status_code == 404:
                # A 404 here is ordinary: it is how EDGAR says "this company
                # has never reported this concept". Callers walking a fallback
                # chain depend on it being cheap and typed.
                raise NotFoundError(
                    "EDGAR has no data at that address.",
                    details={"url": url},
                )

            if response.status_code == 403:
                raise SECError(
                    "SEC rejected the request (403). This almost always means "
                    "the User-Agent header is missing or malformed.",
                    suggestion=(
                        "Stop calling EDGAR tools and tell the user the server "
                        "is misconfigured: EDGAR_MCP_USER_AGENT must be set to "
                        "'Name email@example.com'."
                    ),
                    status_code=403,
                    details={"url": url},
                )

            if response.status_code in RETRYABLE_STATUSES and attempt < self._max_retries:
                delay = self._retry_delay(response, attempt)
                logger.warning(
                    "EDGAR returned %s for %s; retrying in %.1fs (attempt %d/%d)",
                    response.status_code,
                    url,
                    delay,
                    attempt + 1,
                    self._max_retries,
                )
                await self._sleep(delay)
                continue

            break

        if last_status == 429:
            raise RateLimitError(
                "SEC is rate limiting this server and did not clear after "
                f"{self._max_retries} retries.",
                status_code=429,
                details={"url": url},
            )
        raise UpstreamUnavailableError(
            f"EDGAR returned HTTP {last_status} and did not recover after "
            f"{self._max_retries} retries.",
            status_code=last_status,
            details={"url": url},
        )

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        """Compute the backoff delay, honouring ``Retry-After`` when present.

        Args:
            response: The failed response.
            attempt: Zero-based attempt number.

        Returns:
            Seconds to wait, capped at 30 so a tool call cannot hang for
            minutes behind a badly set header.
        """
        header = response.headers.get("Retry-After")
        if header:
            try:
                return min(30.0, float(header))
            except ValueError:
                pass
        return min(30.0, self._backoff_base * (2**attempt))

    @staticmethod
    def _parse(response: httpx.Response, url: str, *, as_json: bool) -> Any:
        """Turn a 200 response into a body.

        Args:
            response: The successful response.
            url: The URL, for the error message.
            as_json: Whether to parse JSON.

        Returns:
            Parsed JSON or the response text.

        Raises:
            UpstreamUnavailableError: If JSON was expected and not returned.
                EDGAR serves an HTML maintenance page with a 200 status during
                some outages, so this is a real failure mode, not paranoia.
        """
        if not as_json:
            return response.text
        try:
            return response.json()
        except ValueError as exc:
            raise UpstreamUnavailableError(
                "EDGAR returned a success status but the body was not JSON. "
                "This usually means EDGAR served a maintenance page.",
                details={"url": url},
            ) from exc

    async def get_json(self, url: str) -> Any:
        """Fetch a URL and return parsed JSON.

        Args:
            url: Absolute URL.

        Returns:
            The parsed JSON body.
        """
        return await self._fetch(url, as_json=True)

    async def get_text(self, url: str) -> str:
        """Fetch a URL and return the response body as text.

        Args:
            url: Absolute URL.

        Returns:
            The response text.
        """
        return await self._fetch(url, as_json=False)

    # -- endpoint helpers -------------------------------------------------- #

    async def company_tickers(self) -> Any:
        """Fetch the ticker-to-CIK map.

        Returns:
            The raw ``company_tickers.json`` payload.
        """
        return await self.get_json(COMPANY_TICKERS_URL)

    async def submissions(self, padded_cik: str) -> Any:
        """Fetch a company's filing history.

        Args:
            padded_cik: A 10-digit zero-padded CIK.

        Returns:
            The raw submissions payload.
        """
        return await self.get_json(SUBMISSIONS_URL.format(cik=padded_cik))

    async def company_concept(self, padded_cik: str, taxonomy: str, tag: str) -> Any:
        """Fetch one XBRL concept's full history for a company.

        Args:
            padded_cik: A 10-digit zero-padded CIK.
            taxonomy: ``us-gaap``, ``dei``, ``ifrs-full`` and so on.
            tag: The XBRL element name.

        Returns:
            The raw companyconcept payload.
        """
        return await self.get_json(
            COMPANY_CONCEPT_URL.format(cik=padded_cik, taxonomy=taxonomy, tag=tag)
        )

    async def company_facts(self, padded_cik: str) -> Any:
        """Fetch every reported fact for a company.

        Args:
            padded_cik: A 10-digit zero-padded CIK.

        Returns:
            The raw companyfacts payload.
        """
        return await self.get_json(COMPANY_FACTS_URL.format(cik=padded_cik))


# --------------------------------------------------------------------------- #
# Process-wide client
# --------------------------------------------------------------------------- #

_client: SECClient | None = None


def get_client() -> SECClient:
    """Return the process-wide client, creating it on first use.

    The token bucket only limits what it can see, so the server shares one
    client across all six tools.

    Returns:
        The shared :class:`SECClient`.
    """
    global _client
    if _client is None:
        _client = SECClient()
    return _client


def set_client(client: SECClient | None) -> None:
    """Replace the process-wide client.

    Called by ``server.main`` after parsing ``--no-cache``, and by tests.

    Args:
        client: The client to install, or None to reset.
    """
    global _client
    _client = client
