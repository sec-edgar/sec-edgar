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

   $ pip install secedgar

or

You can clone the project or download it as zip.

.. code:: bash

   $ git clone https://github.com/rahulrrixe/SEC-Edgar.git
   $ cd SEC-Edgar
   $ python setup.py install

Running
-------


⚠️ The following code is experimental in v0.1.5. Please refer to docs on how to use the `SecCrawler` class if installing v0.1.4 or earlier. ⚠️

.. code:: python

    from secedgar.filings import Filing, FilingType
    my_filings = Filing(cik='0000320193', filing_type=FilingType.FILING_10Q) # 10Q filings for AAPL
    my_filings.save('~/path/to/dir')

    my_filings = Filing(cik='0000320193', filing_type=FilingType.FILING_10Q)
    my_filings.save('~/path/to/dir')

Supported Methods
-----------------

Currently this crawler supports many different filing types. To see the full list, please refer to the docs. If you don't see a filing type you would like
to be supported, please create an issue on GitHub.

Documentation
--------------
To learn more about the APIs and latest changes in the project, read the `official documentation <https://www.rudrakos.com/sec-edgar/>`_.

License
-------

Copyright © 2020 Rahul Ranjan

See LICENSE for details

.. |Build Status| image:: https://travis-ci.com/coyo8/sec-edgar.svg?branch=master
   :target: https://travis-ci.com/coyo8/sec-edgar
