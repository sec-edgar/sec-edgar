# -*- coding:utf-8 -*-
# This script will download all the 10-K, 10-Q and 8-K
# provided that of company symbol and its cik code.
from __future__ import print_function  # Compatibility with Python 2

import requests
import os
import errno
from bs4 import BeautifulSoup
import datetime

DEFAULT_DATA_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'SEC-Edgar-Data'))


class SecCrawler(object):

    def __init__(self, data_path=DEFAULT_DATA_PATH):
        self.data_path = data_path
        print("Path of the directory where data will be saved: " + self.data_path)

    def __repr__(self):
        return "SecCrawler(data_path={0})".format(self.data_path)

    def _make_directory(self, company_code, cik, priorto, filing_type):
        # Making the directory to save comapny filings
        path = os.path.join(self.data_path, company_code, cik, filing_type)

        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise

    def _save_in_directory(self, company_code, cik, priorto, filing_type, docs):
        # Save every text document into its respective folder
        for (url, doc_name) in docs:
            r = requests.get(url)
            data = r.text
            path = os.path.join(self.data_path, company_code, cik,
                                filing_type, doc_name)

            with open(path, "ab") as f:
                f.write(data.encode('ascii', 'ignore'))

    @staticmethod
    def _create_document_list(data):
        # parse fetched data using beatifulsoup
        # Explicit parser needed
        soup = BeautifulSoup(data, features='html.parser')
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
    def _sanitize_date(date):
        if isinstance(date, datetime.datetime):
            return date.strftime("%Y%m%d")
        elif isinstance(date, str):
            if len(date) != 8:
                raise TypeError('Date must be of the form YYYYMMDD')
        elif isinstance(date, int):
            if date < 10**7 or date > 10**8:
                raise TypeError('Date must be of the form YYYYMMDD')

    def _fetch_report(self, company_code, cik, priorto, count, filing_type):
        priorto = self._sanitize_date(priorto)
        self._make_directory(company_code, cik, priorto, filing_type)

        # generate the url to crawl
        base_url = "http://www.sec.gov/cgi-bin/browse-edgar"
        params = {'action': 'getcompany', 'owner': 'exclude', 'output': 'xml',
                  'CIK': cik, 'type': filing_type, 'dateb': priorto, 'count': count}
        print("started {filing_type} {company_code}".format(
            filing_type=filing_type, company_code=company_code))
        r = requests.get(base_url, params=params)
        data = r.text

        # get doc list data
        docs = self._create_document_list(data)

        try:
            self._save_in_directory(
                company_code, cik, priorto, filing_type, docs)
        except Exception as e:
            print(str(e))  # Need to use str for Python 2.5

        print("Successfully downloaded all the files")

    def filing_10Q(self, company_code, cik, priorto, count):
        self._fetch_report(company_code, cik, priorto, count, '10-Q')

    def filing_10K(self, company_code, cik, priorto, count):
        self._fetch_report(company_code, cik, priorto, count, '10-K')

    def filing_8K(self, company_code, cik, priorto, count):
        self._fetch_report(company_code, cik, priorto, count, '8-K')

    def filing_13F(self, company_code, cik, priorto, count):
        self._fetch_report(company_code, cik, priorto, count, '13-F')

    def filing_SD(self, company_code, cik, priorto, count):
        self._fetch_report(company_code, cik, priorto, count, 'SD')

    def filing_4(self, company_code, cik, priorto, count):
        self._fetch_report(company_code, cik, priorto, count, '4')
