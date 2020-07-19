import datetime
import os
import re
import requests

from collections import namedtuple

from secedgar.client import NetworkClient
from secedgar.filings._index import IndexFilings
from secedgar.utils import make_path, get_quarter

from secedgar.utils.exceptions import EDGARQueryError


class DailyFilings(IndexFilings):
    """Class for retrieving all daily filings from https://www.sec.gov/Archives/edgar/daily-index.

    Attributes:
        date (datetime.datetime): Date of daily filing to fetch.
        client (secedgar.client._base.AbstractClient): Client to use for fetching data.
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

    @property
    def path(self):
        """str: Path added to client base.

        .. note::
            The trailing slash at the end of the path is important.
            Omitting will raise EDGARQueryError.
        """
        return "Archives/edgar/daily-index/{year}/QTR{num}/".format(
            year=self.year, num=self.quarter)

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

    # TODO: Take this code and put it into IndexFilings as separate function `save_filings`
    # Then call self.save_filings(os.path.join(self._date, directory)) for daily and
    # self.save_filings(os.path.join(self.year, self.quarter, directory)) for master
    def save(self, directory):
        """Save all daily filings.

        Will store all filings for each unique company name under a separate subdirectory
        within given directory argument.

        Ex:
        my_directory
        |
        ---- Apple Inc.
             |
             ---- ...txt files
        ---- Microsoft Corp.
             |
             ---- ...txt files

        Args:
            directory (str): Directory where filings should be stored. Will be broken down
                further by company name and form type.
        """
        self.get_filings_dict()
        for filings in self._filings_dict.values():
            # take the company name from the first filing and make that the subdirectory name
            subdirectory = os.path.join(directory, filings[0].company_name)
            make_path(subdirectory)
            for filing in filings:
                filename = filing.file_name.split('/')[-1]
                filing_path = os.path.join(subdirectory, filename)
                url = self.make_url(filename)
                data = requests.get(url).text
                with open(filing_path, 'w') as f:
                    f.write(data)
