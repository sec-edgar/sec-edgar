import datetime
import os
import requests

from SECEdgar.filings.base import AbstractFiling
from SECEdgar.client.network_client import NetworkClient
from SECEdgar.utils import sanitize_date, make_path

from SECEdgar.filings.cik import CIK
from SECEdgar.filings.filing_types import FilingType
from SECEdgar.utils.exceptions import FilingTypeError


class Filing(AbstractFiling):
    """Base class for receiving EDGAR filings.

    Attributes:
        cik (str): Central Index Key (CIK) for company of interest.
        filing_type (SECEdgar.filings.filing_types.FilingType): Valid filing type enum.
        start_date (Union[str, datetime.datetime], optional): Date before which not to
            fetch reports. Stands for "date after."
            Defaults to None (will fetch all filings before end_date).
        end_date (Union[str, datetime.datetime], optional): Date after which not to fetch reports.
            Stands for "date before." Defaults to today.

    .. versionadded:: 0.1.5
    """

    # TODO: Maybe allow NetworkClient to take in kwargs
    #  (set to None and if None, create NetworkClient with kwargs)
    def __init__(self,
                 cik,
                 filing_type,
                 start_date=None,
                 end_date=datetime.datetime.today(),
                 client=None,
                 **kwargs):
        self._start_date = start_date
        self._end_date = end_date
        if not isinstance(filing_type, FilingType):
            raise FilingTypeError
        self._filing_type = filing_type
        if not isinstance(cik, CIK):  # make CIK for users if not given
            cik = CIK(cik)
        self._cik = cik
        self._accession_numbers = []
        self._params = {
            'action': 'getcompany',
            'dateb': sanitize_date(self.end_date),
            'output': 'xml',
            'owner': 'include',
            'start': 0,
            'type': self.filing_type.value
        }
        if kwargs.get(count) is not None:
            self._params['count'] = kwargs.get('count')
        if start_date is not None:
            self._params['datea'] = sanitize_date(start_date)
        # Make default client NetworkClient and pass in kwargs
        if client is None:
            self._client = NetworkClient(**kwargs)

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
        """``SECEdgar.client.base``: Client to use to make requests."""
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
        """``SECEdgar.filings.FilingType``: FilingType enum of filing."""
        return self._filing_type

    @filing_type.setter
    def filing_type(self, filing_type):
        if not isinstance(filing_type, FilingType):
            raise FilingTypeError
        self._filing_type = filing_type
        self._params['type'] = filing_type.value

    @property
    def accession_numbers(self):
        return self._accession_numbers

    @property
    def ciks(self):
        """:obj:`list` of :obj:`str`: List of CIK strings."""
        return self._cik.ciks

    def get_urls(self, **kwargs):
        """Get urls for all CIKs given to Filing object.

        Args:
            kwargs: Anything to be passed to requests when making get request.

        Returns:
            urls (list): List of urls for txt files to download.
        """
        urls = []
        for cik in self.ciks:
            urls.extend(self._get_urls_for_cik(cik, **kwargs))
        return urls

    # TODO: Change this to return accession numbers that are turned into URLs later
    def _get_urls_for_cik(self, cik, **kwargs):
        """
        Get all urls for specific company according to CIK that match
        start date, end date, filing_type, and count parameters.

        Args:
            cik (str): CIK for company.
            kwargs: Anything to be passed to requests when making get request.

        Returns:
            txt_urls (list of str): Up to the desired number of URLs for that specific company
            if available.
        """
        self.params['CIK'] = cik
        links = []
        self.params["start"] = 0  # set start back to 0 before paginating

        # TODO: Make paginate utility outside of this class
        while len(links) < self._client.count:
            data = self._client.get_soup(self.path, self.params, **kwargs)
            links.extend([link.string for link in data.find_all("filinghref")])
            # TODO: Consider making client adopt most efficient count
            self.params["start"] += self._client.count
            if len(data.find_all("filinghref")) == 0:
                break  # break if no more filings left

        txt_urls = [link[:link.rfind("-")] + ".txt" for link in links]
        return txt_urls[:self.client.count]

    @staticmethod
    def _get_accession_numbers(links):
        """Gets accession numbers given list of links of the form
        https://www.sec.gov/Archives/edgar/data/<cik>/<first part of accession number before '-'>
        /<accession number>-index.htm

        Args:
            links (list): List of links to extract accession numbers from.

        Returns:
            List of accession numbers for given links.
        """
        return [link.split('/')[-1].replace('-index.htm', '') for link in links]

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
        if len(urls) == 0:
            raise ValueError("No filings available.")
        doc_names = [url.split("/")[-1] for url in urls]
        for (url, doc_name) in list(zip(urls, doc_names)):
            cik = doc_name.split('-')[0]
            data = requests.get(url).text
            path = os.path.join(directory, cik, self.filing_type.value)
            make_path(path)
            path = os.path.join(path, doc_name)
            with open(path, "w") as f:
                f.write(data)
