from datetime import datetime

from secedgar.utils import get_quarter

from secedgar.filings._base import AbstractFiling
from secedgar.client.network_client import NetworkClient


class MasterFilings(AbstractFiling):
    def __init__(self,
                 year,
                 quarter,
                 client=None):
        self._year = year
        self._quarter = quarter
        self._client = client if client is not None else NetworkClient()

    @property
    def client(self):
        return self._client

    @property
    def params(self):
        pass

    @property
    def path(self):
        "Archives/edgar/full-index/{year}/QTR{num}/".format(year=self._year, num=self._quarter)

    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, val):
        if not isinstance(val, int):
            raise TypeError("Year must be an integer.")
        elif val < 1993 or val > datetime.today().year:
            raise ValueError("Year must be in between 1993 and {now} (inclusive)".format(
                now=datetime.today().year))
        self._year = val

    @property
    def quarter(self):
        return self._quarter

    @quarter.setter
    def quarter(self, val):
        if not isinstance(val, int):
            raise TypeError("Quarter must be integer.")
        elif val not in range(1, 5):
            raise ValueError("Quarter must be in between 1 and 4 (inclusive).")
        elif self.year == datetime.now().year and val > get_quarter(datetime.now()):
            raise ValueError("Latest quarter for current year is {qtr}".format(
                get_quarter(datetime.now())))
        self._quarter = val

    def get_urls(self, **kwargs):
        pass

    def save(self, directory):
        pass
