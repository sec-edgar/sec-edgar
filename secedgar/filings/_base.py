from abc import ABC, abstractmethod


class AbstractFiling(ABC):
    """Abstract base class for all SEC EDGAR filings.

    .. versionadded:: 0.1.5
    """

    @property
    @abstractmethod
    def client(self):
        """``secedgar.client._base``: Client to use to make requests."""
        pass  # pragma: no cover

    @abstractmethod
    def get_urls(self, **kwargs):
        """Get all URLs for filings.

        Args:
            kwargs: Anything to be passed to requests when making GET request.

        Returns:
            urls (list): List of urls for txt files to download.
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def params(self):
        """:obj:`dict`: Parameters to include in requests."""
        pass  # pragma: no cover

    @property
    @abstractmethod
    def path(self):
        """str: Path added to client base."""
        pass  # pragma: no cover

    @abstractmethod
    def save(self, directory):
        """Save filings in directory.

        Args:
            directory (str): Path to directory where files should be saved.

        Returns:
            None
        """
        pass  # pragma: no cover
