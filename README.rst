SEC-Edgar-Crawler
=================

|Build Status|

Getting filings of various companies at once is really a pain, but
SEC-Edgar does that for you. You can download all of a company’s
periodic reports, filings and forms from the EDGAR database with a
single command.

Installation
------------

You may have to install the package using pip:

.. code:: bash

   $ pip install SECEdgar

or

You can clone the project or download it as zip.

.. code:: bash

   $ git clone https://github.com/rahulrrixe/SEC-Edgar.git  
   $ cd SEC-Edgar  
   $ python setup.py install

Running
-------


:warning: The following code is experimental in v0.1.5. Please refer to docs on how to use the `SecCrawler` class if installing v0.1.4 or earlier. :warning:

To run it, start python shell

.. code:: console

    >>> from SECEdgar.filings import Filing()
    >>> my_filings = Filing(cik='0000320193', filing_type='10q', count=15) # 10-Q filings for Apple (NYSE: AAPL)
    >>> my_filings.save('~/path/to/dir') # Saves last 15 10Q reports from AAPL to ~/path/to/dir

This will download the past 15 10-Q filings made by Apple.

Supported Methods
-----------------

Currently this crawler supports 6 filings. Any of the following can be used in conjunction 
with the `Filing` class.

-  10-K
-  10-Q
-  8-K
-  13-F
-  4
-  SD

Documentation
--------------
To learn more about the APIs and latest changes in the project, read the [official documentation](https://www.rudrakos.com/sec-edgar/).

License
-------

Copyright © 2019 Rahul Ranjan
See LICENSE for details

.. |Build Status| image:: https://travis-ci.com/coyo8/sec-edgar.svg?branch=master
   :target: https://travis-ci.com/coyo8/sec-edgar
