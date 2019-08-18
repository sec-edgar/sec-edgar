import datetime
import errno
import os
import requests
from SECEdgar.base import _EDGARBase
from SECEdgar.utils import _sanitize_date
from SECEdgar.utils.exceptions import FilingTypeError, CIKError


class Filing(_EDGARBase):
    """Base class for receiving EDGAR filings.

    Attributes:
        cik (str): Central Index Key (CIK) for company of interest.
        filing_type (str): Valid filing type (case-insensitive).
        dateb (Union[str, datetime.datetime], optional): Date after which not to fetch reports.
            Defaults to today.

    .. versionadded:: 0.1.5
    """
    _VALID_FILING_TYPES = ("10-q", "10-k",
                           "8-k", "13-f",
                           "4", "sd", "def 14a",
                           "defa14a")

    def __init__(self, cik, filing_type, **kwargs):
        super(Filing, self).__init__(**kwargs)
        self._dateb = kwargs.get("dateb", datetime.datetime.today())
        self._filing_type = self._validate_filing_type(filing_type)
        self._cik = cik
        self._params.update({"action": "getcompany", "owner": "exclude",
                             "output": "xml", "start": 0, "count": 100, "CIK": self.cik,
                             "type": self.filing_type})

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
        return self._validate_filing_type(self._filing_type)

    @filing_type.setter
    def filing_type(self, ft):
        self._filing_type = self._validate_filing_type(ft)

    @property
    def cik(self):
        return self._validate_cik(self._cik)

    @cik.setter
    def cik(self, val):
        self._cik = self._validate_cik(val)

    def _validate_filing_type(self, filing_type):
        """Validates that given filing type is valid.

        Args:
            filing_type (str): Valid filing type (case-insensitive).

        Raises:
            FilingTypeError: If filing type is not supported/valid.

        Returns:
            filing_type (str): If filing type is valid, given filing
                type will be returned.
        """
        if filing_type.lower() not in self._VALID_FILING_TYPES:
            raise FilingTypeError()
        return filing_type

    def _validate_cik(self, cik):
        """Validates that given CIK *could* be valid.

        Args:
            cik (Union[str, int]): Central index key (CIK) to validate.

        Returns:
            cik (Union[str, int]): Validated CIK.
                Note that the CIK is only validated in
                that it *could* be valid. All CIKs
                must be 10 digits, but not all 10 digit
                numbers are valid CIKs.

        Raises:
            ValueError: If given cik is not str or int
            CIKError: If cik is not a 10 digit number.
        """
        if not isinstance(cik, (str, int)):
            raise ValueError("CIK must be of type str or int.")
        elif isinstance(cik, str):
            if len(cik) != 10 or not cik.isdigit():
                raise CIKError(cik)
        elif isinstance(cik, int):
            if cik not in range(10**9, 10**10):
                raise CIKError(cik)
        return cik

    def _get_urls(self):
        """Get urls for txt files.

        Returns:
            urls (list): List of urls for txt files to download.
        """
        url = self._prepare_query()
        data = self._execute_query(url)
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
    def _sanitize_path(dir):
        return os.path.expanduser(dir)

    def save(self, directory):
        """Save files in specified directory.

        Args:
            directory (str): Path to directory where files should be saved.

        Returns:
            None
        """
        directory = self._sanitize_path(directory)
        self._make_dir(directory)
        txt_urls = self._get_urls()
        if len(txt_urls) == 0:
            raise Exception("No text urls")
        doc_names = [url.split("/")[-1] for url in txt_urls]
        for (url, doc_name) in list(zip(txt_urls, doc_names)):
            r = requests.get(url)
            data = r.text
            path = os.path.join(directory, self.cik, self.filing_type, doc_name)
            with open(path, "ab") as f:
                f.write(data.encode("ascii", "ignore"))
