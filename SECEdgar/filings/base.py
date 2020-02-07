import datetime
import os
import requests

from SECEdgar.base import _EDGARBase
from SECEdgar.client.network_client import NetworkClient
from SECEdgar.utils import sanitize_date, make_path

from SECEdgar.filings.cik import CIK
from SECEdgar.filings.filing_types import FilingType
from SECEdgar.utils.exceptions import FilingTypeError


class Filing(_EDGARBase):
    """Base class for receiving EDGAR filings.

    Attributes:
        cik (str): Central Index Key (CIK) for company of interest.
        filing_type (SECEdgar.filings.filing_types.FilingType): Valid filing type enum.
        dateb (Union[str, datetime.datetime], optional): Date after which not to fetch reports.
            Stands for "date before." Defaults to today.

    .. versionadded:: 0.1.5
    """

    # TODO: Maybe allow NetworkClient to take in kwargs
    #  (set to None and if None, create NetworkClient with kwargs)
    def __init__(self, cik, filing_type, dateb=datetime.datetime.today(), client=None, **kwargs):
        self.dateb = dateb
        self.filing_type = filing_type
        if not isinstance(cik, CIK):  # make CIK for users if not given
            cik = CIK(cik)
        self._ciks = cik.ciks
        self._params = {
            'action': 'getcompany',
            'count': kwargs.get('count', 10),
            'dateb': self.dateb,
            'output': 'xml',
            'owner': 'exclude',
            'start': 0,
            'type': self.filing_type.value
        }
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
    def dateb(self):
        """Union([datetime.datetime, str]): Date after which no filings are fetched."""
        return self._dateb

    @dateb.setter
    def dateb(self, val):
        self._dateb = sanitize_date(val)

    @property
    def filing_type(self):
        """``SECEdgar.filings.FilingType``: FilingType enum of filing."""
        return self._filing_type

    @filing_type.setter
    def filing_type(self, filing_type):
        if not isinstance(filing_type, FilingType):
            raise FilingTypeError(FilingType)
        self._filing_type = filing_type

    @property
    def ciks(self):
        """:obj:`list` of :obj:`str`: List of CIK strings."""
        return self._ciks

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

    def _get_urls_for_cik(self, cik, **kwargs):
        """
        Get all urls for specific company according to CIK that match
        dateb, filing_type, and count parameters.

        Args:
            cik (str): CIK for company.
            kwargs: Anything to be passed to requests when making get request.

        Returns:
            txt_urls (list of str): Up to the desired number of URLs for that specific company
            if available.
        """
        self.params['CIK'] = cik
        data = self._client.get_soup(self.path, self.params, **kwargs)
        links = []

        # TODO: Make paginate utility outside of this class
        while len(links) < self._client.count:
            links.extend([link.string for link in data.find_all("filinghref")])
            self.params["start"] += 100
            if len(data.find_all("filinghref")) == 0:
                break
        self.params["start"] = 0  # set start back to 0 after paginating
        txt_urls = [link[:link.rfind("-")] + ".txt" for link in links]
        return txt_urls[:self.client.count]

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
