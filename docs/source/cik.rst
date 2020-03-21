.. _cik:

CIK
===
The CIK class allows users to get company filings using company tickers and/or company names. For example,
the code below fetches the past 15 10Q reports for the tickers AAPL, MSFT, and FB (Apple, Microsoft, and Facebook).

.. ipython:: python

   from secedgar.filings import Filing, FilingType, CIK
   my_ciks = CIK(['aapl', 'msft', 'fb'])
   my_filings = Filing(cik=my_ciks, filing_type=FilingType.FILING_10Q, count=15)

The CIK class can also look for CIK values by using the company name.

.. ipython:: python

   from secedgar.filings import Filing, FilingType, CIK
   my_ciks = CIK(['Apple Inc.', 'Microsoft Corp', 'Facebook'])
   my_filings = Filing(cik=my_ciks, filing_type=FilingType.FILING_10Q, count=15)

A mix of tickers and company names is also allowed.

.. ipython:: python

   from secedgar.filings import Filing, FilingType, CIK
   my_ciks = CIK(['aapl', 'msft', 'Facebook'])
   my_filings = Filing(cik=my_ciks, filing_type=FilingType.FILING_10Q, count=15)

.. autoclass:: secedgar.filings.CIK