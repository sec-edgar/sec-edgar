from abc import ABC, abstractmethod


class AbstractClient(ABC):
    """Abstract base class for client to retrieve data from EDGAR."""

    @abstractmethod
    def get_response(self, path, params, **kwargs):
        """Executes HTTP request and returns response if valid.

        Args:
            path (str): A properly-formatted path
            params (dict): Dictionary of parameters to pass
            to request.

        Returns:
            response (requests.response): A requests.response object.

        Raises:
            EDGARQueryError: If problems arise when making query.
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_soup(self, path, params, **kwargs):
        """Return BeautifulSoup object from response text. Uses lxml parser.

        Args:
            path (str): A properly-formatted path
            params (dict): Dictionary of parameters to pass
            to request.

        Returns:
            BeautifulSoup object from response text.
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def batch_size(self):
        """Number of results per page searched. Increasing can improve speed for large requests."""
        pass  # pragma: no cover

    @staticmethod
    @abstractmethod
    def _prepare_query(path):
        """Prepare the query url.

        Args:
            url (str): End of url.

        Returns:
            url (str): A formatted url.
        """
        pass  # pragma: no cover

    @abstractmethod
    async def wait_for_download_async(self, inputs):
        """Asynchronously download links into files using rate limit."""
        pass  # pragma: no cover
