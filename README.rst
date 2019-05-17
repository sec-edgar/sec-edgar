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

To run it, start python shell

.. code:: console

    >>> from SECEdgar.filings import Filing10Q
    >>> my_filings = Filing10Q('0000320193', count=15) # 0000320193 is CIK for Apple (NYSE: AAPL)
    >>> my_filings.save('~/path/to/dir') # Saves last 15 10Q reports from AAPL to ~/path/to/dir

This will download the past 15 10-Q filings made by Apple.

Supported Methods
-----------------

Currently this crawler supports 6 filings. Each has its own class of the form 
``Filing*`` (replace * with filing name and remove any hyphens).

-  10-K
-  10-Q
-  8-K
-  13-F
-  4
-  SD

License
-------

Copyright © 2019 Rahul Ranjan
See LICENSE for details

.. |Build Status| image:: https://travis-ci.com/coyo8/sec-edgar.svg?branch=master
   :target: https://travis-ci.com/coyo8/sec-edgar