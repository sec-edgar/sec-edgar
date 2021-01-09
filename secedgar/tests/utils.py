import os


def datapath(*args):
    """Get the path to a data file.

    Returns:
        path including ``secedgar/tests/data``.
    """
    base_path = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(base_path, *args)


class MockResponse:
    def __init__(self, datapath_args=[],
                 status_code=200,
                 file_read_args='r',
                 text=None,
                 *args,
                 **kwargs):
        self.status_code = status_code
        if text is not None:
            self.text = text
        else:
            with open(datapath(*datapath_args), file_read_args, **kwargs) as f:
                self.text = f.read()

    def __call__(self, *args, **kwargs):
        return self


class AsyncMockResponse(MockResponse):
    def __init__(self, datapath_args=[], status_code=200, file_read_args="r", text=None,
                 encoding="utf-16", *args, **kwargs):
        super().__init__(datapath_args=datapath_args, status_code=status_code,
                         file_read_args=file_read_args, text=text, *args, **kwargs)
        self._encoding = encoding

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self

    async def read(self):
        return bytes(self.text, encoding=self._encoding)


class AsyncLimitedResponsesSession:
    def __init__(self, response=AsyncMockResponse(text="Testing..."), limit=10):
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
