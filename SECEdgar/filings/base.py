import datetime
import errno
import os
import requests
from SECEdgar.base import _EDGARBase
from SECEdgar.utils import _sanitize_date
from SECEdgar.utils.exceptions import FilingTypeError, CIKError
from SECEdgar.filings.filing_types import FilingType
from SECEdgar.filings.cik import CIK


class Filing(_EDGARBase):
    """Base class for receiving EDGAR filings.

    Attributes:
        cik (str): Central Index Key (CIK) for company of interest.
        filing_type (str): Valid filing type (case-insensitive).
        dateb (Union[str, datetime.datetime], optional): Date after which not to fetch reports.
            Defaults to today.

    .. versionadded:: 0.1.5
    """

    def __init__(self, cik, filing_type, **kwargs):
        super(Filing, self).__init__(**kwargs)
        self._dateb = kwargs.get("dateb", datetime.datetime.today())
        self._filing_type = self._validate_filing_type(filing_type)
        self._cik = self._validate_cik(cik)
        self._params.update({"action": "getcompany", "owner": "exclude",
                             "output": "xml", "start": 0, "count": self.count,
                             "type": self.filing_type.value})

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
        return Filing._validate_filing_type(self._filing_type)

    @filing_type.setter
    def filing_type(self, ft):
        self._filing_type = self._validate_filing_type(ft)

    @property
    def cik(self):
        return Filing._validate_cik(self._cik)

    @staticmethod
    def _validate_filing_type(filing_type):
        """Validates that given filing type is valid.

        Args:
            filing_type (filings.FilingType): Valid filing type enum.

        Raises:
            FilingTypeError: If filing type is not supported/valid.

        Returns:
            filing_type (filings.FilingType): If filing type is valid, given filing
                type will be returned.
        """
        if not isinstance(filing_type, FilingType):
            raise FilingTypeError(FilingType)

        return filing_type

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

    def _get_urls(self):
        """Get urls for all CIKs given to Filing object.

        Returns:
            urls (list): List of urls for txt files to download.
        """
        if isinstance(self._cik, (list, tuple, set)):
            urls = list()
            for cik in self._cik:
                urls.append(self._get_cik_urls(cik))
            return urls
        else:
            return self._get_cik_urls(self._cik)

    def _get_cik_urls(self, cik):
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
        self._prepare_query()
        data = self._execute_query()
        links = []
        while len(links) < self.count:
            links.extend([link.string for link in data.find_all("filinghref")])
            self.params["start"] += 100
            if len(data.find_all("filinghref")) == 0:
                break
        self.params["start"] = 0
        txt_urls = [link[:link.rfind("-")] + ".txt" for link in links]
        return txt_urls[:self.count]

    def _make_dir(self, directory):
        """Make directory based on filing info.

        Args:
            directory (str): Base directory where filings should be saved from.

        Raises:
            OSError: If there is a problem making the directory.

        Returns:
            None
        """
        path = os.path.join(directory, self.cik, self.filing_type)

        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise OSError

    @staticmethod
    def _sanitize_path(directory):
        return os.path.expanduser(directory)

    @staticmethod
    def _get_filing(url):
        """
        Returns all text data from given filing url.

        Args:
            url (str): URL for specific filing.

        Returns:
            response.text (str): All text from filing.
        """
        response = requests.get(url)
        return response.text

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
        urls = self._get_urls()
        if len(urls) == 0:
            raise ValueError("No text urls available.")
        doc_names = [url.split("/")[-1] for url in urls]
        for (url, doc_name) in list(zip(urls, doc_names)):
            data = self._get_filing(url)
            path = os.path.join(directory, self.cik, self.filing_type, doc_name)
            with open(path, "ab") as f:
                f.write(data.encode("ascii", "ignore"))
