import datetime
import errno
import os

import requests

from SECEdgar.base import _EDGARBase
from SECEdgar.filings.cik import CIK
from SECEdgar.filings.filing_types import FilingType
from SECEdgar.utils import _sanitize_date
from SECEdgar.utils.exceptions import FilingTypeError, CIKError


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
        self._cik = self._validate_cik(cik).ciks
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
        return _sanitize_date(self._dateb)

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
    def cik(self):
        return Filing._validate_cik(self._cik)

    @staticmethod
    def _validate_cik(cik):
        """Validates that given CIK *could* be valid.

        Args:
            cik (Union[CIK, str, int]): Central index key (CIK) to validate.

        Returns:
            cik (Union[str, list of str]): Validated CIK.
                Note that the CIK is only validated in
                that it *could* be valid. CIKs formatted as
                10 digits, but not all 10 digit
                numbers are valid CIKs.

        Raises:
            ValueError: If given cik is not str, int, or CIK object.
            CIKError: If cik is not a 10 digit number or valid CIK object
        """
        # creating CIK object should check to see if ciks are valid
        if not isinstance(cik, CIK):
            if not isinstance(cik, (str, int)):
                raise ValueError("CIK must be of type str or int.")
            elif isinstance(cik, str):
                if len(cik) != 10 or not cik.isdigit():
                    raise CIKError(cik)
            elif isinstance(cik, int):
                if cik > 10**10:
                    raise CIKError(cik)
                elif cik < 10**9:
                    return str(cik).zfill(10)  # pad with zeros if less than 10 digits given
            return str(cik)
        else:
            return cik.cik

    def get_urls(self):
        """Get urls for all CIKs given to Filing object.

        Returns:
            urls (list): List of urls for txt files to download.
        """
        return list(*[self._get_urls_for_cik(cik) for cik in self.cik])

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

    def _make_dir(self, directory):
        """Make directory based on filing info.

        Args:
            directory (str): Base directory where filings should be saved from.

        Raises:
            OSError: If there is a problem making the directory.

        Returns:
            None
        """
        path = os.path.join(directory, self.cik, self.filing_type.value)

        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise OSError

    @staticmethod
    def _sanitize_path(directory):
        return os.path.expanduser(directory)

    def save(self, directory):
        """Save files in specified directory.

        Args:
            directory (str): Path to directory where files should be saved.

        Returns:
            None

        Raises:
            ValueError: If no text urls are available for given filing object.
        """
        directory = self._sanitize_path(directory)
        self._make_dir(directory)
        urls = self.get_urls()
        if len(urls) == 0:
            raise ValueError("No urls available.")
        doc_names = [url.split("/")[-1] for url in urls]
        for (url, doc_name) in list(zip(urls, doc_names)):
            data = requests.get(url).text
            path = os.path.join(directory, self.cik, self.filing_type.value, doc_name)
            with open(path, "ab") as f:
                f.write(data.encode("ascii", "ignore"))
