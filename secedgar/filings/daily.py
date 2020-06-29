import datetime
import os
import re
import requests

from collections import namedtuple

from secedgar.client import NetworkClient
from secedgar.filings._base import AbstractFiling
from secedgar.utils import make_path

from secedgar.utils.exceptions import EDGARQueryError


class DailyFilings(AbstractFiling):
    """Class for retrieving all daily filings from https://www.sec.gov/Archives/edgar/daily-index.

    Attributes:
        date (datetime.datetime): Date of daily filing to fetch.
        client (secedgar.client._base.AbstractClient): Client to use for fetching data.
            Defaults to ``secedgar.client.NetworkClient`` if none is given.
    """

    def __init__(self, date, client=None):
        if not isinstance(date, datetime.datetime):
            raise TypeError(
                "Date must be given as datetime object. Was given type {type}.".format(
                    type=type(date)))
        self._date = date
        self._client = client if client is not None else NetworkClient()
        # Caches for responses
        self._quarterly_directory = None
        self._master_idx_file = None
        self._filings_dict = None
        self._paths = []
        self._urls = []

    @property
    def client(self):
        """``secedgar.client._base``: Client to use to make requests."""
        return self._client

    @property
    def quarter(self):
        """Get quarter number from date attribute."""
        return (self._date.month - 1) // 3 + 1

    @property
    def path(self):
        """str: Path added to client base.

        .. note::
            The trailing slash at the end of the path is important.
            Omitting will raise EDGARQueryError.
        """
        return "Archives/edgar/daily-index/{year}/QTR{num}/".format(
            year=self._date.year, num=self.quarter)

    @property
    def params(self):
        """Params should be empty."""
        return {}

    def _get_quarterly_directory(self, update_cache=False, **kwargs):
        """Get page with list of all idx files for given date's year and quarter.

        Args:
            update_cache (bool, optional): Whether quarterly directory should update cache. Defaults
                to False.
            kwargs: Any keyword arguments to pass to the client's `get_response` method.

        Returns:
            response (requests.Response): Response object from page with all idx files for
                given quarter and year.
        """
        if self._quarterly_directory is None or update_cache:
            self._quarterly_directory = self.client.get_response(self.path, self.params, **kwargs)
        return self._quarterly_directory

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
            formatted_date = self._get_idx_formatted_date()
            formatted_file_name = "master.{date}.idx".format(date=formatted_date)
            if formatted_file_name in self._get_quarterly_directory().text:
                master_idx_url = "{path}/master.{date}.idx".format(
                    path=self.path, date=formatted_date)
                self._master_idx_file = self.client.get_response(
                    master_idx_url, self.params, **kwargs).text
            else:
                raise EDGARQueryError("""File master.{date}.idx not found.
                                     There may be no filings for this day.""".format(
                    date=formatted_date))
        return self._master_idx_file

    def get_paths(self, update_cache=False):
        """Gets all paths for given day.

        Each path will look something like
        "edgar/data/1000228/0001209191-18-064398.txt".

        Args:
            update_cache (bool, optional): Whether urls should be updated on each method call.
                Defaults to False.

        Returns:
            urls (list of str): List of urls.
        """
        if len(self._paths) == 0:
            for entries in self.get_filings_dict().values():
                for entry in entries:
                    # Will be of the form
                    self._paths.append(
                        "Archives/{file_name}".format(
                            file_name=entry.file_name))
        return self._paths

    def get_filings_dict(self, update_cache=False, **kwargs):
        """Get all filings for day.

        Args:
            update_cache (bool, optional): Whether filings dict should be
                updated on each method call. Defaults to False.
            kwargs: Any kwargs to pass to _get_master_idx_file. See
                ``secedgar.filings.daily.DailyFilings._get_master_idx_file``.
        """
        if self._filings_dict is None or update_cache:
            idx_file = self._get_master_idx_file(**kwargs)
            # Will have CIK as keys and list of FilingEntry namedtuples as values
            self._filings_dict = {}
            FilingEntry = namedtuple(
                "FilingEntry", ["cik", "company_name", "form_type", "date_filed", "file_name"])
            # idx file will have lines of the form CIK|Company Name|Form Type|Date Filed|File Name
            entries = re.findall(r'^[0-9]+[|].+[|].+[|][0-9]+[|].+$', idx_file, re.MULTILINE)
            for entry in entries:
                fields = entry.split("|")
                # Add new filing entry to CIK's list
                if fields[0] in self._filings_dict:
                    self._filings_dict[fields[0]].append(FilingEntry(*fields))
                else:
                    self._filings_dict[fields[0]] = [FilingEntry(*fields)]
        return self._filings_dict

    def make_url(self, path):
        """Make URLs from path given.

        Args:
            path (str): Ending of URL

        Returns:
            url (str): Full URL which can be used to access filing.
        """
        return "{base}{path}".format(base=self.client._BASE, path=path)

    def get_urls(self):
        """Get all URLs for day.

        Expects client _BASE to have trailing "/" for final URLs.

        Returns:
            urls (list of str): List of all URLs to get.
        """
        if len(self._urls) == 0:
            paths = self.get_paths()
            self._urls = [self.make_url(path) for path in paths]
        return self._urls

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
