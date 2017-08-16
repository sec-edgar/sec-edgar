# -*- coding:utf-8 -*-
# This script will download all the 10-K, 10-Q and 8-K
# provided that of company symbol and its cik code.

import requests
import os
import errno
from bs4 import BeautifulSoup
from config import DEFAULT_DATA_PATH


class SECCrawlerException(Exception):
    pass


class UnknownFormTypeError(SECCrawlerException):
    pass


class SecCrawler():

    FORM_10K = '10-K'
    FORM_10Q = '10-Q'
    FORM_8K = '8-K'
    FORM_13F = '13F'
    FORM_SD = 'SD'
    FORM_PREM14A = 'PREM14A'

    FORM_TYPES = (
        FORM_10K,
        FORM_10Q,
        FORM_8K,
        FORM_13F,
        FORM_SD,
        FORM_PREM14A,
    )

    BASE_URL = "http://www.sec.gov/cgi-bin/browse-edgar"

    def __init__(self):
        self.hello = "Welcome to Sec Cralwer!"
        print("Path of the directory where data will be saved: " + DEFAULT_DATA_PATH)

    def make_directory(self, company_code, cik, priorto, filing_type):
        # Making the directory to save comapny filings
        path = os.path.join(DEFAULT_DATA_PATH, company_code, cik, filing_type)

        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise

    def save_in_directory(self, company_code, cik, priorto, doc_list,
        doc_name_list, filing_type):
        # Save every text document into its respective folder
        for j in range(len(doc_list)):
            base_url = doc_list[j]
            r = requests.get(base_url)
            data = r.text
            path = os.path.join(DEFAULT_DATA_PATH, company_code, cik,
                filing_type, doc_name_list[j])

            with open(path, "ab") as f:
                f.write(data.encode('ascii', 'ignore'))

    def filing_generic_form(self, company_code, cik, prior_to, count, form_type, include_owner=False):
        if form_type not in self.FORM_TYPES:
            raise UnknownFormTypeError()

        self.make_directory(company_code, cik, prior_to, form_type)
        print ("started {form_type} {company_code}".format(form_type=form_type, company_code=company_code))

        params = {
            'action': 'getcompany',
            'CIK': str(cik),
            'type': form_type,
            'dateb': str(prior_to),
            'owner': 'include' if include_owner else 'exclude',
            'output': 'xml',
            'count': str(count),
        }

        response = requests.get(self.BASE_URL, params=params)

        data = response.text
        doc_list, doc_name_list = self.create_document_list(data)

        try:
            self.save_in_directory(company_code, cik, prior_to, doc_list, doc_name_list, form_type)
        except Exception as e:
            print (str(e))

        print ("Successfully downloaded all the files")

    def filing_10Q(self, company_code, cik, priorto, count):
        self.filing_generic_form(company_code, cik, priorto, count, self.FORM_10Q)

    def filing_10K(self, company_code, cik, priorto, count):
        self.filing_generic_form(company_code, cik, priorto, count, self.FORM_10K)

    def filing_8K(self, company_code, cik, priorto, count):
        self.filing_generic_form(company_code, cik, priorto, count, self.FORM_8K)

    def filing_13F(self, company_code, cik, priorto, count):
        self.filing_generic_form(company_code, cik, priorto, count, self.FORM_13F)

    def filing_SD(self, company_code, cik, priorto, count):
        self.filing_generic_form(company_code, cik, priorto, count, self.FORM_SD)

    def create_document_list(self, data):
        # parse fetched data using beatifulsoup
        soup = BeautifulSoup(data)
        # store the link in the list
        link_list = list()

        # If the link is .htm convert it to .html
        for link in soup.find_all('filinghref'):
            url = link.string
            if link.string.split(".")[len(link.string.split("."))-1] == "htm":
                url += "l"
            link_list.append(url)
        link_list_final = link_list

        print ("Number of files to download {0}".format(len(link_list_final)))
        print ("Starting download....")

        # List of url to the text documents
        doc_list = list()
        # List of document names
        doc_name_list = list()

        # Get all the doc
        for k in range(len(link_list_final)):
            required_url = link_list_final[k].replace('-index.html', '')
            txt_doc = required_url + ".txt"
            doc_name = txt_doc.split("/")[-1]
            doc_list.append(txt_doc)
            doc_name_list.append(doc_name)
        return doc_list, doc_name_list

