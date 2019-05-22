from bs4 import BeautifulSoup
import requests
from SECEdgar.utils.exceptions import EDGARQueryError
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

    .. versionadded:: 0.1.5
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
