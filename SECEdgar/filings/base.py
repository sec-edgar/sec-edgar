import datetime
import errno
import os
import requests
from SECEdgar.base import _EDGARBase
from SECEdgar.utils import _sanitize_date
from SECEdgar.utils.exceptions import FilingTypeError


class Filing(_EDGARBase):
    """Base class for receiving EDGAR filings.

    Attributes:
        cik (str): Central Index Key (CIK) for company of interest.
        filing_type (str): Valid filing type (case-insensitive).
        dateb (Union[str, datetime.datetime], optional): Date after which not to fetch reports.
            Defaults to today.

    """
    _VALID_FILING_TYPES = ["10q", "10-q", "10k",
                           "10-k", "8k", "8-k",
                           "13f", "13-f", "4", "sd"]

    def __init__(self, cik, filing_type, **kwargs):
        super(Filing, self).__init__(**kwargs)
        self._dateb = kwargs.get("dateb", datetime.datetime.today())
        self._filing_type = self._validate_filing_type(filing_type)
        self.cik = cik
        self._params.update({"action": "getcompany", "owner": "exclude",
                             "output": "xml", "start": 0, "count": 100, "CIK": self.cik})

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

    def _make_dir(self, dir):
        """Make directory based on filing info.

        Args:
            dir (str): Base directory where filings should be saved from.

        Raises:
            OSError: If there is a problem making the directory.

        Returns:
            None
        """
        path = os.path.join(dir, self.cik, self.filing_type)

        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise OSError

    @staticmethod
    def _sanitize_path(dir):
        return os.path.expanduser(dir)

    def save(self, dir):
        """Save files in specified directory.

        Args:
            dir (str): Path to directory where files should be saved.

        Returns:
            None
        """
        dir = self._sanitize_path(dir)
        self._make_dir(dir)
        txt_urls = self._get_urls()
        doc_names = [url.split("/")[-1] for url in txt_urls]
        for (url, doc_name) in list(zip(txt_urls, doc_names)):
            r = requests.get(url)
            data = r.text
            path = os.path.join(dir, self.cik, self.filing_type, doc_name)
            with open(path, "ab") as f:
                f.write(data.encode("ascii", "ignore"))
