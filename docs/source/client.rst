.. _client:

Using Network Client
====================

The :class:`secedgar.client.NetworkClient` class is used to interact with the SEC's website.
This class aims to provide all utilities needed to make requesting data from the SEC as easily
as possible.

.. note::
   By default, ``secedgar`` will use ``NetworkClient``. Modifying ``NetworkClient`` is not
   necessary unless you need further control over how you would like to interact with the
   SEC's website.


.. autoclass:: secedgar.client.NetworkClient
   :members: