"""Crawl financial documents.

This script will download all the 10-K, 10-Q and 8-K
provided that of company symbol and its cik code.
"""
from __future__ import print_function
import os
import requests
from bs4 import BeautifulSoup


class SecCrawler():
    """Crawl EDGAR and save files."""

    def __init__(self, path=None):
        """Instantiate object with root path."""
        if path:
            self.path = path
        else:
            self.path = "SEC-Edgar-data/"

        if self.path[-1] != "/":
            self.path = self.path + "/"

    def _make_directory(self, company_code, cik, priorto, filing_type):
        """Making the directory to save company filings."""
        try:
            os.makedirs(self.path + str(company_code) + "/" +
                        str(cik) + "/" + str(filing_type))
        except FileExistsError:
            pass

    def _save_in_directory(self, company_code, cik, priorto, doc_list,
                           doc_name_list, filing_type):
        """Save every text document into its respective folder."""
        base_path = self.path + str(company_code) + "/" + str(cik)
        base_path = base_path + "/" + str(filing_type) + "/"

        for doc_url, doc_name in zip(doc_list, doc_name_list):
            data = requests.get(doc_url).text
            path = base_path + str(doc_name)

            try:
                with open(path, "ab") as filename:
                    filename.write(data.encode('utf-8', 'ignore'))
            except FileNotFoundError:
                with open(path, "wb") as filename:
                    filename.write(data.encode('utf-8', 'ignore'))

    def _create_document_list(self, data):
        # parse fetched data using beatifulsoup
        soup = BeautifulSoup(data)
        # store the link in the list
        link_list = list()

        # If the link is .htm convert it to .html
        for link in soup.find_all('filinghref'):
            url = link.string
            if url.split(".")[-1] == "htm":
                url += "l"
            link_list.append(url)

        print("Number of documents being downloaded: {}".format(
            len(link_list)))

        # List of url to the text documents
        doc_list = list()
        # List of document names
        doc_name_list = list()

        # Get all the doc
        for link in link_list:
            required_url = link[:-11]
            txtdoc = required_url + ".txt"
            docname = txtdoc.split("/")[-1]
            doc_list.append(txtdoc)
            doc_name_list.append(docname)

        return doc_list, doc_name_list

    @staticmethod
    def _get_base_url(cik, ftype, priorto, count):
        base_url = (
            "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=" +
            "{cik}&type={ftype}&dateb={priorto}" +
            "&owner=exclude&output=xml&count={count}"
        ).format(cik=cik, ftype=ftype, priorto=priorto, count=count)

        return base_url

    def _get_filings(self, company_code, cik, priorto, count, ftype):
        """Pull _get_filings data."""
        # Create directory to store said data
        self._make_directory(company_code, cik, priorto, ftype)

        # Get base_url to pull information from
        base_url = self._get_base_url(cik, ftype, priorto, count)

        # URL request
        r = requests.get(base_url)
        data = r.text

        # Retrieve list of documents
        doc_list, doc_name_list = self._create_document_list(data=data)

        # Save documents in the appropriate directory
        self._save_in_directory(
            company_code, cik, priorto, doc_list, doc_name_list, ftype)

    def filing_10q(self, company_code, cik, priorto, count):
        """Pull them 10Qs."""
        self._get_filings(company_code, cik, priorto, count, "10-Q")

    def filing_10k(self, company_code, cik, priorto, count):
        """Pull them 10Ks."""
        self._get_filings(company_code, cik, priorto, count, "10-K")

    def filing_8k(self, company_code, cik, priorto, count):
        """Pull them 8Ks."""
        self._get_filings(company_code, cik, priorto, count, "8-Q")

    def filing_13f(self, company_code, cik, priorto, count):
        """Pull them 8Ks."""
        self._get_filings(company_code, cik, priorto, count, "13-F")
