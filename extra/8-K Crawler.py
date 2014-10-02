# Script to crawl and save 13-F filing from the Edgar and save that in structured directory format

from bs4 import BeautifulSoup
import re, urllib2
import requests
import os


# Procedure to retrieve the CIK codes with the entered SEC Code
sec = input("Enter the SEC Code : ")
count = 0 # Count for displaying 40 elements on the Company Search page
tddoc=[1] # Initialize to any non-empty list
companyList = []

# The loop checks for comapnies in a sector (SEC NO.) and append those coampany's cik
# number in the companyList. If we can provide CIK number directly then comment this loop 
# and add the cik codes to cikList
while(len(tddoc)!=0):
	#print type(sec)
	base_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&SIC="+str(sec)+"&owner=include&match=&start="+str(count)+"&count=40hidefilings=0"
	r = requests.get(base_url)
	data = r.text
	#print data
	soup = BeautifulSoup(data)
	tddoc = soup.find_all("td")
	for i in range(0,len(tddoc)):
		companyList.append(tddoc[i].string)
		i+=2
	count+=40

# `companyList` now contains the list of companies corresponding to the entered SEC code.
cikList = []
#cikList.append("0000320193")

for i in range(0,len(companyList),3):
	cikList.append(companyList[i])
# List of CIK codes to be crawled has been extracted into `cikList`

# Below procedure creates the required folders if they don't already exist.
if not os.path.exists("Crawled Data/"):
	os.makedirs("Crawled Data/")
if not os.path.exists("Crawled Data/"+str(sec)):
	os.makedirs("Crawled Data/"+str(sec))
for j in range(len(cikList)):
	if not os.path.exists("Crawled Data/"+str(sec)+"/"+str(cikList[j])):
		os.makedirs("Crawled Data/"+str(sec)+"/"+str(cikList[j]))
	if not os.path.exists("Crawled Data/"+str(sec)+"/"+str(cikList[j])+"/"+str("10-Q")):
		os.makedirs("Crawled Data/"+str(sec)+"/"+str(cikList[j])+"/"+str("10-Q"))

for i in range(len(cikList)):
	base_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+str(cikList[i])+"&type=10-Q&dateb=&owner=exclude&output=xml&count=100"	
	#print base_url
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
	#print linkListFinal
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
		path = "Crawled Data/"+str(sec)+"/"+str(cikList[i])+"/"+str("10-Q")+"/"+str(docNameList[j])
		filename = open(path,"a")
		filename.write(data.encode('ascii', 'ignore'))
