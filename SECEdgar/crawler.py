# This script will download all the 10-K, 10-Q and 8-K 
# provided that of company symbol and its cik code.

from bs4 import BeautifulSoup
import re
import requests
import os

class SecCrawler():

	def __init__(self):
		self.hello = "Welcome to Sec Cralwer!"

	def make_directory(self, companyCode, cik, priorto, filing_type):
		# Making the directory to save comapny filings
		if not os.path.exists("SEC-Edgar-data/"):
			os.makedirs("SEC-Edgar-data/")
		if not os.path.exists("SEC-Edgar-data/"+str(companyCode)):
			os.makedirs("SEC-Edgar-data/"+str(companyCode))
		if not os.path.exists("SEC-Edgar-data/"+str(companyCode)+"/"+str(cik)):
			os.makedirs("SEC-Edgar-data/"+str(companyCode)+"/"+str(cik))
		if not os.path.exists("SEC-Edgar-data/"+str(companyCode)+"/"+str(cik)+"/"+str("filing_type")):
			os.makedirs("SEC-Edgar-data/"+str(companyCode)+"/"+str(cik)+"/"+str("filing_type"))
	
	def save_in_directory(self, companyCode, cik, priorto, docList, docNameList, filing_type):
		# Save every text document into its respective folder
		for j in range(len(docList)):
			base_url = docList[j]
			r = requests.get(base_url)
			data = r.text
			path = "SEC-Edgar-data/"+str(companyCode)+"/"+str(cik)+"/"+str(filing_type)+"/"+str(docNameList[j])
			filename = open(path,"a")
			filename.write(data.encode('ascii', 'ignore'))	


	def filing_10Q(self, companyCode, cik, priorto, count):
		try:
			self.make_directory(companyCode,cik, priorto, '10-Q')
		except:
			print "Not able to create directory"
		
		#generate the url to crawl 
		base_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+str(cik)+"&type=10-Q&dateb="+str(priorto)+"&owner=exclude&output=xml&count="+str(count)	
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
			self.save_in_directory(companyCode, cik, priorto, docList, docNameList, '10-Q')
		except:
			print "Not able to save the file :( "

		print "Successfully downloaded all the files"


	def filing_10K(self, companyCode, cik, priorto, count):
		try:
			self.make_directory(companyCode,cik, priorto, '10-K')
		except:
			print "Not able to create directory"
		
		#generate the url to crawl 
		base_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+str(cik)+"&type=10-K&dateb="+str(priorto)+"&owner=exclude&output=xml&count="+str(count)	
		print ("started !0-K"+str(companyCode))
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
		except:
			print "Not able to save the file :( "

		print "Successfully downloaded all the files"

	def filing_8K(self, companyCode, cik, priorto, count):
		try:
			self.make_directory(companyCode,cik, priorto, '8-K')
		except:
			print "Not able to create directory"
		
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
		except:
			print "Not able to save the file :( "

		print "Successfully downloaded all the files"

	def filing_13F(self, companyCode, cik, priorto, count):
		try:
			self.make_directory(companyCode,cik, priorto, '13-F')
		except:
			print "Not able to create directory"
		
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
		except:
			print "Not able to save the file :( "

		print "Successfully downloaded all the files"

