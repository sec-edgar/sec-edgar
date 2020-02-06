from abc import ABC, abstractmethod


class Client(ABC):

    @abstractmethod
    def get_response(self, path, params, **kwargs):
        pass

    @abstractmethod
    def get_soup(self, path, params, **kwargs):
        pass

    @property
    @abstractmethod
    def count(self):
        pass
