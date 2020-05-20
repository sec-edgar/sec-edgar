.. _filings:

Filings
=======

Filings can be downloaded using :class:`secedgar.filings.Filing`.

Supported filing types can be found at :ref:`filingtypes`

.. autoclass:: secedgar.filings.Filing

Examples
--------

Restrict the start and end dates by using the `start_date` and `end_date` arguments.

.. code-block:: python

   from secedgar.filings import FilingType, Filing
   from datetime import datetime

   filing = Filing(cik_lookup='aapl',
                   filing_type=FilingType.FILING_10K,
                   start_date=datetime(2015, 1, 1),
                   end_date=datetime(2019, 1, 1))

If you would like to find all filings from some `start_date` until today, simply exclude `end_date`.
The end date defaults to today's date.

.. code-block:: python

   from secedgar.filings import FilingType, Filing
   from datetime import datetime

   filing = Filing(cik_lookup='aapl',
                   filing_type=FilingType.FILING_10K,
                   start_date=datetime(2015, 1, 1)) # end date defaults to today

You can also look up a specific filing type for multiple companies.

.. code-block:: python

   from secedgar.filings import FilingType, Filing
   from datetime import datetime

   filing = Filing(cik_lookup=['aapl', 'msft', 'fb'],
                   filing_type=FilingType.FILING_10K,
                   start_date=datetime(2015, 1, 1))

*For a full list of the available filing types, please see* :class:`secedgar.filings.FilingType`.