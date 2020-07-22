import datetime
import os

from secedgar.filings._index import IndexFilings
from secedgar.utils import get_quarter


class DailyFilings(IndexFilings):
    """Class for retrieving all daily filings from https://www.sec.gov/Archives/edgar/daily-index.

    Attributes:
        date (datetime.datetime): Date of daily filing to fetch.
        client (secedgar.client._base.AbstractClient, optional): Client to use for fetching data.
            Defaults to ``secedgar.client.NetworkClient`` if none is given.
    """

    def __init__(self, date, client=None):
        super().__init__(client=client)
        if not isinstance(date, datetime.datetime):
            raise TypeError(
                "Date must be given as datetime object. Was given type {type}.".format(
                    type=type(date)))
        self._date = date

    @property
    def path(self):
        """str: Path added to client base.

        .. note::
            The trailing slash at the end of the path is important.
            Omitting will raise EDGARQueryError.
        """
        return "Archives/edgar/daily-index/{year}/QTR{num}/".format(
            year=self.year, num=self.quarter)

    @property
    def quarter(self):
        """Get quarter number from date attribute."""
        return get_quarter(self._date)

    @property
    def year(self):
        """Year of date for daily filing."""
        return self._date.year

    @property
    def idx_filename(self):
        """Main index filename to look for."""
        return "master.{date}.idx".format(date=self._get_idx_formatted_date())

    def _get_idx_formatted_date(self):
        """Format date for idx file.

        EDGAR changed its master.idx file format twice. In 1995 QTR 1 and in 1998 QTR 2.
        The format went from MMDDYY to YYMMDD to YYYYMMDD.

        Returns:
            date (str): Correctly formatted date for master.idx file.
        """
        if self._date.year < 1995:
            return self._date.strftime("%m%d%y")
        elif self._date < datetime.datetime(1998, 3, 31):
            return self._date.strftime("%y%m%d")
        else:
            return self._date.strftime("%Y%m%d")

    def save(self, directory):
        """Save all daily filings.

        Store all filings for each unique company name under a separate subdirectory
        within given directory argument. Creates directory with date in YYYYMMDD format
        within given directory.

        Args:
            directory (str): Directory where filings should be stored. Will be broken down
                further by company name and form type.
        """
        directory = os.path.join(directory, self._date.strftime("%Y%m%d"))
        self.save_filings(directory)
