from abc import ABC, abstractmethod


class _EDGARBase(ABC):
    """Abstract Base Class for EDGAR requests.

    Attributes:
        client (SECEdgar.network_client.NetworkClient) : NetworkClient object that handles
            getting data from EDGAR.
        url (str): URL endpoint.
        params (dict): Dictionary of parameters to add.

    .. versionadded:: 0.1.5
    """

    @property
    @abstractmethod
    def path(self):
        pass

    @property
    @abstractmethod
    def params(self):
        pass

    @property
    @abstractmethod
    def client(self):
        pass
