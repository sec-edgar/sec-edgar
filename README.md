Edgar-Crawler
=============

 Getting filings of various comapanies at once is really a pain but Edgar-Crawler does that for you.
 you can Download all companies  periodic reports, filings and forms from EDGAR database in a single command.
 
 You may have to install the package using pip.
 ```bash
 $ pip install SEC-Edgar
 ```
 or

 You can clone the project or download it as zip.
 ```bash
 $ git clone https://github.com/rahulrrixe/SEC-Edgar.git
 $ cd SEC-Edgar
 $ python setup.py install
 ```

 Change file.txt to add the name of company's, CIK code and date (prior to) to get the filings of that company.
 
 Now to run it
   ```bash
 $ python allinone.py
   ```
 This will download the company's 8-K, 10-K, 10-Q filings of company's listed in file.txt. The data will be saved in "Crawled
 Data" folder in the same folder where allinone.py is.
 
 The pypy package will be available soon.
 

