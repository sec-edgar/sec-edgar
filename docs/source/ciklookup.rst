.. _ciklookup:

CIK Lookup
==========
The ``CIKLookup`` class allows users to get company filings using company tickers and/or company names. For example,
the code below fetches the past 15 10Q reports for the tickers AAPL, MSFT, and FB (Apple, Microsoft, and Facebook).

.. ipython:: python

   from secedgar.filings import Filing, FilingType, CIKLookup
   lookup = CIKLookup(['aapl', 'msft', 'fb'])
   my_filings = Filing(cik_lookup=lookup, filing_type=FilingType.FILING_10Q, count=15)

The ``CIKLookup`` class can also look for CIK values by using the company name.

.. ipython:: python

   from secedgar.filings import Filing, FilingType, CIKLookup
   lookup = CIKLookup(['Apple Inc.', 'Microsoft Corp', 'Facebook'])
   my_filings = Filing(cik_lookup=lookup, filing_type=FilingType.FILING_10Q, count=15)

A mix of tickers and company names is also allowed.

.. ipython:: python

   from secedgar.filings import Filing, FilingType, CIKLookup
   lookup = CIKLookup(['aapl', 'msft', 'Facebook'])
   my_filings = Filing(cik_lookup=lookup, filing_type=FilingType.FILING_10Q, count=15)

.. autoclass:: secedgar.filings.CIKLookup