import abc
import errno
import os
import sys

from bs4 import BeautifulSoup

from SECEdgar.network_client import NetworkClient

if sys.version_info >= (3, 4):
    ABC = abc.ABC
else:
    ABC = abc.ABCMeta(str('ABC'), (), {})


class _EDGARBase(ABC):
    """Abstract Base Class for EDGAR requests.

    Attributes:
        client (SECEdgar.network_client.NetworkClient) : NetworkClient object that handles
            getting data from EDGAR.
        url (str): URL endpoint.
        params (dict): Dictionary of parameters to add.

    .. versionadded:: 0.1.5
    """

    def __init__(self, **kwargs):
        self._client = NetworkClient(**kwargs)
        self._params = {'count': self._client.count}

    @property
    def url(self):
        raise NotImplementedError

    @property
    def params(self):
        return self._params

    @property
    def client(self):
        return self._client

    def get_soup(self):
        return BeautifulSoup(self.get_response().text, features='lxml')

    def get_response(self, **kwargs):
        return self._client.get_response(self.url, self.params, **kwargs)

    @staticmethod
    def _make_path(path, **kwargs):
        """Make directory based on filing info.

        Args:
            path (str): Path to be made if it doesn't exist.

        Raises:
            OSError: If there is a problem making the path.

        Returns:
            None
        """

        if not os.path.exists(path):
            try:
                os.makedirs(path, **kwargs)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise OSError
