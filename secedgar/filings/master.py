from datetime import datetime

from secedgar.utils import get_quarter

from secedgar.filings._index import IndexFilings
from secedgar.client.network_client import NetworkClient


class MasterFilings(IndexFilings):
    def __init__(self,
                 year,
                 quarter,
                 client=None):
        super().__init__(client=client)
        self._year = year
        self._quarter = quarter

    @property
    def path(self):
        return "Archives/edgar/full-index/{year}/QTR{num}/".format(year=self._year, num=self._quarter)

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
                qtr=get_quarter(datetime.now())))
        self._quarter = val

    # TODO: Implement zip decompression to idx file to decrease response load
    @property
    def idx_filename(self):
        """Main index filename to look for."""
        return "master.idx"

    def save(self, directory):
        pass
