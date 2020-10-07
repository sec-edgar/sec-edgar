import os
import re
from abc import abstractmethod
from collections import namedtuple

import requests
from secedgar.client import NetworkClient
from secedgar.filings._base import AbstractFilings
from secedgar.utils import create_subdirectory
from secedgar.utils.exceptions import EDGARQueryError


class AbstractIndexFilings(AbstractFilings):
    """Abstract Base Class for index filings.

    Attributes:
        client (secedgar.client._base, optional): Client to use. Defaults to
            ``secedgar.client.NetworkClient``.
        kwargs: Any keyword arguments to pass to ``NetworkClient`` if no client is specified.
    """

    @property
    def client(self):
        """``secedgar.client._base``: Client to use to make requests."""
        pass

    @property
    def params(self):
        """Params should be empty."""
        pass

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


class IndexFilings(AbstractIndexFilings):

    def __init__(self, client=None, **kwargs):
        self._client = client if client is not None else NetworkClient(**kwargs)
        self._listings_directory = None
        self._master_idx_file = None
        self._filings_dict = None
        self._paths = []
        self._urls = None

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
            update_cache (bool, optional): Whether master index should be updated.
                Defaults to False.
            kwargs: Any keyword arguments to pass to
                ``secedgar.client._base.AbstractClient.get_response``.

        Returns:
            text (str): Idx file text.

        Raises:
            EDGARQueryError: If no file of the form master.<DATE>.idx
                is found.
        """
        if self._master_idx_file is None or update_cache:
            if self.idx_filename in self.get_listings_directory(update_cache).text:
                master_idx_url = "{path}/{filename}".format(
                    path=self.path, filename=self.idx_filename)
                self._master_idx_file = self.client.get_response(
                    master_idx_url, self.params, **kwargs).text
            else:
                raise EDGARQueryError("""File {filename} not found.
                                     There may be no filings for the given day/quarter.""".format(
                    filename=self.idx_filename))
        return self._master_idx_file

    def get_filings_dict(self, **kwargs):
        """Get all filings for day.

        Args:
            kwargs: Any keyword arguments to pass to
                ``secedgar.filings.daily.DailyFilings._get_master_idx_file``.

        Returns:
            filings_dict (dict of list of namedtuples): Dictionary with list of
                filing entries (namedtuples).
        """
        idx_file = self._get_master_idx_file(**kwargs)

        # Will have CIK as keys and list of FilingEntry namedtuples as values
        self._filings_dict = {}
        FilingEntry = namedtuple(
            "FilingEntry",
            ["cik", "company_name", "filing_type", "date_filed", "file_name", "path"])

        # idx file will have lines of the form CIK|Company Name|Form Type|Date Filed|File Name
        entries = re.findall(r'^[0-9]+[|].+[|].+[|][0-9\-]+[|].+$', idx_file, re.MULTILINE)
        for entry in entries:
            fields = entry.split("|")
            path = self.make_path(fields[-1])
            filing_entry = FilingEntry(*fields, path)

            # Add new filing entry to company name's list
            company_name = filing_entry.company_name

            try:
                self._filings_dict[company_name].append(filing_entry)
            except KeyError:
                self._filings_dict[company_name] = [filing_entry]
        return self._filings_dict

    def make_url(self, path):
        """Make URLs from path given.

        Args:
            path (str): Ending of URL

        Returns:
            url (str): Full URL which can be used to access filing.
        """
        return "{base}{path}".format(base=self.client._BASE, path=path)

    @staticmethod
    def make_path(filename):
        """Gets all paths for given day.

        Each path will look something like
        "edgar/data/1000228/0001209191-18-064398.txt".

        Args:
            filename (str): File name to create path from.


        Returns:
            Correct path from filename.
        """
        return "Archives/{filename}".format(filename=filename)

    def get_urls(self, **kwargs):
        """Get all URLs for day.

        Expects client _BASE to have trailing "/" for final URLs.

        Args:
            kwargs: Any keyword arguments to pass to
                ``secedgar.filings._index.IndexFilings.get_filings_dict``.

        Returns:
            urls (dict of dict of list of str): Dict with all URLs to get broken down by
            company name and further by form type. Of the form {company_name: {filing_type: urls}}
        """
        if self._urls is None or kwargs.get('update_cache', False):
            self._urls = {}
            for company_name, filings in self.get_filings_dict(**kwargs).items():
                for filing in filings:
                    url = self.make_url(filing.path)

                    # Create or append to company_name key further breaking down
                    # by filing type
                    try:
                        self._urls[company_name][filing.filing_type].append(url)
                    except KeyError:
                        try:
                            self._urls[company_name][filing.filing_type] = [url]
                        except KeyError:
                            self._urls[company_name] = {filing.filing_type: [url]}
        return self._urls

    def save_filings(self, directory, **kwargs):
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
            kwargs: Any keyword arguments to pass to
                ``secedgar.filings._index.IndexFilings.get_urls``.
        """
        for company_name, filing_types in self.get_urls(**kwargs).items():
            clean_company_name = self.clean_directory_path(company_name)
            for filing_type, urls in filing_types.items():
                subdirectory = os.path.join(directory, clean_company_name, filing_type)
                create_subdirectory(subdirectory)
                for url in urls:
                    accession_number = self.get_accession_number(url)
                    filing_path = os.path.join(subdirectory, accession_number)
                    data = requests.get(url).text
                    with open(filing_path, 'w') as f:
                        f.write(data)
