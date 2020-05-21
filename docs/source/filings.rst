.. _filings:

Filings
=======

There are currently two supported ways to fetch filings. If you
are interested in grabbing specific types of filings for a specific set of companies,
it is suggested that you use :class:`secedgar.filings.Filing`. If you are interested in
fetching all filings from any given day, you should use :class:`secedgar.filings.DailyFilings`.

Filings can be downloaded using :class:`secedgar.filings.Filing`.

Supported filing types can be found at :ref:`filingtypes`

Filing
------

.. autoclass:: secedgar.filings.Filing

Filing Examples
---------------

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

Daily Filings
-------------

.. autoclass:: secedgar.filings.DailyFilings

Daily Filings Examples
----------------------

If you wanted to download all filings from January 2, 2020, you could use the following code.
Note that you should replace ``'/my_directory'`` with the desired directory of the filings.

.. code-block:: python

   from secedgar.filings import DailyFilings
   from datetime import datetime

   daily_filings = DailyFilings(date=datetime(2020, 1, 2))
   daily_filings.save('/my_directory')


