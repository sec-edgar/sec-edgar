.. _filings:

Filings
=======

There are multiple ways to download filings. The most direct way is to use the :meth:`secedgar.filings`
function. This function will return a class which tries to best match your needs based on the arguments
provided. For the more technical, the :meth:`secedgar.filings` function is a factory.

If you find that this does not meet your needs for any reason or would like more direct control
over what is being created, you can use the following classes:

- :class:`secedgar.CompanyFilings` - for fetching filings for specific companies
- :class:`secedgar.DailyFilings` - for fetching filings from a specific date
- :class:`secedgar.QuarterlyFilings` - for fetching filings from a specific quarter
- :class:`secedgar.ComboFilings` - for fetching filings over a time span (most useful when spanning multiple quarters)

Supported filing types can be found at :ref:`filingtypes`

Filings Function
----------------

.. autofunction:: secedgar.filings


Filings Classes
---------------

Filing
~~~~~~

.. autoclass:: secedgar.CompanyFilings
   :members:
   :inherited-members:



Daily Filings
~~~~~~~~~~~~~

The ``DailyFilings`` class can be used to fetch all the URLs for or download all filings from any given day.

.. autoclass:: secedgar.DailyFilings
   :members:


Quarterly Filings
~~~~~~~~~~~~~~~~~

The ``QuarterlyFilings`` class can be used to fetch all the URLs for or download all filings from any given quarter.

.. autoclass:: secedgar.QuarterlyFilings
   :members:


Combo Filings
~~~~~~~~~~~~~

The ``ComboFilings`` class can download all filings from a specified time frame.
Internally, this class uses a mixture of ``DailyFilings`` and ``QuarterlyFilings`` to get all of the needed
filings.

.. autoclass:: secedgar.ComboFilings
   :members:


Saving Filings
--------------

In version 0.3.0, the ``dir_pattern`` and ``file_pattern`` arguments were introduced to allow for more flexible structuring of filings.

Here are some examples of how you might use those arguments to create custom directory structures

.. code-block:: python

   from secedgar import CompanyFilings, FilingType

   f = CompanyFilings(cik_lookup=["aapl", "msft"],
                      filing_type=FilingType.FILING_10Q,
                      count=5,
                      user_agent="Name (email)")
   f.save("./my_directory",
          dir_pattern="cik_{cik}/{type}",
          file_pattern="{accession_number}")

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


This same sort of templating can be used for :class:`secedgar.DailyFilings` and :class:`secedgar.QuarterlyFilings`.
