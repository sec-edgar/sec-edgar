.. _cikmap:

Finding Company CIKs
====================

The ``secedgar.utils.get_cik_map`` function is provided as a utility to easily
fetch CIKs based on a company's ticker or name.

.. autofunction:: secedgar.utils.get_cik_map

By default, ``get_cik_map`` fetches a dictionary using company tickers as keys.

.. ipython:: python

   from secedgar.utils import get_cik_map
   print(get_cik_map())

To get a dictionary with the company names as the keys, use ``key="title"``.

.. ipython:: python

   from secedgar.utils import get_cik_map
   print(get_cik_map(key="title"))