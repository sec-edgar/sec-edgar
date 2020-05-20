.. _usage:


Common Usage Examples
=====================

secedgar provides a simple way to download multiple filings from the
`SEC Edgar database <https://www.sec.gov/edgar/searchedgar/companysearch.html>`__.

This package is useful for obtaining important financial information about public companies such as

- Financials
- Business Profile
- Letter to Shareholders
- Management's Analysis

The ``Filing`` class provides a simple API to fetch SEC filings.

.. code-block:: python

   from secedgar.filings import Filing, FilingType

   my_filings = Filing(cik_lookup='aapl',
                       filing_type=FilingType.FILING_10Q,
                       count=15)

The ``cik_lookup`` argument can also take multiple tickers and/or company names.

.. code-block:: python

   from secedgar.filings import Filing, FilingType

   my_filings = Filing(cik_lookup=['aapl', 'msft', 'Facebook'],
                       filing_type=FilingType.FILING_10Q,
                       count=15)


In order to save all fetched filings to a specific directory, use the ``save`` method.

.. code-block:: python

   my_filings.save('~/tempdir')
