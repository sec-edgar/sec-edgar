.. _crawler:

Crawler
=======

.. warning::
    The ``SecCrawler`` class will be deprecated in v0.2.0 in favor of the 
    newly released ``Filing`` class (found in ``secedgar.filing``).
    To learn more about the ``Filing`` class, please see :ref:`filings <filings>`.

The ``secedgar`` module is largely centered around the ``SecCrawler`` class.
This class fetches the filing information.

.. autoclass:: secedgar.crawler.SecCrawler

The crawler has many different methods to fetch different filings from the Edgar 
database. Each method will create new documents in the specified data path.

.. automethod:: secedgar.crawler.SecCrawler.filing_10Q

.. automethod:: secedgar.crawler.SecCrawler.filing_10K

.. automethod:: secedgar.crawler.SecCrawler.filing_8K

.. automethod:: secedgar.crawler.SecCrawler.filing_13F

.. automethod:: secedgar.crawler.SecCrawler.filing_SD

.. automethod:: secedgar.crawler.SecCrawler.filing_4
