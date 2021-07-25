import os
from datetime import date

from secedgar.core._index import IndexFilings
from secedgar.utils import get_quarter


class QuarterlyFilings(IndexFilings):
    """Class for retrieving all filings from specific year and quarter.

    Args:
        year (int): Must be in between 1993 and the current year (inclusive).
        quarter (int): Must be 1, 2, 3, or 4. Quarter of filings to fetch.
        user_agent (Union[str, NoneType], optional): Value used for HTTP header
            "User-Agent" for all requests. If given None, a valid client with
            user_agent must be given. See the SEC's statement on
            `fair access <https://www.sec.gov/os/accessing-edgar-data>`_
            for more information. Defaults to None.
        client (Union[NoneType, secedgar.client.NetworkClient], optional): Client to use for
            fetching data. If None is given, a user_agent must be given to pass to
            :class:`secedgar.client.NetworkClient`. Defaults to ``secedgar.client.NetworkClient``
            if none is given.
        entry_filter (function, optional): A boolean function to determine
            if the FilingEntry should be kept. Defaults to ``lambda _: True``.
            See :class:`secedgar.core.DailyFilings` for more detail.
        kwargs: Keyword arguments to pass to ``secedgar.core._index.IndexFilings``.

    Examples:
        .. code-block:: python

            import secedgar as sec
            quarterly = sec.QuarterlyFilings(year=2021,
                                             quarter=2,
                                             user_agent="Name (email)")
            quarterly.save("/path/to/dir")

    """

    def __init__(self,
                 year,
                 quarter,
                 user_agent=None,
                 client=None,
                 entry_filter=lambda _: True,
                 **kwargs):
        super().__init__(user_agent=user_agent,
                         client=client,
                         entry_filter=entry_filter,
                         **kwargs)
        self.year = year
        self.quarter = quarter

    @property
    def path(self):
        """Path property to pass to client."""
        return "Archives/edgar/full-index/{year}/QTR{num}/".format(
            year=self._year, num=self._quarter)

    @property
    def year(self):
        """Year of filings."""
        return self._year

    @year.setter
    def year(self, val):
        if not isinstance(val, int):
            raise TypeError("Year must be an integer.")
        elif val < 1993 or val > date.today().year:
            raise ValueError(
                "Year must be in between 1993 and {now} (inclusive)".format(
                    now=date.today().year))
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
        elif self.year == date.today().year and val > get_quarter(date.today()):
            raise ValueError("Latest quarter for current year is {qtr}".format(
                qtr=get_quarter(date.today())))
        self._quarter = val

    @property
    def idx_filename(self):
        """Main index filename to look for."""
        return "master.idx"

    def _get_tar_urls(self):
        """The list of .tar.gz daily files in the current quarter."""
        soup = self.client.get_soup(self.tar_path, {})
        files = [a.get('href') for a in soup.find_all('a') if "nc.tar.gz" in a.get('href')]
        return files

    def save(self,
             directory,
             dir_pattern=None,
             file_pattern="{accession_number}",
             download_all=False):
        """Save all daily filings.

        Creates subdirectory within given directory of the form <YEAR>/QTR<QTR NUMBER>/.
        Then each distinct company name receives its own directory with all of its filings.
        See ``secedgar.core._index.IndexFilings`` for more detail.

        Args:
            directory (str): Directory where filings should be stored. Will be broken down
                further by company name and form type.
            dir_pattern (str): Format string for subdirectories. Default is
                `{year}/QTR{quarter}/{cik}`. Valid options to mix and match
                 are `{year}`, `{quarter}`, and `{cik}`.
            file_pattern (str): Format string for files. Default is `{accession_number}`.
                Valid options are `{accession_number}`.
            download_all (bool): Type of downloading system, if true downloads all data for each
                day, if false downloads each file in index. Default is `False`.
        """
        if dir_pattern is None:
            # https://stackoverflow.com/questions/11283961/partial-string-formatting
            dir_pattern = os.path.join('{year}', 'QTR{quarter}', '{cik}')

        # If "{cik}" is in dir_pattern, it will be passed on and if not it will be ignored
        formatted_dir = dir_pattern.format(year=self.year,
                                           quarter=self.quarter,
                                           cik="{cik}")
        self._save_filings(directory,
                           dir_pattern=formatted_dir,
                           file_pattern=file_pattern,
                           download_all=download_all)
