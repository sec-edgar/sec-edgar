Edgar-Crawler
=============

 Getting filings of various comapanies at once is really a pain but Edgar-Crawler does that for you.
 you can Download all companies  periodic reports, filings and forms from EDGAR database in a single command.
 
 Clone the project or download it as zip. 
 
 You may have to install a few packages.
 ```bash
 $ pip install BeautifulSoup4
 $ pip install requests
 ```
 Change file.txt to add the name of company's, CIK code and date (prior to) to get the filings of that company.
 
 Now to run it
   ```bash
 $ python allinone.py
   ```
 This will download the company's 8-K, 10-K, 10-Q filings of company's listed in file.txt. The data will be saved in "Crawled
 Data" folder in the same folder where allinone.py is.
 
 The pypy package will be available soon.
 

