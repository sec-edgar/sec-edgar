from abc import ABC, abstractmethod
from secedgar.filings.filing_extractor import FilingExtractor
import string
import os
import sys
import asyncio
from secedgar.utils import make_path
from secedgar.utils.exceptions import EDGARQueryError
from secedgar.client.aiohttp_client import RateLimitedClientSession
from aiohttp import ClientSession, TCPConnector
import importlib.util
import time


class AbstractFiling(ABC):
    """Abstract base class for all SEC EDGAR filings.

    .. versionadded:: 0.1.5
    """
    @property
    @abstractmethod
    def rate_limit(self):
        """Passed to child classes."""
        pass

    async def wait_for_download_async(self, inputs):
        """Asynchronously download links into files using rate limit."""
        time.sleep(1)

        async def fetch_and_save(link, path, session):
            async with await session.get(link) as response:
                # print(response.headers['Content-Length'])
                contents = await response.read()
                if contents.startswith(b'<!DOCTYPE'):
                    raise EDGARQueryError("You hit the rate limit")
                make_path(os.path.dirname(path))
                with open(path, "wb") as f:
                    f.write(contents)

        conn = TCPConnector(limit=self.rate_limit)
        raw_client = ClientSession(connector=conn, headers={'Connection': 'keep-alive'})
        async with raw_client:
            client = RateLimitedClientSession(raw_client, self.rate_limit)
            tasks = [asyncio.ensure_future(fetch_and_save(link, path, client))
                     for link, path in inputs]
            for f in asyncio.as_completed(tasks):
                await f

    """``secedgar.filings.filing_extractor`: Extractor class used."""
    extractor = FilingExtractor()

    def extract(self, directory, out_dir=None, create_subdir=True, rm_infile=False):
        """Extract filings in directory."""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.txt'):
                    self.extractor.process(os.path.join(root, file),
                                           out_dir=out_dir,
                                           create_subdir=create_subdir,
                                           rm_infile=rm_infile)

    @property
    @abstractmethod
    def client(self):
        """``secedgar.client._base``: Client to use to make requests."""
        pass  # pragma: no cover

    @property
    @abstractmethod
    def params(self):
        """:obj:`dict`: Parameters to include in requests."""
        pass  # pragma: no cover

    @property
    @abstractmethod
    def path(self):
        """str: Path added to client base."""
        pass  # pragma: no cover

    @abstractmethod
    def get_urls(self, **kwargs):
        """Get all URLs for filings.

        Args:
            kwargs: Anything to be passed to requests when making GET request.

        Returns:
            urls (dict): Dictionary of urls for txt files to download.
                Keys are lookup terms and values are list of URLs.
        """
        pass  # pragma: no cover

    @abstractmethod
    def save(self, directory):
        """Save filings in directory.

        Args:
            directory (str): Path to directory where files should be saved.

        Returns:
            None
        """
        pass  # pragma: no cover

    @staticmethod
    def get_accession_number(url):
        """Get accession number from filing URL.

        .. note::
           All URLs are expected to end with /{accession number}.txt
        """
        return url.split("/")[-1]

    @staticmethod
    def clean_directory_path(path):
        """Clean string to use as directory name.

        Args:
            path (str): Directory name to clean.
        """
        allowed = string.digits + string.ascii_letters + string.whitespace
        stripped = "".join(c for c in path if c in allowed)
        return stripped.replace(" ", "_")

    def _check_urls_exist(self):
        """Wrapper around `get_urls` to check if there is a positive number of URLs.

        .. note:: This method will not check if the URLs are valid. Simply if they exist.

        Raises:
            ValueError: If no URLs exist, then ValueError is raised.

        Returns:
            urls (dict): Result of `get_urls` method.
        """
        urls = self.get_urls()
        if all(len(urls[cik]) == 0 for cik in urls.keys()):
            raise ValueError("No filings available.")
        return urls
