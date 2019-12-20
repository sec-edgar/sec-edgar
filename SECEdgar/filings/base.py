import datetime
import errno
import os

import requests

from SECEdgar.base import _EDGARBase
from SECEdgar.filings.cik import CIK
from SECEdgar.filings.filing_types import FilingType
from SECEdgar.utils import _sanitize_date
from SECEdgar.utils.exceptions import FilingTypeError


class Filing(_EDGARBase):
    """Base class for receiving EDGAR filings.

    Attributes:
        cik (str): Central Index Key (CIK) for company of interest.
        filing_type (SECEdgar.filings.filing_types.FilingType): Valid filing type enum.
        dateb (Union[str, datetime.datetime], optional): Date after which not to fetch reports.
            Defaults to today.

    .. versionadded:: 0.1.5
    """

    def __init__(self, cik, filing_type, dateb=datetime.datetime.today(), **kwargs):
        super(Filing, self).__init__(**kwargs)
        self._dateb = _sanitize_date(dateb)
        self._filing_type = self._validate_filing_type(filing_type)
        if not isinstance(cik, CIK):  # make CIK for users if not given
            cik = CIK(cik)
        self._ciks = cik.ciks
        self._params['action'] = 'getcompany'
        self._params['owner'] = 'exclude'
        self._params['output'] = 'xml'
        self._params['start'] = 0
        self._params['type'] = self.filing_type.value
        self._params['dateb'] = self._dateb

    @property
    def url(self):
        return "browse-edgar"

    @property
    def dateb(self):
        return self._dateb

    @dateb.setter
    def dateb(self, val):
        self._dateb = _sanitize_date(val)

    @property
    def filing_type(self):
        return self._filing_type

    @filing_type.setter
    def filing_type(self, filing_type):
        if not isinstance(filing_type, FilingType):
            raise FilingTypeError(FilingType)
        self._filing_type = filing_type

    @property
    def ciks(self):
        return self._ciks

    @staticmethod
    def _validate_filing_type(filing_type):
        if not isinstance(filing_type, FilingType):
            raise FilingTypeError(FilingType)
        return filing_type

    def get_urls(self):
        """Get urls for all CIKs given to Filing object.

        Returns:
            urls (list): List of urls for txt files to download.
        """
        urls = []
        for cik in self.ciks:
            urls += self._get_urls_for_cik(cik)
        return urls

    def _get_urls_for_cik(self, cik):
        """
        Get all urls for specific company according to CIK that match
        dateb, filing_type, and count parameters.

        Args:
            cik (str): CIK for company.

        Returns:
            txt_urls (list of str): Up to the desired number of URLs for that specific company
            if available.
        """
        self.params['CIK'] = cik
        data = self.get_soup()
        links = []

        # paginate
        while len(links) < self._client.count:
            links.extend([link.string for link in data.find_all("filinghref")])
            self.params["start"] += 100
            if len(data.find_all("filinghref")) == 0:
                break
        self.params["start"] = 0  # set start back to 0 after paginating
        txt_urls = [link[:link.rfind("-")] + ".txt" for link in links]
        return txt_urls[:self.client.count]

    @staticmethod
    def _make_path(path):
        """Make directory based on filing info.

        Args:
            path (str): Path to be made if it doesn't exist.

        Raises:
            OSError: If there is a problem making the path.

        Returns:
            None
        """

        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise OSError

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
            self._make_path(path)
            path = os.path.join(path, doc_name)
            with open(path, "w") as f:
                f.write(data)
