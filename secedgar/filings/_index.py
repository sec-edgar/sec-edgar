import os
import re
import requests
from abc import abstractmethod
from collections import namedtuple

from secedgar.client import NetworkClient
from secedgar.utils import make_path

from secedgar.filings._base import AbstractFiling
from secedgar.utils.exceptions import EDGARQueryError


class IndexFilings(AbstractFiling):
    def __init__(self, client=None):
        super().__init__()
        self._client = client if client is not None else NetworkClient()
        self._listings_directory = None
        self._master_idx_file = None
        self._filings_dict = None
        self._paths = []
        self._urls = []

    @property
    def client(self):
        """``secedgar.client._base``: Client to use to make requests."""
        return self._client

    @property
    def params(self):
        """Params should be empty."""
        return {}

    @property
    @abstractmethod
    def year(self):
        pass

    @property
    @abstractmethod
    def quarter(self):
        pass

    @property
    @abstractmethod
    def idx_filename(self):
        pass

    def get_listings_directory(self, update_cache=False, **kwargs):
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
            self._listings_directory = self.client.get_response(self.path, self.params, **kwargs)
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
            if self.idx_filename in self.get_listings_directory().text:
                master_idx_url = "{path}/{filename}".format(
                    path=self.path, filename=self.idx_filename)
                self._master_idx_file = self.client.get_response(
                    master_idx_url, self.params, **kwargs).text
            else:
                raise EDGARQueryError("""File {filename} not found.
                                     There may be no filings for the given day/quarter.""".format(
                    filename=self.idx_filename))
        return self._master_idx_file

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

    def save_filings(self, directory):
        """Save all filings.

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
