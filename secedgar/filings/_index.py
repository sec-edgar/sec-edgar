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
    """Abstract Base Class for index filings.

    Attributes:
        client (secedgar.client._base, optional): Client to use. Defaults to
            ``secedgar.client.NetworkClient``.
        kwargs: Any keyword arguments to pass to ``NetworkClient`` if no client is specified.
    """

    def __init__(self, client=None, **kwargs):
        super().__init__()
        self._client = client if client is not None else NetworkClient(**kwargs)
        self._listings_directory = None
        self._master_idx_file = None
        self._filings_dict = None
        self._paths = []
        self._urls = {}

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
        """Passed to children classes."""
        pass

    @property
    @abstractmethod
    def quarter(self):
        """Passed to children classes."""
        pass  # pragma: no cover

    @property
    @abstractmethod
    def idx_filename(self):
        """Passed to children classes."""
        pass  # pragma: no cover

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
                "FilingEntry", ["cik", "company_name", "form_type", "date_filed", "file_name",
                                "path"])
            # idx file will have lines of the form CIK|Company Name|Form Type|Date Filed|File Name
            entries = re.findall(r'^[0-9]+[|].+[|].+[|][0-9\-]+[|].+$', idx_file, re.MULTILINE)
            for entry in entries:
                fields = entry.split("|")
                path = "Archives/{file_name}".format(file_name=fields[-1])
                entry = FilingEntry(*fields, path=path)
                # Add new filing entry to CIK's list
                if fields[0] in self._filings_dict:
                    self._filings_dict[fields[0]].append(entry)
                else:
                    self._filings_dict[fields[0]] = [entry]
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
        if not self._urls:
            filings_dict = self.get_filings_dict()
            self._urls = {company: [self.make_url(entry.path) for entry in entries]
                          for company, entries in filings_dict.items()}
        return self._urls

    def save_filings(self, directory):
        """Save all filings.

        Will store all filings for each unique CIK under a separate subdirectory
        within given directory argument.

        Ex:
        my_directory
        |
        ---- CIK 1
             |
             ---- ...txt files
        ---- CIK 2
             |
             ---- ...txt files

        Args:
            directory (str): Directory where filings should be stored.
        """
        urls = self._check_urls_exist()

        for company, links in urls.items():
            for link in links:
                data = requests.get(link).text
                path = os.path.join(directory, company)
                make_path(path)
                path = os.path.join(path, self.get_accession_number(link))
                with open(path, "w") as f:
                    f.write(data)
