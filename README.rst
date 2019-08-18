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


⚠️ The following code is experimental in v0.1.5. Please refer to docs on how to use the `SecCrawler` class if installing v0.1.4 or earlier. ⚠️

To run it, start python shell

.. code:: console

    >>> from SECEdgar.filings import Filing()
    >>> my_filings = Filing(cik='0000320193', filing_type='10-q', count=15) # 10-Q filings for Apple (NYSE: AAPL)
    >>> my_filings.save('~/path/to/dir') # Saves last 15 10Q reports from AAPL to ~/path/to/dir

This will download the past 15 10-Q filings made by Apple.

Supported Methods
-----------------

Currently this crawler supports the filings listed below. Any of the following can be used in conjunction 
with the `Filing` class. Suggestions for supporting other filings (using the issues tab) is always welcome.

-  **10-K**: Annual reports of company standing, includes financials
-  **10-Q**: Quarterly reports of company standing, includes financials
-  **8-K**: Timely reports of information that may be important for shareholders or potential investors
-  **13-F**: Institutional investor disclosure of holdings (for institutions with over $100 million under management)
-  **4**: Statement of change in beneficial ownership
-  **SD**: Special disclosures required by the Dodd-Frank Wall Street Reform and Consumer Protection Act relating to conflict minerals contained in products that reporting companies manufacture or contract to be manufactured and necessary to the functionality or production of those products
-  **DEF 14A**: Definitive proxy statement. Required ahead of annual meeting when firm is soliciting shareholder votes.
-  **DEFA 14A**: Additional materials to DEF 14A.

Documentation
--------------
To learn more about the APIs and latest changes in the project, read the `official documentation <https://www.rudrakos.com/sec-edgar/>`_.

License
-------

Copyright © 2019 Rahul Ranjan

See LICENSE for details

.. |Build Status| image:: https://travis-ci.com/coyo8/sec-edgar.svg?branch=master
   :target: https://travis-ci.com/coyo8/sec-edgar
