import datetime
import os

from secedgar.filings._index import IndexFilings

class DailyFilings(IndexFilings):
    """Class for retrieving all daily filings from https://www.sec.gov/Archives/edgar/daily-index.

    Attributes:
        date (datetime.date): Date of daily filing to fetch.
        client (secedgar.client._base.AbstractClient, optional): Client to use for fetching data.
            Defaults to ``secedgar.client.NetworkClient`` if none is given.
        entry_filter (function, optional): A boolean function to determine
            if the FilingEntry should be kept. Defaults to `lambda _: True`.
            The ``FilingEntry`` object exposes 6 variables which can be
            used to filter which filings to keep. These are "cik", "company_name",
            "form_type", "date_filed", "file_name", and "path".

    Using ``entry_filter``
    ----------------------

    To only download filings from a company named "Company A", the following
    function would suffice for only getting those filings:

    .. code-block:: python

        def get_company_a_filings(filing_entry):
            return filing_entry.company_name == "Company A"

    To only download Company A or Company B's 10-K fillings from
    a specific day, a well-defined ``entry_filter`` would be:

    .. code-block:: python

        def get_company_ab_10k(filing_entry):
            return filing_entry.company_name in ("Company A", "Company B") and
                   filing_entry.form_type.lower() == "10-k"

    To use the second function as an ``entry_filter``, the following code could be used:

    .. code-block:: python

        from datetime import date
        from secedgar.filings import DailyFilings

        d = DailyFilings(date=date(2020, 12, 10), entry_filter=get_company_ab_10k)

    """

    def __init__(self, date, **kwargs):
        super().__init__(**kwargs)
        if not isinstance(date, datetime.date):
            raise TypeError(
                "Date must be given as datetime.date object. Was given type {type}.".format(
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
        return self.get_quarter(self._date)

    @property
    def year(self):
        """Year of date for daily filing."""
        return self._date.year

    @property
    def idx_filename(self):
        """Main index filename to look for."""
        return "master.{date}.idx".format(date=self._get_idx_formatted_date())

    def _get_tar(self):
        """The .tar.gz filename for the current day."""
        if self.year < 1995 or (self.year == 1995 and self.quarter < 3):
            raise ValueError('Bulk downloading is only available starting 1995 Q3.')
        daily_file = '{date}.nc.tar.gz'.format(date=self._date.strftime("%Y%m%d"))
        return [daily_file]
    def _get_listings_directory(self, update_cache=False, **kwargs):
        """Get page with list of all idx files for given date or quarter.

        Args:
            update_cache (bool, optional): Whether quarterly directory should update cache. Defaults
                to False.
            kwargs: Any keyword arguments to pass to the client's `get_response` method.

        Returns:
            response (requests.Response): Response object from page with all idx files for
                given quarter and year.
        """
        if self._listings_directory is None or update_cache:
            self._listings_directory = self.client.get_response(self.path, **kwargs)
        return self._listings_directory

    def _get_master_idx_file(self, update_cache=False, **kwargs):
        """Get master file with all filings from given date.

        Args:
            update_cache (bool, optional): Whether master index should be updated
                method call. Defaults to False.
            kwargs: Keyword arguments to pass to
                ``secedgar.client._base.AbstractClient.get_response``.

        Returns:
            text (str): Idx file text.

        Raises:
            EDGARQueryError: If no file of the form master.<DATE>.idx
                is found.
        """
        if self._master_idx_file is None or update_cache:
            if self.idx_filename in self._get_listings_directory().text:
                master_idx_url = "{path}{filename}".format(
                    path=self.path, filename=self.idx_filename)
                self._master_idx_file = self.client.get_response(
                    master_idx_url, self.params, **kwargs).text
            else:
                raise EDGARQueryError("""File {filename} not found.
                                     There may be no filings for the given day/quarter.""".format(
                    filename=self.idx_filename))
        return self._master_idx_file

    def _get_idx_formatted_date(self):
        """Format date for idx file.

        EDGAR changed its master.idx file format twice. In 1995 QTR 1 and in 1998 QTR 2.
        The format went from MMDDYY to YYMMDD to YYYYMMDD.

        Returns:
            date (str): Correctly formatted date for master.idx file.
        """
        if self._date.year < 1995:
            return self._date.strftime("%m%d%y")
        elif self._date < datetime.date(1998, 3, 31):
            return self._date.strftime("%y%m%d")
        else:
            return self._date.strftime("%Y%m%d")

    def save(self,
             directory,
             dir_pattern=None,
             file_pattern="{accession_number}",
             date_format="%Y%m%d",
             download_all=False):
        """Save all daily filings.

        Store all filings for each unique company name under a separate subdirectory
        within given directory argument. Creates directory with date in YYYYMMDD format
        within given directory.

        Args:
            directory (str): Directory where filings should be stored. Will be broken down
                further by company name and form type.
            dir_pattern (str): Format string for subdirectories. Default is `{date}/{cik}`.
                Valid options that must be wrapped in curly braces are `date` and `cik`.
            date_format (str): Format string to use for the `{date}` pattern. Default is ``%Y%m%d``.
            file_pattern (str): Format string for files. Default is `{accession_number}`.
                Valid options are `accession_number`.
            download_all (bool): Type of downloading system, if true downloads all data for the day,
                if false downloads each file in index. Default is `False`.
        """
        if dir_pattern is None:
            dir_pattern = os.path.join("{date}", "{cik}")

        # If "{cik}" is in dir_pattern, it will be passed on and if not it will be ignored
        formatted_dir = dir_pattern.format(date=self._date.strftime(date_format), cik="{cik}")
        self.save_filings(directory, dir_pattern=formatted_dir,
                          file_pattern=file_pattern, download_all=download_all)
