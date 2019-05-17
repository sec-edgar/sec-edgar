from SECEdgar.utils.exceptions import EDGARQueryError
from SECEdgar.utils import _sanitize_date
from bs4 import BeautifulSoup
import datetime
import errno
import os
import requests
import time


class _EDGARBase(object):
    """Base class for EDGAR requests.

    Attributes:
        retry_count (int, optional): Desired number of retries if a request fails.
            Defaults to 3.
        pause (float, optional): Pause time between retry attempts.
            Defaults to 0.5.
        count (int, optional): Number of reports to fetch. Defaults to 10.
            Will fetch all if total available is less than count.
    """
    _BASE = "http://www.sec.gov/cgi-bin/"

    def __init__(self, **kwargs):
        self.retry_count = kwargs.get("retry_count", 3)
        self.pause = kwargs.get("pause", 0.5)
        self.count = kwargs.get("count", 10)
        self._params = dict()

    @property
    def url(self):
        raise NotImplementedError

    @property
    def params(self):
        return self._params

    def _execute_query(self, url):
        """Executes HTTP request.

        Args:
            url (str): A properly-formatted url

        Returns:
            response (requests.response): A requests.response object.

        Raises:
            EDGARQueryError: If problems arise when making query.
        """
        for _ in range(self.retry_count + 1):
            response = requests.get(url=url, params=self.params)
            if response.status_code == 200:
                try:
                    return self._validate_response(response)
                except EDGARQueryError:
                    continue
            time.sleep(self.pause)
        return self._handle_error(response)

    def _validate_response(self, response):
        """Ensures response from EDGAR is valid.

        Args:
            response (requests.response): A requests.response object.

        Returns:
            parsed_html (str): Parsed HTML from response.

        Raises:
            EDGARQueryError: If response contains EDGAR error message.
        """
        if "The value you submitted is not valid" in response.text:
            raise EDGARQueryError()
        return BeautifulSoup(response.text, features="html.parser")

    def _handle_error(self, response):
        """Handles all responses which return an error status code.

        Args:
            response(requests.response): Response object.

        Raises:
            EDGARQueryError: If response throws error.
        """
        status_code = response.status_code
        if 400 <= status_code < 500:
            if status_code == 400:
                raise EDGARQueryError("The query could not be completed. "
                                      "The page does not exist.")
            else:
                raise EDGARQueryError("The query could not be completed. "
                                      "There was a client-side error with your "
                                      "request.")
        elif 500 <= status_code < 600:
            raise EDGARQueryError("The query could not be completed. "
                                  "There was a server-side error with "
                                  "your request.")
        else:
            raise EDGARQueryError()

    def _prepare_query(self):
        """Prepares the query url.

        Returns:
            url (str): A formatted url.
        """
        return "%s%s" % (self._BASE, self.url)


class _FilingBase(_EDGARBase):
    """Base class for receiving EDGAR filings.

    Attributes:
        dateb (Union[str, datetime.datetime], optional): Date after which not to fetch reports.
            Defaults to today.
        cik (str): Central Index Key (CIK) for company of interest.
    """

    def __init__(self, cik, **kwargs):
        super(_FilingBase, self).__init__(**kwargs)
        self._dateb = kwargs.get("dateb", datetime.datetime.today())
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
        raise NotImplementedError

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
        """
        path = os.path.join(dir, self.cik, self.filing_type)

        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

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
