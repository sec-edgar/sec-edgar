from bs4 import BeautifulSoup
import abc
import sys
from SECEdgar.network_client import NetworkClient

if sys.version_info >= (3, 4):
    ABC = abc.ABC
else:
    ABC = abc.ABCMeta(str('ABC'), (), {})


class _EDGARBase(ABC):
    """Abstract Base Class for EDGAR requests.

    Attributes:
        client (SECEdgar.network_client.NetworkClient) : NetworkClient object that handles getting data from EDGAR.
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
        return BeautifulSoup(self.get_response().text, features="html.parser")

    def get_response(self):
        return self._client.get_response(self.url, self.params)
