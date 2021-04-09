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
   :inherited-members:
   :members:


Examples
^^^^^^^^

Restrict the start and end dates by using the ``start_date`` and ``end_date`` arguments.

.. code-block:: python

   from secedgar.filings import FilingType, Filing
   from datetime import datetime

   filing = Filing(cik_lookup='aapl',
                   filing_type=FilingType.FILING_10K,
                   start_date=datetime(2015, 1, 1),
                   end_date=datetime(2019, 1, 1))

If you would like to find all filings from some ``start_date`` until today, simply exclude ``end_date``.
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


SEC requests that traffic identifies itself via a user agent string. You can
customize this according to your preference using the ``user_agent`` argument.

.. code-block:: python

   from secedgar.filings import FilingType, Filing
   from datetime import datetime

   filing = Filing(cik_lookup=['aapl', 'msft', 'fb'],
                   filing_type=FilingType.FILING_10K,
                   start_date=datetime(2015, 1, 1),
                   user_agent='YOUR COMPANY NAME HERE')


Daily Filings
-------------

The ``DailyFilings`` class can be used to fetch all the URLs for or download all filings from any given day.

.. autoclass:: secedgar.filings.DailyFilings
   :inherited-members:
   :members:


Examples
^^^^^^^^

If you wanted to download all filings from January 2, 2020, you could use the following code.
Note that you should replace ``'/my_directory'`` with the desired directory of the filings.

.. code-block:: python

   from secedgar.filings import DailyFilings
   from datetime import datetime

   daily_filings = DailyFilings(date=datetime(2020, 1, 2))
   daily_filings.save('/my_directory')

Master Filings (Quarterly)
--------------------------

The ``MasterFilings`` class can be used to fetch all the URLs for or download all filings from any given quarter.

.. autoclass:: secedgar.filings.MasterFilings
   :inherited-members:
   :members:


Examples
^^^^^^^^

.. code-block:: python

   from secedgar.filings import MasterFilings

   master_filings = MasterFilings(year=2000, quarter=4)
   urls = master_filings.get_urls()  # gets all URLs for filings from quarter 4 of 2000
   master_filings.save('/my_directory')  # saves all filings from quarter 4 of 2000 in my_directory

Saving Filings
--------------

In version 0.3.0, the ``dir_pattern`` and ``file_pattern`` arguments were introduced to allow for more flexible structuring of filings.

Here are some examples of how you might use those arguments to create custom directory structures

.. code-block:: python

   from secedgar.filings import Filing, FilingType

   f = Filing(cik_lookup=["aapl", "msft"], filing_type=FilingType.FILING_10Q, count=5)
   f.save("./my_directory", dir_pattern="cik_{cik}/{type}", file_pattern="{accession_number}")

The code above would create a directory structure that would look something like this:

::

   my_directory/
   ├── cik_aapl
   │   └── 10-q
   │       ├── 0000320193-19-000066.txt
   │       ├── 0000320193-19-000076.txt
   │       ├── 0000320193-20-000010.txt
   │       ├── 0000320193-20-000052.txt
   │       └── 0000320193-20-000062.txt
   └── cik_msft
      └── 10-q
         ├── 0001564590-19-012709.txt
         ├── 0001564590-19-037549.txt
         ├── 0001564590-20-002450.txt
         ├── 0001564590-20-019706.txt
         └── 0001564590-20-047996.txt


This same sort of templating can be used for :class:`secedgar.filings.DailyFilings` and :class:`secedgar.filings.MasterFilings`.
