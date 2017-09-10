SEC-Edgar-Crawler
=============

 Getting filings of various companies at once is really a pain but SEC-Edgar-Crawler does that for you.
 You can download all companies' periodic reports, filings and forms from the EDGAR database in a single command.

Installation
------------- 
 You may have to install the package using pip.
 ```bash
 $ pip install SECEdgar
 ```
 or

 You can clone the project or download it as zip.
 ```bash
 $ git clone https://github.com/rahulrrixe/SEC-Edgar.git
 $ cd SEC-Edgar
 $ python setup.py install
 ```

Running
-------
 Check [data.txt][1] to see the format in which the company names, CIK code date (prior to), and count is given to get the filings of that company.

 Now to run it start python shell
   ```bash
  >>> from SECEdgar.crawler import SecCrawler
  >>> secCrawler = SecCrawler()
  >>> secCrawler.filing_10K('AAPL', '0000320193', '20010101', '10')
   ```
This will download AAPL's 10-K filings and the data will be saved in "SEC-Edgar-data" folder which will be created at run time.

Example 
--------
```python
import time
from SECEdgar.crawler import SecCrawler

def get_filings():
	t1 = time.time()
	
	# create object
	seccrawler = SecCrawler()

	companyCode = 'AAPL'    # company code for apple 
	cik = '0000320193'      # cik code for apple
	date = '20010101'       # date from which filings should be downloaded
	count = '10'            # no of filings
	
	seccrawler.filing_10Q(str(companyCode), str(cik), str(date), str(count))
	seccrawler.filing_10K(str(companyCode), str(cik), str(date), str(count))
	seccrawler.filing_8K(str(companyCode), str(cik), str(date), str(count))
	seccrawler.filing_13F(str(companyCode), str(cik), str(date), str(count))

	t2 = time.time()
	print ("Total Time taken: "),
	print (t2-t1)
	
if __name__ == '__main__':
	get_filings()	
```

Supported Methods
-----------------
Currently this crawler supports only 4 filings 
*  10-K
*  10-Q
*   8-K
*  13-F

I have maintained a list of companies with their CIK code and the file can be downloaded from [here][2].

[1]: https://github.com/rahulrrixe/SEC-Edgar/blob/master/SECEdgar/data.txt
[2]: https://github.com/rahulrrixe/SEC-Edgar/blob/master/SECEdgar/companylist.txt
