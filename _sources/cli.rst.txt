.. _cli:

Command Line Interface
======================

The secedgar project also provides an easy to use command line interface.
This helps to easily download filings from EDGAR without writing any code.

In order to use the CLI, make sure you have click installed as a dependency.
When installing from PyPi, you can ``pip install secedgar[cli]``.

.. click:: secedgar.cli:cli
   :prog: secedgar
   :show-nested: