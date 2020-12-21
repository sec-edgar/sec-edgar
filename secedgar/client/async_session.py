import asyncio
import time


class RateLimitedClientSession:
    """Rate Limited Client.

    Attributes:
        client (aiohttp.ClientSession): A client to call
        rate_limit (int): Maximum number of requests per second to make

    https://quentin.pradet.me/blog/how-do-you-rate-limit-calls-with-aiohttp.html
    This class is not thread-safe.
    """

    def __init__(self, client, rate_limit):
        self._client = client
        self._rate_limit = rate_limit
        self._max_tokens = rate_limit
        self._tokens = self._max_tokens
        self._updated_at = time.monotonic()
        self._start = time.monotonic()

    async def get(self, *args, **kwargs):
        """Wrapper for ``client.get`` that first waits for a token."""
        await self.wait_for_token()
        return self._client.get(*args, **kwargs)

    async def wait_for_token(self):
        """Sleeps until a new token is added."""
        while self._tokens < 1:
            self.add_new_tokens()
            await asyncio.sleep(0.03)
        self._tokens -= 1

    def add_new_tokens(self):
        """Adds a new token if time elapsed is greater than minimum time."""
        now = time.monotonic()
        time_since_update = now - self._updated_at
        new_tokens = time_since_update * self._rate_limit
        if self._tokens + new_tokens >= 1:
            self._tokens = min(self._tokens + new_tokens, self._max_tokens)
            self._updated_at = now
