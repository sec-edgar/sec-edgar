import datetime

from secedgar.filings._base import AbstractFiling
from secedgar.client import NetworkClient


class DailyFilings(AbstractFiling):
    """Class for retrieving all daily filings from https://www.sec.gov/Archives/edgar/daily-index."""

    def __init__(self, date, client=None):
        super().__init__()
        if not isinstance(date, datetime.datetime):
            raise TypeError(
                "Date must be given as datetime object. Was given type {t}.".format(type(date)))
        self._date = date
        self._client = client if client is not None else NetworkClient()

    @property
    def client(self):
        return self._client

    def _get_quarter(self):
        """Get quarter number from date given."""
        return (self._date.month - 1) // 3 + 1

    @property
    def path(self):
        return "Archives/edgar/daily-index/{year}/QTR{num}".format(year=self._date.year, num=self._get_quarter())

    @property
    def params(self):
        """Params should be empty."""
        return {}

    def get_urls(self, **kwargs):
        pass
