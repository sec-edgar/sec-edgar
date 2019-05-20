.. _filings:

Filings
=======

Filings can be downloaded using the :class:`SECEdgar.base.Filing` class found in the ``SECEdgar.filings`` module. 
These classes inherit from the :class:`SECEdgar.base._EDGARBase` class. This class provides relevant ``**kwargs`` 
for making requests and the number of filings to fetch.

Base Class
----------

.. autoclass:: SECEdgar.base._EDGARBase

Filings
-------

.. note::
    SECEdgar tries to be flexible when interpreting what filing type 
    you want. Filing types of the form Number-Letter such as 10-K can 
    either be expressed as "10-k" or "10k" (case-insensitive).


.. autoclass:: SECEdgar.filings.Filing