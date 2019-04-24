# SEC-Edgar-Crawler

Getting filings of various companies at once is really a pain, but SEC-Edgar does that for you. You can download all of a company's periodic reports, filings and forms from the EDGAR database with a single command.

Installation
============

You may have to install the package using pip:
```bash
$ pip install SECEdgar
```
or

You can clone the project or download it as zip.
```
$ git clone https://github.com/rahulrrixe/SEC-Edgar.git  
$ cd SEC-Edgar  
$ python setup.py install
```

Running
=======

Check
[data.txt](https://github.com/rahulrrixe/SEC-Edgar/blob/master/SECEdgar/data.txt) to see the format in which name of company's, CIK code date (prior to) and count is given to get the filings of that company.

To run it, start python shell

```console
>>> from SECEdgar.crawler import SecCrawler

>>> crawler = SecCrawler()
Path of the directory where data will be saved: /path/to/your/dir

>>> crawler.filing_10K('AAPL', '0000320193', '20010101', '10')
started 10-K AAPL
Number of files to download: 8
Starting download...
Successfully downloaded all the files
```

This will download the AAPL company's 10-K filings. By default, the data will be saved in the "SEC-Edgar-data" folder which will be created on the run time. If you would like to save the data at a different location, you can use
```console
>>> crawler = SecCrawler('/path/to/location')
```

Example
=======

``` python
import time
from SECEdgar.crawler import SecCrawler

def get_filings():
    t1 = time.time()
    seccrawler = SecCrawler() # create object

    companyCode = 'AAPL'    # company code for apple
    cik = '0000320193'      # cik code for apple
    date = '20010101'       # date from which filings should be downloaded
    count = '10'            # no of filings

    seccrawler.filing_10Q(companyCode, cik, date, count)
    seccrawler.filing_10K(companyCode, cik, date, count)
    seccrawler.filing_8K(companyCode, cik, date, count)
    seccrawler.filing_13F(companyCode, cik, date, count)


    t2 = time.time()
    print ("Total Time taken: {0}".format(t2-t1))

if __name__ == '__main__':
    get_filings()
```

Supported Methods
=================

Currently this crawler only supports 4 filings

   -   10-K
   -   10-Q
   -   8-K
   -   13-F

I have maintained a list of companies with their cik codes and the file
can be downloaded from
[here](https://github.com/rahulrrixe/SEC-Edgar/blob/master/SECEdgar/companylist.txt).
