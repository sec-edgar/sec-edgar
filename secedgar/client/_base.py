from abc import ABC, abstractmethod


class AbstractClient(ABC):

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
        pass

    @abstractmethod
    def get_soup(self, path, params, **kwargs):
        """ Return BeautifulSoup object from response text. Uses lxml parser.

        Args:
            path (str): A properly-formatted path
            params (dict): Dictionary of parameters to pass
            to request.

        Returns:
            BeautifulSoup object from response text.
        """
        pass

    @property
    @abstractmethod
    def count(self):
        """Number of results per page searched. Increasing can improve speed for large requests."""
        pass
