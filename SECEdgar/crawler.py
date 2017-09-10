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
        self.hello = 'Welcome to SEC Crawler!'
        print('Path of the directory where data will be saved: ' + DEFAULT_DATA_PATH)

    def make_directory(self, company_code, cik, priorto, filing_type):
        
        # Make the directory to save company filings
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

            with open(path, 'ab') as f:
                f.write(data.encode('ascii', 'ignore'))
        
    def get_filing(self, company_code, cik, filingtype, priorto, count):
		
		if self.filingtype.lower() not in ['10q', '10k', '8k', '13f']:
			
			print 'Use a valid filing type. \'10q\', \'10k\', \'8k\', or \'13f\''
			
		else:
			self.make_directory(company_code, cik, priorto, filingtype)
			
			# generate the url to crawl
			urlfilingtype = ''
			if filingtype.lower() = '10q':
				urlfilingtype = '10-Q'
			elif filingtype.lower() = '10k':
				urlfilingtype = '10-K'
			elif filingtype.lower() = '8k':
				urlfilingtype = '8-K'
			elif filingtype.lower() = '13f':
				urlfilingtype = '13-F'
						
			base_url = 'http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK='+str(cik)+'&type=' + urlfilingtype + '&dateb='+str(priorto)+'&owner=exclude&output=xml&count='+str(count)
			
			print ('Retrieving ' + urlfilingtype + 's for ' + str(company_code))
			r = requests.get(base_url)
			data = r.text
			
			# get doc list data
            doc_list, doc_name_list = self.create_document_list(data)

			try:
				self.save_in_directory(company_code, cik, priorto, doc_list, doc_name_list, filingtype)
			except Exception as e:
				print (str(e))

			print ("Successfully downloaded all the files")

    def create_document_list(self, data):
        
        # Parse fetched data using beautifulsoup
        soup = BeautifulSoup(data)
        # Store the link in the list
        link_list = list()

        # If the link is .htm convert it to .html
        for link in soup.find_all('filinghref'):
            url = link.string
            if link.string.split('.')[len(link.string.split('.'))-1] == 'htm':
                url += 'l'
            link_list.append(url)
        link_list_final = link_list

        print ('Number of files to download {0}'.format(len(link_list_final)))
        print ('Starting download...')

        # List of url to the text documents
        doc_list = list()
        # List of document names
        doc_name_list = list()

        # Get all the docs
        for k in range(len(link_list_final)):
            required_url = link_list_final[k].replace('-index.html', '')
            txtdoc = required_url + '.txt'
            docname = txtdoc.split('/')[-1]
            doc_list.append(txtdoc)
            doc_name_list.append(docname)
        return doc_list, doc_name_list

    def get_ciks_for_company_name(self, company_name):
        url = 'https://www.sec.gov/cgi-bin/cik_lookup'
        
        payload = {
                'company':str(company_name),
                'submit':'Submit'
                }
        
        r = requests.post(url, payload)
        data = r.text
        
        soup = BeautifulSoup(data)
        
        cik_list = []
        company_list = []
        
        for pre in soup.find_all('pre'):
            for a in pre.find_all('a'):
                if 'CIK=' in a['href']:
                    cik_list.append(a.get_text())
                    company_list.append(str(a.next_sibling).strip())
        
        return cik_list, company_list
    
    def get_cik_for_ticker(self, ticker):
        url = 'http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=' + str(ticker)
        
        r = requests.get(url)
        data = r.text
        
        soup = BeautifulSoup(data)
        
        cik = str(soup.find('input', {'name':'CIK'})['value'])
        
        return cik
