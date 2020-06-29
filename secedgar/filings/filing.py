import datetime
import os
import requests

from secedgar.filings._base import AbstractFiling
from secedgar.client.network_client import NetworkClient
from secedgar.utils import sanitize_date, make_path

from secedgar.filings.cik_lookup import CIKLookup
from secedgar.filings.filing_types import FilingType
from secedgar.utils.exceptions import FilingTypeError


class Filing(AbstractFiling):
    """Base class for receiving EDGAR filings.

    Attributes:
        cik_lookup (str): Central Index Key (CIK) for company of interest.
        filing_type (secedgar.filings.filing_types.FilingType): Valid filing type enum.
        start_date (Union[str, datetime.datetime], optional): Date before which not to
            fetch reports. Stands for "date after."
            Defaults to None (will fetch all filings before end_date).
        end_date (Union[str, datetime.datetime], optional): Date after which not to fetch reports.
            Stands for "date before." Defaults to today.
        count (int): Number of filings to fetch. Will fetch up to `count` if that many filings
            are available. Defaults to all filings available.
        kwargs: See kwargs accepted for :class:`secedgar.client.network_client.NetworkClient`.

    .. versionadded:: 0.1.5
    """

    def __init__(self,
                 cik_lookup,
                 filing_type,
                 start_date=None,
                 end_date=datetime.datetime.today(),
                 client=None,
                 count=None,
                 **kwargs):
        self._start_date = start_date
        self._end_date = end_date
        self._accession_numbers = []
        if not isinstance(filing_type, FilingType):
            raise FilingTypeError
        self._filing_type = filing_type
        # make CIKLookup object for users if not given
        if not isinstance(cik_lookup, CIKLookup):
            cik_lookup = CIKLookup(cik_lookup)
        self._cik_lookup = cik_lookup
        self._params = {
            'action': 'getcompany',
            'dateb': sanitize_date(self.end_date),
            'output': 'xml',
            'owner': 'include',
            'start': 0,
            'type': self.filing_type.value
        }
        self._count = count
        if count is not None:
            self._params['count'] = count
        if start_date is not None:
            self._params['datea'] = sanitize_date(start_date)
        # Make default client NetworkClient and pass in kwargs
        self._client = client if client is not None else NetworkClient(**kwargs)

    @property
    def path(self):
        """str: Path added to client base."""
        return "cgi-bin/browse-edgar"

    @property
    def params(self):
        """:obj:`dict`: Parameters to include in requests."""
        return self._params

    @property
    def client(self):
        """``secedgar.client._base``: Client to use to make requests."""
        return self._client

    @property
    def start_date(self):
        """Union([datetime.datetime, str]): Date before which no filings are fetched."""
        return self._start_date

    @start_date.setter
    def start_date(self, val):
        self._start_date = val
        self._params['datea'] = sanitize_date(val)

    @property
    def end_date(self):
        """Union([datetime.datetime, str]): Date after which no filings are fetched."""
        return self._end_date

    @end_date.setter
    def end_date(self, val):
        self._end_date = val
        self._params['dateb'] = sanitize_date(val)

    @property
    def filing_type(self):
        """``secedgar.filings.FilingType``: FilingType enum of filing."""
        return self._filing_type

    @filing_type.setter
    def filing_type(self, filing_type):
        if not isinstance(filing_type, FilingType):
            raise FilingTypeError
        self._filing_type = filing_type
        self._params['type'] = filing_type.value

    @property
    def count(self):
        """Number of filings to fetch."""
        return self._count

    @count.setter
    def count(self, val):
        if not (val is None or isinstance(val, int)) or val < 1:
            raise TypeError("Count must be positive integer or None.")
        self._count = val
        self._params['count'] = val

    @property
    def accession_numbers(self):
        """List of accession numbers for filings."""
        return self._accession_numbers

    @property
    def cik_lookup(self):
        """``secedgar.cik.CIKLookup``: CIKLookupobject."""
        return self._cik_lookup

    def get_urls(self, **kwargs):
        """Get urls for all CIKs given to Filing object.

        Args:
            **kwargs: Anything to be passed to requests when making get request.
                See keyword arguments accepted for
                ``secedgar.client._base.AbstractClient.get_soup``.

        Returns:
            urls (list): List of urls for txt files to download.
        """
        return {
            key: self._get_urls_for_cik(cik, **kwargs)
            for key, cik in self.cik_lookup.lookup_dict.items()
        }

    # TODO: Change this to return accession numbers that are turned into URLs later
    def _get_urls_for_cik(self, cik, **kwargs):
        """Get all urls for specific company according to CIK.

        Must match start date, end date, filing_type, and count parameters.

        Args:
            cik (str): CIK for company.
            **kwargs: Anything to be passed to requests when making get request.
                See keyword arguments accepted for
                ``secedgar.client._base.AbstractClient.get_soup``.

        Returns:
            txt_urls (list of str): Up to the desired number of URLs for that specific company
            if available.
        """
        self.params['CIK'] = cik
        links = []
        self.params["start"] = 0  # set start back to 0 before paginating

        # TODO: Make paginate utility outside of this class
        while self.count is None or len(links) < self.count:
            data = self.client.get_soup(self.path, self.params, **kwargs)
            links.extend([link.string for link in data.find_all("filinghref")])
            self.params["start"] += self.client.batch_size
            if len(data.find_all("filinghref")) == 0:  # no more filings
                break

        txt_urls = [link[:link.rfind("-")].strip() + ".txt" for link in links]
        # Takes `count` filings at most
        return txt_urls[:self.count]

    def _get_accession_numbers(self, links):
        """Gets accession numbers given list of links.

        Of the form https://www.sec.gov/Archives/edgar/data/<cik>/
        <first part of accession number before '-'>/<accession number>-index.htm.

        Args:
            links (list): List of links to extract accession numbers from.

        Returns:
            List of accession numbers for given links.
        """
        self._accession_numbers = [link.split('/')[-1].replace('-index.htm', '') for link in links]
        return self._accession_numbers

    # TODO: break this method down further
    def save(self, directory):
        """Save files in specified directory.

        Each txt url looks something like:
        https://www.sec.gov/Archives/edgar/data/1018724/000101872419000043/0001018724-19-000043.txt

        Args:
            directory (str): Path to directory where files should be saved.

        Returns:
            None

        Raises:
            ValueError: If no text urls are available for given filing object.
        """
        urls = self.get_urls()
        if all(len(urls[cik]) == 0 for cik in urls.keys()):
            raise ValueError("No filings available.")

        for cik, links in urls.items():
            for link in links:
                data = requests.get(link).text
                accession_number = link.split("/")[-1]
                path = os.path.join(directory, cik, self.filing_type.value)
                make_path(path)
                path = os.path.join(path, accession_number)
                with open(path, "w") as f:
                    f.write(data)
