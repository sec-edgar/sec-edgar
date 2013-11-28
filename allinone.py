# This script will download all the 10-K, 10-Q and 8-K 
# provided that of company symbol and its cik code.




from bs4 import BeautifulSoup
import re, urllib2
import requests
import os

def Filing_10Q(companyCode, cik, priorto):
	#Making the directory to save comapny filings
	if not os.path.exists("Crawled Data/"):
		os.makedirs("Crawled Data/")
	if not os.path.exists("Crawled Data/"+str(companyCode)):
		os.makedirs("Crawled Data/"+str(companyCode))
	if not os.path.exists("Crawled Data/"+str(companyCode)+"/"+str(cik)):
		os.makedirs("Crawled Data/"+str(companyCode)+"/"+str(cik))
	if not os.path.exists("Crawled Data/"+str(companyCode)+"/"+str(cik)+"/"+str("10-Q")):
		os.makedirs("Crawled Data/"+str(companyCode)+"/"+str(cik)+"/"+str("10-Q"))
	
	#generate the url to crawl 
	base_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+str(cik)+"&type=10-Q&dateb="+str(priorto)+"&owner=exclude&output=xml&count=100"	
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
	print "List Completed"
	docList = [] # List of URL to the text documents
	docNameList = [] # List of document names

	# Get all the doc
	for k in range(len(linkListFinal)):
		requiredURL = str(linkListFinal[k])[0:len(linkListFinal[k])-11]
		txtdoc = requiredURL+".txt"
		docname = txtdoc.split("/")[len(txtdoc.split("/"))-1]
		docList.append(txtdoc)
		docNameList.append(docname)
	# Save every text document into its respective folder
	for j in range(len(docList)):
		base_url = docList[j]
		r = requests.get(base_url)
		data = r.text
		path = "Crawled Data/"+str(companyCode)+"/"+str(cik)+"/"+str("10-Q")+"/"+str(docNameList[j])
		filename = open(path,"a")
		filename.write(data.encode('ascii', 'ignore'))	

def Filing_10K(companyCode, cik, priorto):
	#Making the directory to save comapny filings
	if not os.path.exists("Crawled Data/"):
		os.makedirs("Crawled Data/")
	if not os.path.exists("Crawled Data/"+str(companyCode)):
		os.makedirs("Crawled Data/"+str(companyCode))
	if not os.path.exists("Crawled Data/"+str(companyCode)+"/"+str(cik)):
		os.makedirs("Crawled Data/"+str(companyCode)+"/"+str(cik))
	if not os.path.exists("Crawled Data/"+str(companyCode)+"/"+str(cik)+"/"+str("10-K")):
		os.makedirs("Crawled Data/"+str(companyCode)+"/"+str(cik)+"/"+str("10-K"))
	
	#generate the url to crawl 
	base_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+str(cik)+"&type=10-K&dateb="+str(priorto)+"&owner=exclude&output=xml&count=100"	
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
	print "List Completed"
	docList = [] # List of URL to the text documents
	docNameList = [] # List of document names

	for k in range(len(linkListFinal)):
		requiredURL = str(linkListFinal[k])[0:len(linkListFinal[k])-11]
		txtdoc = requiredURL+".txt"
		docname = txtdoc.split("/")[len(txtdoc.split("/"))-1]
		docList.append(txtdoc)
		docNameList.append(docname)
	# Save every text document into its respective folder
	for j in range(len(docList)):
		base_url = docList[j]
		r = requests.get(base_url)
		data = r.text
		path = "Crawled Data/"+str(companyCode)+"/"+str(cik)+"/"+str("10-K")+"/"+str(docNameList[j])
		filename = open(path,"a")
		filename.write(data.encode('ascii', 'ignore'))	

def Filing_8K(companyCode, cik, priorto):
	#Making the directory to save comapny filings
	if not os.path.exists("Crawled Data/"):
		os.makedirs("Crawled Data/")
	if not os.path.exists("Crawled Data/"+str(companyCode)):
		os.makedirs("Crawled Data/"+str(companyCode))
	if not os.path.exists("Crawled Data/"+str(companyCode)+"/"+str(cik)):
		os.makedirs("Crawled Data/"+str(companyCode)+"/"+str(cik))
	if not os.path.exists("Crawled Data/"+str(companyCode)+"/"+str(cik)+"/"+str("8-K")):
		os.makedirs("Crawled Data/"+str(companyCode)+"/"+str(cik)+"/"+str("8-K"))
	
	#generate the url to crawl 
	base_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+str(cik)+"&type=8-K&dateb="+str(priorto)+"&owner=exclude&output=xml&count=100"	
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
	print "List Completed"
	docList = [] # List of URL to the text documents
	docNameList = [] # List of document names

	for k in range(len(linkListFinal)):
		requiredURL = str(linkListFinal[k])[0:len(linkListFinal[k])-11]
		txtdoc = requiredURL+".txt"
		docname = txtdoc.split("/")[len(txtdoc.split("/"))-1]
		docList.append(txtdoc)
		docNameList.append(docname)
	# Save every text document into its respective folder
	for j in range(len(docList)):
		base_url = docList[j]
		r = requests.get(base_url)
		data = r.text
		path = "Crawled Data/"+str(companyCode)+"/"+str(cik)+"/"+str("8-K")+"/"+str(docNameList[j])
		filename = open(path,"a")
		filename.write(data.encode('ascii', 'ignore'))	


def test():
	import time
	t1 = time.time()
	# file containig company name and corresponding cik codes
	companyCodeList = list()    # company code list 
	cikList = list()	    # cik code list
	dateList = list()           # pror date list
	try:
		crs = open("file.txt", "r")
	except:
		print "No input file Found"
	
	# get the comapny  quotes and cik number from the file.
	for columns in ( raw.strip().split() for raw in crs ):  
	     	companyCodeList.append(columns[0])
		cikList.append(columns[1])
		dateList.append(columns[2])

	del cikList[0]; del companyCodeList[0]; del dateList[0]
	for i in range(len(cikList)):
		Filing_10Q(str(companyCodeList[i]), str(cikList[i]), str(dateList[i]))
		Filing_10K(str(companyCodeList[i]), str(cikList[i]), str(dateList[i]))
		Filing_8K(str(companyCodeList[i]), str(cikList[i]), str(dateList[i]))
	
	t2 = time.time()
	print "Total Time taken: ",
	print (t2-t1)
	crs.close()
	
if __name__ == '__main__':
	test()	
	

