.. _rest_api:

REST API
========

The SEC recently released an API which can be used to more easily access data on companies.
For a complete overview of the API, you can
`read more here <https://www.sec.gov/edgar/sec-api-documentation>`_.


Wrapper
-------

In order to make this information even easier to extract, ``secedgar`` contains functions that
wrap around the EDGAR API to make the data even more accessible. Below are the functions available
via ``secedgar``.

.. autofunction:: secedgar.core.rest.get_submissions

.. autofunction:: secedgar.core.rest.get_company_concepts

.. autofunction:: secedgar.core.rest.get_company_facts

.. autofunction:: secedgar.core.rest.get_xbrl_frames