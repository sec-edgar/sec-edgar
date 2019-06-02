.. _install:


Install
=======

Dependencies
------------

SECEdgar relies on:

-  `beautifulsoup4 <https://www.crummy.com/software/BeautifulSoup/bs4/doc/>`__
-  `requests <http://docs.python-requests.org>`__

Installation
------------

Latest stable release via pip (recommended):

.. code:: bash

    $ pip install SECEdgar

Latest development version:

.. code:: bash

    $ pip install git+https://github.com/coyo8/SECEdgar.git

or

.. code:: bash

     $ git clone https://github.com/coyo8/SECEdgar.git
     $ cd SECEdgar
     $ pip install .

**Note:**

The use of
`virtualenv <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`__
is recommended as below:

.. code:: bash

    $ pip install virtualenv
    $ virtualenv env
    $ source env/bin/activate