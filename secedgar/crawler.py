# This script will download all the 10-K, 10-Q and 8-K
# provided that of company symbol and its cik code.
from __future__ import print_function  # Compatibility with Python 2
import errno
import os
import requests
import warnings

from bs4 import BeautifulSoup

from secedgar.utils import sanitize_date

from secedgar.utils.exceptions import EDGARQueryError, CIKError

DEFAULT_DATA_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'SEC-Edgar-Data'))


class SecCrawler(object):
    """Main crawler object for SEC filings.

    Args:
        data_path (str): Path where data will be saved.

    .. versionadded:: 0.1.4
    """

    warnings.warn("The SecCrawler class will be deprecated "
                  "in favor of the classes in "
                  "secedgar.filings beginning in v0.2.0.")

    def __init__(self, data_path=DEFAULT_DATA_PATH):
        self.data_path = data_path
        print("Path of the directory where data will be saved: " + self.data_path)

    def __repr__(self):
        return "SecCrawler(data_path={0})".format(self.data_path)

    def _make_directory(self, company_code, cik, priorto, filing_type):
        """Make directory based on filing info.

        Args:
          company_code (str): Code used to help find company filings.
              Often the company's ticker is used.
          cik (Union[str, int]): Central Index Key assigned by SEC.
              See https://www.sec.gov/edgar/searchedgar/cik.htm to search for
              a company's CIK.
          priorto (Union[str, datetime.datetime]): Most recent report to consider.
              Must be in form 'YYYYMMDD' or
              valid ``datetime.datetime`` object.
          filing_type (str): Choose from list of valid filing types.
              Includes '10-Q', '10-K', '8-K', '13-F', 'SD', '4'.

        Returns:
          None
        """
        path = os.path.join(self.data_path, company_code, cik, filing_type)

        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

    def _save_in_directory(self, company_code, cik, priorto, filing_type, docs):
        """Save in directory based on filing info.

        Args:
          company_code (str): Code used to help find company filings.
              Often the company's ticker is used.
          cik (Union[str, int]): Central Index Key assigned by SEC.
              See https://www.sec.gov/edgar/searchedgar/cik.htm to search for
              a company's CIK.
          priorto (Union[str, datetime.datetime]): Most recent report to consider.
              Must be in form 'YYYYMMDD' or
              valid ``datetime.datetime`` object.
          filing_type (str): Choose from list of valid filing types.
              Includes '10-Q', '10-K', '8-K', '13-F', 'SD'.
          docs (str): List of doc paths.

        Returns:
          None
        """
        for (url, doc_name) in docs:
            r = requests.get(url)
            data = r.text
            path = os.path.join(self.data_path, company_code, cik,
                                filing_type, doc_name)

            with open(path, "ab") as f:
                f.write(data.encode('ascii', 'ignore'))

    @staticmethod
    def _create_document_list(data):
        """Create list of txt urls and doc names.

        Args:
          data (str): Raw HTML from SEC Edgar lookup.

        Returns:
          list: Zipped list with tuples of the form
                (<url for txt file>, <doc name>)
        """
        soup = BeautifulSoup(data, features='lxml')
        # store the link in the list
        link_list = [link.string for link in soup.find_all('filinghref')]

        print("Number of files to download: {0}".format(len(link_list)))
        print("Starting download...")

        # List of url to the text documents
        txt_urls = [link[:link.rfind("-")] + ".txt" for link in link_list]
        # List of document doc_names
        doc_names = [url.split("/")[-1] for url in txt_urls]

        return list(zip(txt_urls, doc_names))

    @staticmethod
    def _check_cik(cik):
        """Check if CIK is valid.

        Args:
          cik (Union[str, int]): Central Index Key assigned by SEC.
              See https://www.sec.gov/edgar/searchedgar/cik.htm to search for

        Returns:
          (Union[str, int]): Valid CIK

        Raises:
          CIKError: An error occured while verifying the CIK.
        """
        invalid_str = isinstance(cik, str) and len(cik) != 10
        invalid_int = isinstance(cik, int) and not (999999999 < cik < 10 ** 10)
        invalid_type = not isinstance(cik, (int, str))
        if invalid_str or invalid_int or invalid_type:
            raise CIKError(cik)
        else:
            return cik

    def _fetch_report(self, company_code, cik, priorto, count, filing_type):
        """Fetch filings.

        Args:
          company_code (str): Code used to help find company filings.
              Often the company's ticker is used.
          cik (Union[str, int]): Central Index Key assigned by SEC.
              See https://www.sec.gov/edgar/searchedgar/cik.htm to search for
              a company's CIK.
          priorto (Union[str, datetime.datetime]): Most recent report to consider.
              Must be in form 'YYYYMMDD' or
              valid ``datetime.datetime`` object.
          filing_type (str): Choose from list of valid filing types.
              Includes '10-Q', '10-K', '8-K', '13-F', 'SD'.

        Returns:
          None
        """
        priorto = sanitize_date(priorto)
        cik = self._check_cik(cik)
        self._make_directory(company_code, cik, priorto, filing_type)

        # generate the url to crawl
        base_url = "http://www.sec.gov/cgi-bin/browse-edgar"
        params = {'action': 'getcompany', 'owner': 'exclude', 'output': 'xml',
                  'CIK': cik, 'type': filing_type, 'dateb': priorto, 'count': count}
        print("started {filing_type} {company_code}".format(
            filing_type=filing_type, company_code=company_code))
        r = requests.get(base_url, params=params)
        if r.status_code == 200:
            data = r.text
            # get doc list data
            docs = self._create_document_list(data)

            try:
                self._save_in_directory(
                    company_code, cik, priorto, filing_type, docs)
            except Exception as e:
                print(str(e))  # Need to use str for Python 2.5
        else:
            raise EDGARQueryError(r.status_code)

        print("Successfully downloaded all the files")

    def filing_10Q(self, company_code, cik, priorto, count):
        """Fetch 10Q reports before priorto date.

        Args:
          company_code (str): Code used to help find company filings.
              Often the company's ticker is used.
          cik (Union[str, int]): Central Index Key assigned by SEC.
              See https://www.sec.gov/edgar/searchedgar/cik.htm to search for
              a company's CIK.
          priorto (Union[str, datetime.datetime]): Most recent report to consider.
              Must be in form 'YYYYMMDD' or
              valid ``datetime.datetime`` object.
          filing_type (str): Choose from list of valid filing types.
              Includes '10-Q', '10-K', '8-K', '13-F', 'SD'.

        Returns:
          None
        """
        self._fetch_report(company_code, cik, priorto, count, '10-Q')

    def filing_10K(self, company_code, cik, priorto, count):
        """Fetch 10K reports before priorto date.

        Args:
          company_code (str): Code used to help find company filings.
              Often the company's ticker is used.
          cik (Union[str, int]): Central Index Key assigned by SEC.
              See https://www.sec.gov/edgar/searchedgar/cik.htm to search for
              a company's CIK.
          priorto (Union[str, datetime.datetime]): Most recent report to consider.
              Must be in form 'YYYYMMDD' or
              valid ``datetime.datetime`` object.
          filing_type (str): Choose from list of valid filing types.
              Includes '10-Q', '10-K', '8-K', '13-F', 'SD'.

        Returns:
          None
        """
        self._fetch_report(company_code, cik, priorto, count, '10-K')

    def filing_8K(self, company_code, cik, priorto, count):
        """Fetch 8K reports before priorto date.

        Args:
          company_code (str): Code used to help find company filings.
              Often the company's ticker is used.
          cik (Union[str, int]): Central Index Key assigned by SEC.
              See https://www.sec.gov/edgar/searchedgar/cik.htm to search for
              a company's CIK.
          priorto (Union[str, datetime.datetime]): Most recent report to consider.
              Must be in form 'YYYYMMDD' or
              valid ``datetime.datetime`` object.
          filing_type (str): Choose from list of valid filing types.
              Includes '10-Q', '10-K', '8-K', '13-F', 'SD'.

        Returns:
          None
        """
        self._fetch_report(company_code, cik, priorto, count, '8-K')

    def filing_13F(self, company_code, cik, priorto, count):
        """Fetch 13F reports before priorto date.

        Args:
          company_code (str): Code used to help find company filings.
              Often the company's ticker is used.
          cik (Union[str, int]): Central Index Key assigned by SEC.
              See https://www.sec.gov/edgar/searchedgar/cik.htm to search for
              a company's CIK.
          priorto (Union[str, datetime.datetime]): Most recent report to consider.
              Must be in form 'YYYYMMDD' or
              valid ``datetime.datetime`` object.
          filing_type (str): Choose from list of valid filing types.
              Includes '10-Q', '10-K', '8-K', '13-F', 'SD'.

        Returns:
          None
        """
        self._fetch_report(company_code, cik, priorto, count, '13-F')

    def filing_SD(self, company_code, cik, priorto, count):
        """Fetch SD reports before priorto date.

        Args:
          company_code (str): Code used to help find company filings.
              Often the company's ticker is used.
          cik (Union[str, int]): Central Index Key assigned by SEC.
              See https://www.sec.gov/edgar/searchedgar/cik.htm to search for
              a company's CIK.
          priorto (Union[str, datetime.datetime]): Most recent report to consider.
              Must be in form 'YYYYMMDD' or
              valid ``datetime.datetime`` object.
          filing_type (str): Choose from list of valid filing types.
              Includes '10-Q', '10-K', '8-K', '13-F', 'SD'.

        Returns:
          None
        """
        self._fetch_report(company_code, cik, priorto, count, 'SD')

    def filing_4(self, company_code, cik, priorto, count):
        """Fetch '4' reports before priorto date.

        Args:
          company_code (str): Code used to help find company filings.
              Often the company's ticker is used.
          cik (Union[str, int]): Central Index Key assigned by SEC.
              See https://www.sec.gov/edgar/searchedgar/cik.htm to search for
              a company's CIK.
          priorto (Union[str, datetime.datetime]): Most recent report to consider.
              Must be in form 'YYYYMMDD' or
              valid ``datetime.datetime`` object.
          filing_type (str): Choose from list of valid filing types.
              Includes '10-Q', '10-K', '8-K', '13-F', 'SD'.

        Returns:
          None
        """
        self._fetch_report(company_code, cik, priorto, count, '4')
