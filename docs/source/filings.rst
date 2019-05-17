.. _filings:

Filings
=======

Filings can be downloaded using the classes found in the ``SECEdgar.filings`` module. 
These classes inherit from the :class:`SECEdgar.base._FilingBase` class which inherits from the 
:class:`SECEdgar.base._EDGARBase` class. These classes provide relevant ``**kwargs`` 
that are relevant to making requests and the number of filings to fetch.

Currently, the following filings can be accessed through the ``SECEdgar.filings`` module:

* :class:`SECEdgar.filings.Filing10Q`
* :class:`SECEdgar.filings.Filing10K`
* :class:`SECEdgar.filings.Filing8K`
* :class:`SECEdgar.filings.Filing13F`
* :class:`SECEdgar.filings.Filing4`
* :class:`SECEdgar.filings.FilingSD`

Base Classes
------------

.. autoclass:: SECEdgar.base._EDGARBase

.. autoclass:: SECEdgar.base._FilingBase

Available Filings
-----------------

.. autoclass:: SECEdgar.filings.Filing10Q

.. autoclass:: SECEdgar.filings.Filing10K

.. autoclass:: SECEdgar.filings.Filing8K

.. autoclass:: SECEdgar.filings.Filing13F

.. autoclass:: SECEdgar.filings.Filing4

.. autoclass:: SECEdgar.filings.FilingSD