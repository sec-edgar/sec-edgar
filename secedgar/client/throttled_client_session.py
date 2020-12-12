import time
import asyncio
from aiohttp import ClientSession, TCPConnector


class ThrottledClientSession(ClientSession):
    """Rate-throttled client session class inherited from aiohttp.ClientSession.

    Attributes:
        rate_limit (int): Number of requests to limit session to per second.
    """

    def __init__(self, rate_limit: int, *args, **kwargs):
        kwargs['connector'] = TCPConnector(limit=rate_limit) # Another safeguard against rate limit
        super().__init__(*args, **kwargs)
        if rate_limit <= 0:
            raise ValueError('rate_limit must be positive')
        self.rate_limit = rate_limit
        self._start_time = time.time()
        self._queue = asyncio.Queue(min(2, rate_limit))
        self._fillerTask = asyncio.create_task(self._filler())
    def _get_sleep(self):
        return 1 / self.rate_limit

    async def close(self):
        """Close rate-limiter's "bucket filler" task."""
        if self._fillerTask is not None:
            self._fillerTask.cancel()
        try:
            await asyncio.wait_for(self._fillerTask, timeout=0.5)
        except asyncio.TimeoutError as err:
            raise err
        await super().close()

    async def _filler(self):
        """Filler task to fill the leaky bucket algo."""
        try:
            if self._queue is None:
                return
            sleep = self._get_sleep()
            updated_at = time.monotonic()
            fraction = 0
            extra_increment = 0
            for i in range(self._queue.maxsize):
                self._queue.put_nowait(i)
            while True:
                if not self._queue.full():
                    now = time.monotonic()
                    increment = self.rate_limit * (now - updated_at)
                    fraction += increment % 1
                    extra_increment = fraction // 1
                    items_to_add = int(min(self._queue.maxsize - self._queue.qsize(),
                                           int(increment) + extra_increment))
                    fraction = fraction % 1
                    for i in range(items_to_add):
                        self._queue.put_nowait(i)
                    updated_at = now
                await asyncio.sleep(sleep)
        except asyncio.CancelledError:
            pass  # Was canceled b/c of close
        except Exception as err:
            raise err

    async def _allow(self):
        if self._queue is not None:
            await self._queue.get()
            self._queue.task_done()
        return None

    async def _request(self, *args, **kwargs):
        """Throttled request."""
        await self._allow()
        return await super()._request(*args, **kwargs)
