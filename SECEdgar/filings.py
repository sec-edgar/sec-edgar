from bs4 import BeautifulSoup
import datetime
import requests
from SECEdgar.exceptions import EDGARQueryError
from SECEdgar.util import _sanitize_date
import time


class _FilingBase(object):
    """Base class for receiving EDGAR filings.

    Attributes:
        retry_count (int, optional): Desired number of retries if a request fails.
            Defaults to 3.
        pause (float, optional): Pause time between retry attempts.
            Defaults to 0.5.
        count (int, optional): Number of reports to fetch. Defaults to 10.
            Will fetch all if total available is less than count.
        dateb (Union[str, datetime.datetime], optional): Date after which not to fetch reports.
            Defaults to today.
    """
    _BASE = "http://www.sec.gov/cgi-bin/"

    def __init__(self, cik, **kwargs):
        self.retry_count = kwargs.get("retry_count", 3)
        self.pause = kwargs.get("pause", 0.5)
        self.count = kwargs.get("count", 10)
        self.dateb = _sanitize_date(kwargs.get("dateb", datetime.datetime.today()))
        self.cik = cik
        self._params = {"action": "getcompany", "owner": "exclude",
                        "output": "xml", "start": 0, "count": 100, "CIK": self.cik}

    @property
    def params(self):
        return self._params

    @property
    def url(self):
        return "browse-edgar"

    @property
    def filing_type(self):
        raise NotImplementedError

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

    def _get_urls(self):
        url = self._prepare_query()
        data = self._execute_query(url)
        links = []
        while len(links) < self.count:
            links.extend([link.string for link in data.find_all('filinghref')])
            self.params['start'] += 100
            if len(data.find_all('filinghref')) == 0:
                break
        self.params['start'] = 0
        txt_urls = [link[:link.rfind("-")] + ".txt" for link in links]
        return txt_urls[:self.count]


class Filing10K(_FilingBase):

    def __init__(self, cik, **kwargs):
        super(Filing10K, self).__init__(cik, **kwargs)

    @property
    def filing_type(self):
        return "10-K"

    @property
    def params(self):
        self._params["type"] = self.filing_type
        return self._params


class Filing10Q(_FilingBase):

    def __init__(self, cik, **kwargs):
        super(Filing10Q, self).__init__(cik, **kwargs)

    @property
    def filing_type(self):
        return "10-Q"

    @property
    def params(self):
        self._params["type"] = self.filing_type
        return self._params


class Filing8K(_FilingBase):

    def __init__(self, cik, **kwargs):
        super(Filing8K, self).__init__(cik, **kwargs)

    @property
    def filing_type(self):
        return "8-K"

    @property
    def params(self):
        self._params["type"] = self.filing_type
        return self._params


class FilingSD(_FilingBase):

    def __init__(self, cik, **kwargs):
        super(FilingSD, self).__init__(cik, **kwargs)

    @property
    def filing_type(self):
        return "SD"

    @property
    def params(self):
        self._params["type"] = self.filing_type
        return self._params


class Filing13F(_FilingBase):

    def __init__(self, cik, **kwargs):
        super(Filing13F, self).__init__(cik, **kwargs)

    @property
    def filing_type(self):
        return "13-F"

    @property
    def params(self):
        self._params["type"] = self.filing_type
        return self._params


class Filing4(_FilingBase):

    def __init__(self, cik, **kwargs):
        super(Filing4, self).__init__(cik, **kwargs)

    @property
    def filing_type(self):
        return "4"

    @property
    def params(self):
        self._params["type"] = self.filing_type
        return self._params
