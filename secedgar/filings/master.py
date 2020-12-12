import os
from datetime import datetime, date, timedelta
from calendar import monthrange

from secedgar.utils import get_quarter
from secedgar.filings._index import IndexFilings


class MasterFilings(IndexFilings):
    """Class for retrieving all filings from specific year and quarter.

    Attributes:
        year (int): Must be in between 1993 and the current year (inclusive).
        quarter (int): Must be 1, 2, 3, or 4. Quarter of filings to fetch.
        client (secedgar.client._base, optional): Client to use. Defaults to
            ``secedgar.client.NetworkClient`` if None given.
        entry_filter (function, optional): A boolean function to determine
            if the FilingEntry should be kept. Defaults to ``lambda _: True``.
        kwargs: Keyword arguments to pass to ``secedgar.filings._index.IndexFilings``.
    """

    def __init__(self,
                 year,
                 quarter,
                 client=None,
                 entry_filter=lambda _: True,
                 **kwargs):
        super().__init__(client=client, entry_filter=entry_filter, **kwargs)
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

    def get_file_names(self):
        """The list of .tar.gz daily files in the current quarter."""
        if self.year < 1995 or (self.year == 1995 and self.quarter < 3):
            raise ValueError('Bulk downloading is only available starting 1995 Q3.')
        # https://stackoverflow.com/questions/36793381/python-get-first-and-last-day-of-current-calendar-quarter
        first_month_of_quarter = 3 * self.quarter - 2
        last_month_of_quarter = 3 * self.quarter
        start_date = date(self.year, first_month_of_quarter, 1)
        end_date = date(self.year, last_month_of_quarter,
                        monthrange(self.year, last_month_of_quarter)[1])
        if self.year == 1995 and self.quarter == 3:
            days = [15, 18, 19, 21, 22, 25, 28]
            dates_between = [date(1995, 9, day) for day in days]
        else:
            dates_between = [start_date + timedelta(days=x)
                             for x in range((end_date-start_date).days + 1)]
        daily_file_format = '{date}.nc.tar.gz'
        all_days_in_quarter = [daily_file_format.format(
            date=d.strftime("%Y%m%d")) for d in dates_between]
        return all_days_in_quarter

    def save(self, directory, dir_pattern=None, file_pattern=None, download_all=False):
        """Save all daily filings.

        Creates subdirectory within given directory of the form <YEAR>/QTR<QTR NUMBER>/.
        Then each distinct company name receives its own directory with all of its filings.
        See ``secedgar.filings._index.IndexFilings`` for more detail.

        Args:
            directory (str): Directory where filings should be stored. Will be broken down
                further by company name and form type.
            dir_pattern (str): Format string for subdirectories. Default is
                `{year}/QTR{quarter}/{cik}`. Valid options are `year`, `quarter`, and `cik`.
            file_pattern (str): Format string for files. Default is `{accession_number}`.
                Valid options are `accession_number`.
            download_all (bool): Type of downloading system, if true downloads all data for each
                day, if false downloads each file in index. Default is `False`.
        """
        if dir_pattern is None:
            # https://stackoverflow.com/questions/11283961/partial-string-formatting
            dir_pattern = os.path.join('{year}', 'QTR{quarter}', '{cik}')

        formatted_dir = dir_pattern.format(year=self.year, quarter=self.quarter, cik="{cik}")
        self.save_filings(directory, dir_pattern=formatted_dir,
                          file_pattern=file_pattern, download_all=download_all)
