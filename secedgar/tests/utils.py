import os

import requests


def datapath(*args):
    """Get the path to a data file.

    Returns:
        path including ``secedgar/tests/data``.
    """
    base_path = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(base_path, *args)


class MockResponse(requests.Response):
    def __init__(self, datapath_args=[],
                 status_code=200,
                 content=None,
                 *args,
                 **kwargs):
        super().__init__()
        self.status_code = status_code
        if content is not None:
            self._content = content
        else:
            with open(datapath(*datapath_args), "rb", **kwargs) as f:
                self._content = f.read()
        self._content_consumed = True

    def __call__(self, *args, **kwargs):
        return self


class AsyncMockResponse(MockResponse):
    def __init__(self, datapath_args=[],
                 status_code=200,
                 content=None,
                 encoding="utf-8",
                 *args,
                 **kwargs):
        super().__init__(datapath_args=datapath_args,
                         status_code=status_code,
                         content=content,
                         *args,
                         **kwargs)
        self._encoding = encoding

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self

    async def read(self):
        return self._content


class AsyncLimitedResponsesSession:
    def __init__(self, response=AsyncMockResponse(content=bytes("Testing...", "utf-8")), limit=10):
        self._response = response
        self._limit = limit
        self._requests_made = 0

    async def get(self, *args, **kwargs):
        if self._requests_made < self._limit:
            return await self._response
        return

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass
