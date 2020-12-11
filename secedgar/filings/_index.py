import os
import re
from abc import abstractmethod
from collections import namedtuple
import asyncio
import requests
import shutil

from secedgar.client import NetworkClient
from secedgar.utils import download_link_to_path, make_path
from secedgar.filings._base import AbstractFiling
from secedgar.utils.exceptions import EDGARQueryError


class IndexFilings(AbstractFiling):
    """Abstract Base Class for index filings.

    Attributes:
        client (secedgar.client._base, optional): Client to use. Defaults to
            ``secedgar.client.NetworkClient``.

        entry_filter (function, optional): A boolean function to determine
            if the FilingEntry should be kept. Defaults to `lambda _: True`.

        kwargs: Any keyword arguments to pass to ``NetworkClient`` if no client is specified.
    """

    def __init__(self, client=None, entry_filter=lambda _: True, **kwargs):
        super().__init__()
        self._client = client if client is not None else NetworkClient(**kwargs)
        self._listings_directory = None
        self._master_idx_file = None
        self._filings_dict = None
        self._paths = []
        self._urls = {}
        self._entry_filter = entry_filter

    @property
    def entry_filter(self):
        """A boolean function to be tested on each listing entry.

        This is tested regardless of download method.
        """
        return self._entry_filter

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
        pass  # pragma: no cover

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
                master_idx_url = "{path}{filename}".format(
                    path=self.path, filename=self.idx_filename)
                print(master_idx_url)
                self._master_idx_file = self.client.get_response(
                    master_idx_url, self.params, **kwargs).text
            else:
                raise EDGARQueryError("""File {filename} not found.
                                     There may be no filings for the given day/quarter.""".format(
                    filename=self.idx_filename))
        return self._master_idx_file

    def get_filings_dict(self, update_cache=False, **kwargs):
        """Get all filings inside an index file.

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
                if not self.entry_filter(entry):
                    continue

                # Add new filing entry to CIK's list
                if entry.cik in self._filings_dict:
                    self._filings_dict[entry.cik].append(entry)
                else:
                    self._filings_dict[entry.cik] = [entry]
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

    @abstractmethod
    def get_file_names(self):
        """Passed to child classes."""
    @property
    def tar_path(self):
        """str: Tar.gz path added to the client base."""
        return "Archives/edgar/Feed/{year}/QTR{num}/".format(year=self.year, num=self.quarter)

    def save_filings(self, directory, dir_pattern=None, file_pattern=None, download_all=False):
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
            dir_pattern (str): Format string for subdirectories. Default is `{cik}`.
                Valid options are `cik`.
            file_pattern (str): Format string for files. Default is `{accession_number}`.
                Valid options are `accession_number`.
            download_all (bool): Type of downloading system, if true downloads all tar files,
                if false downloads each file in index. Default is `False`.
        """
        urls = self._check_urls_exist()

        if dir_pattern is None:
            dir_pattern = '{cik}'
        if file_pattern is None:
            file_pattern = '{accession_number}'
        REQUESTS_PER_SECOND = 10

        async def download_async(link, path):
            asyncio.create_task(download_link_to_path(link, path))
            await asyncio.sleep(1/REQUESTS_PER_SECOND)

        async def wait_for_download_async(inputs):
            await asyncio.wait([download_async(link, path) for link, path in inputs])

        if download_all:
            # Download tar files into huge temp directory
            extract_directory = os.path.join(directory, 'temp')
            make_path(extract_directory)
            tar_files = self.get_file_names()
            for filename in tar_files:
                response = requests.get(self.make_url(self.tar_path + filename), stream=True)
                download_target = os.path.join(extract_directory, filename)
                if response.status_code == 403:
                    # Ignore days that do not exist in daily backup record
                    print('WARNING', filename, 'DOES NOT EXIST')
                    continue
                else:
                    # Throw an error for bad status codes
                    response.raise_for_status()

                with open(download_target, 'wb') as handle:
                    for block in response.iter_content(1024):
                        handle.write(block)

                shutil.unpack_archive(download_target, extract_directory)
                os.remove(download_target)

            # Get a list of all extracted files
            (_, _, extracted_files) = next(os.walk(extract_directory))
            # Now check extracted_files against urls
            for _, links in urls.items():
                for link in links:
                    link_cik = link.split('/')[-2]
                    filepath = self.get_accession_number(link).split('.')[0]
                    possible_endings = ['nc', 'corr04', 'corr03', 'corr02', 'coor01']
                    for ending in possible_endings:
                        full_filepath = filepath + '.' + ending
                        # If the filepath is found, move it to the correct path
                        if full_filepath in extracted_files:

                            formatted_dir = dir_pattern.format(cik=link_cik)
                            formatted_file = file_pattern.format(
                                accession_number=self.get_accession_number(link))
                            full_dir = os.path.join(directory, formatted_dir)
                            make_path(full_dir)
                            path = os.path.join(full_dir, formatted_file)
                            old_path = os.path.join(extract_directory, full_filepath)
                            shutil.copyfile(old_path, path)
                            break
            # Now delete extract directory
            shutil.rmtree(extract_directory)
        else:
            inputs = []
            for company, links in urls.items():
                formatted_dir = dir_pattern.format(cik=company)
                for link in links:
                    formatted_file = file_pattern.format(
                        accession_number=self.get_accession_number(link))
                    path = os.path.join(directory, formatted_dir, formatted_file)
                    inputs.append((link, path))

            loop = asyncio.get_event_loop()
            loop.run_until_complete(wait_for_download_async(inputs))
