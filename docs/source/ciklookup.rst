.. _ciklookup:

CIK Lookup
==========
The ``CIKLookup`` class allows users to get company filings using company tickers and/or company names.

.. note::
   By default, the ``Filing`` class wraps any given string or an iterable with string objects (e.g. a list of strings or a tuple
   of strings). You will probably not need to use this class. However, it can be useful if you wish to save the CIKs for lookup terms.

Below is an example of how you can retrieve lookup CIKs by using the ``CIKLookup`` class.

.. ipython:: python

   from secedgar.filings.cik_lookup import CIKLookup
   lookups = CIKLookup(['aapl', 'msft', 'Facebook'])
   lookups.lookup_dict