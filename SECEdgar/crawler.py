# -*- coding:utf-8 -*-
# This script will download all the 10-K, 10-Q and 8-K
# provided that of company symbol and its cik code.

import requests
import os
import errno
from bs4 import BeautifulSoup
from config import DEFAULT_DATA_PATH



class SecCrawler():

    def __init__(self):
        self.hello = "Welcome to Sec Cralwer!"
        print DEFAULT_DATA_PATH

    def make_directory(self, company_code, cik, priorto, filing_type):
        # Making the directory to save comapny filings
        path = os.path.join(DEFAULT_DATA_PATH, company_code, cik, filing_type)

        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise

    def save_in_directory(self, company_code, cik, priorto, doc_list, doc_name_list, filing_type):
        # Save every text document into its respective folder
        for j in range(len(doc_list)):
            base_url = doc_list[j]
            r = requests.get(base_url)
            data = r.text
            path = os.join.path(DEFAULT_DATA_PATH, company_code, cik,
                filing_type, doc_name_list[j])

            with open(path, "a+") as f:
                f.write(data.encode('ascii', 'ignore'))

    def filing_10Q(self, company_code, cik, priorto, count):

        self.make_directory(company_code, cik, priorto, '10-Q')

        # generate the url to crawl
        base_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+str(cik)+"&type=10-Q&dateb="+str(priorto)+"&owner=exclude&output=xml&count="+str(count)
        print ("started 10-Q" + str(company_code))
        r = requests.get(base_url)
        data = r.text
        soup = BeautifulSoup(data)
        link_list = list()

        # If the link is .htm convert it to .html
        for link in soup.find_all('filinghref'):
            url = link.string
            if link.string.split(".")[len(link.string.split("."))-1] == "htm":
                url += "l"
                link_list.append(url)
        link_list_final = link_list

        print ("Number of files to download %s", len(link_list_final))
        print ("Starting download....")

        # List of URL to the text documents
        doc_list = list()
        # List of document names
        doc_name_list = list()

        # Get all the doc
        for k in range(len(link_list_final)):
            required_url = str(link_list_final[k])[0:len(link_list_final[k]) - 11]
            txtdoc = required_url + ".txt"
            docname = txtdoc.split("/")[len(txtdoc.split("/")) - 1]
            doc_list.append(txtdoc)
            doc_name_list.append(docname)

        try:
            self.save_in_directory(company_code, cik, priorto, doc_list, doc_name_list, '10-Q')
        except Exception, e:
            print str(e)

        print "Successfully downloaded all the files"


    def filing_10K(self, companyCode, cik, priorto, count):
        try:
            self.make_directory(companyCode,cik, priorto, '10-K')
        except Exception,e:
             print str(e)

        #generate the url to crawl
        base_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+str(cik)+"&type=10-K&dateb="+str(priorto)+"&owner=exclude&output=xml&count="+str(count)
        print ("started 10-K"+str(companyCode))
        r = requests.get(base_url)
        data = r.text
        soup = BeautifulSoup(data) # Initializing to crawl again
        linkList=[] # List of all links from the CIK page

        # If the link is .htm convert it to .html
        for link in soup.find_all('filinghref'):
            URL = link.string
            if link.string.split(".")[len(link.string.split("."))-1] == "htm":
                URL+="l"
                linkList.append(URL)
        linkListFinal = linkList

        print ("Number of files to download %s", len(linkListFinal))
        print ("Starting download....")

        docList = [] # List of URL to the text documents
        docNameList = [] # List of document names

        for k in range(len(linkListFinal)):
            requiredURL = str(linkListFinal[k])[0:len(linkListFinal[k])-11]
            txtdoc = requiredURL+".txt"
            docname = txtdoc.split("/")[len(txtdoc.split("/"))-1]
            docList.append(txtdoc)
            docNameList.append(docname)

        try:
            self.save_in_directory(companyCode, cik, priorto, docList, docNameList, '10-K')
        except Exception,e:
            print str(e)

        print "Successfully downloaded all the files"

    def filing_8K(self, companyCode, cik, priorto, count):
        try:
            self.make_directory(companyCode,cik, priorto, '8-K')
        except Exception,e:
            print str(e)

        #generate the url to crawl
        base_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+str(cik)+"&type=8-K&dateb="+str(priorto)+"&owner=exclude&output=xml&count="+str(count)
        print ("started 8-K" + str(companyCode))
        r = requests.get(base_url)
        data = r.text
        soup = BeautifulSoup(data) # Initializing to crawl again
        linkList=[] # List of all links from the CIK page

        # If the link is .htm convert it to .html
        for link in soup.find_all('filinghref'):
            URL = link.string
            if link.string.split(".")[len(link.string.split("."))-1] == "htm":
                URL+="l"
                linkList.append(URL)
        linkListFinal = linkList

        print ("Number of files to download %s", len(linkListFinal))
        print ("Starting download....")

        docList = [] # List of URL to the text documents
        docNameList = [] # List of document names

        for k in range(len(linkListFinal)):
            requiredURL = str(linkListFinal[k])[0:len(linkListFinal[k])-11]
            txtdoc = requiredURL+".txt"
            docname = txtdoc.split("/")[len(txtdoc.split("/"))-1]
            docList.append(txtdoc)
            docNameList.append(docname)

        try:
            self.save_in_directory(companyCode, cik, priorto, docList, docNameList, '8-K')
        except Exception,e:
            print str(e)

        print "Successfully downloaded all the files"

    def filing_13F(self, companyCode, cik, priorto, count):
        try:
            self.make_directory(companyCode,cik, priorto, '13-F')
        except Exception,e:
            print str(e)

        #generate the url to crawl
        base_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+str(cik)+"&type=13F&dateb="+str(priorto)+"&owner=exclude&output=xml&count="+str(count)
        print ("started 10-Q"+str(companyCode))
        r = requests.get(base_url)
        data = r.text
        soup = BeautifulSoup(data) # Initializing to crawl again
        linkList=[] # List of all links from the CIK page

        # If the link is .htm convert it to .html
        for link in soup.find_all('filinghref'):
            URL = link.string
            if link.string.split(".")[len(link.string.split("."))-1] == "htm":
                URL+="l"
                linkList.append(URL)
        linkListFinal = linkList

        print ("Number of files to download %s", len(linkListFinal))
        print ("Starting download....")

        docList = [] # List of URL to the text documents
        docNameList = [] # List of document names

        # Get all the doc
        for k in range(len(linkListFinal)):
            requiredURL = str(linkListFinal[k])[0:len(linkListFinal[k])-11]
            txtdoc = requiredURL+".txt"
            docname = txtdoc.split("/")[len(txtdoc.split("/"))-1]
            docList.append(txtdoc)
            docNameList.append(docname)

        try:
            self.save_in_directory(companyCode, cik, priorto, docList, docNameList, '13-F')
        except Exception,e:
            print str(e)

        print "Successfully downloaded all the files"

