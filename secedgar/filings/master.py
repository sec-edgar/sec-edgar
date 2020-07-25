import os
from datetime import datetime

from secedgar.utils import get_quarter

from secedgar.filings._index import IndexFilings


class MasterFilings(IndexFilings):
    """Class for retrieving all filings from specific year and quarter.

    Attributes:
        year (int): Must be in between 1993 and the current year (inclusive).
        quarter (int): Must be 1, 2, 3, or 4. Quarter of filings to fetch.
        client (secedgar.client._base, optional): Client to use. Defaults to
            ``secedgar.client.NetworkClient`` if None given.
        kwargs: Keyword arguments to pass to ``secedgar.filings._index.IndexFilings``.
    """

    def __init__(self,
                 year,
                 quarter,
                 client=None,
                 **kwargs):
        super().__init__(client=client, **kwargs)
        self.year = year
        self.quarter = quarter

    @property
    def path(self):
        """Path property to pass to client."""
        return "Archives/edgar/full-index/{year}/QTR{num}/".format(year=self._year,
                                                                   num=self._quarter)

    @property
    def year(self):
        """Year of filings."""
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
        """Quarter of filings."""
        return self._quarter

    @quarter.setter
    def quarter(self, val):
        if not isinstance(val, int):
            raise TypeError("Quarter must be integer.")
        elif val not in range(1, 5):
            raise ValueError("Quarter must be in between 1 and 4 (inclusive).")
        elif self.year == datetime.today().year and val > get_quarter(datetime.today()):
            raise ValueError("Latest quarter for current year is {qtr}".format(
                qtr=get_quarter(datetime.today())))
        self._quarter = val

    # TODO: Implement zip decompression to idx file to decrease response load
    @property
    def idx_filename(self):
        """Main index filename to look for."""
        return "master.idx"

    def save(self, directory):
        """Save all daily filings.

        Creates subdirectory within given directory of the form <YEAR>/QTR<QTR NUMBER>/.
        Then each distinct company name receives its own directory with all of its filings.
        See ``secedgar.filings._index.IndexFilings`` for more detail.

        Args:
            directory (str): Directory where filings should be stored. Will be broken down
                further by company name and form type.
        """
        directory = os.path.join(directory, str(self.year), "QTR" + str(self.quarter))
        self.save_filings(directory)
