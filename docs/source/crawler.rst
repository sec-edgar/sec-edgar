.. _crawler:

Crawler
=======

.. warning::
    The ``SecCrawler`` class will be deprecated in v0.2.0 in favor of the 
    newly released filing classes (found in ``SECEdgar.filings``). 
    See the complete list :doc:`here <filings.rst>`.

The ``SECEdgar`` module is largely centered around the ``SecCrawler`` class.
This class fetches the filing information.

.. autoclass:: SECEdgar.crawler.SecCrawler

The crawler has many different methods to fetch different filings from the Edgar 
database. Each method will create new documents in the specified data path.

.. automethod:: SECEdgar.crawler.SecCrawler.filing_10Q

.. automethod:: SECEdgar.crawler.SecCrawler.filing_10K

.. automethod:: SECEdgar.crawler.SecCrawler.filing_8K

.. automethod:: SECEdgar.crawler.SecCrawler.filing_13F

.. automethod:: SECEdgar.crawler.SecCrawler.filing_SD

.. automethod:: SECEdgar.crawler.SecCrawler.filing_4
