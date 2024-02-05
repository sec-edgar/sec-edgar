.. _cikmap:

Finding Company CIKs
====================

The ``secedgar.cik_lookup.get_cik_map`` function is provided as a utility to easily
fetch CIKs based on a company's ticker or name.

.. autofunction:: secedgar.cik_lookup.get_cik_map

By default, ``get_cik_map`` fetches a dictionary using company tickers as keys.

.. note::

   In both examples below, only the first 5 results are shown.

.. ipython:: python

   from secedgar.cik_lookup import get_cik_map
   dict(list(get_cik_map(user_agent="Example (email@example.com)")["ticker"].items())[:5])

To get a dictionary with the company names as the keys, use the "title" key.

.. ipython:: python

   from secedgar.cik_lookup import get_cik_map
   dict(list(get_cik_map(user_agent="Example (email@example.com)")["title"].items())[:5])