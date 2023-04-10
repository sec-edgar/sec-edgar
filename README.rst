
Running
-------


```bash
# For macOS, refer to weasyprint installation docs for different platforms
brew install weasyprint
pip install -r requirements.txt

export SUPABASE_URL=...
export SUPABASE_KEY=...
python main.py
```

Edit the list in `tickers.txt` to upload 10-Ks for different companies. If a ticker is already present in the supabase bucket,
the crawler will skip it.

Company Filings
~~~~~~~~~~~~~~~

Single Company
^^^^^^^^^^^^^^

.. code:: python

    from secedgar import filings, FilingType

    # 10Q filings for Apple (ticker "aapl")
    my_filings = filings(cik_lookup="aapl",
                         filing_type=FilingType.FILING_10Q,
                         user_agent="Your name (your email)")
    my_filings.save('/path/to/dir')


Multiple Companies
^^^^^^^^^^^^^^^^^^

.. code:: python

    from secedgar import filings, FilingType

    # 10Q filings for Apple and Facebook (tickers "aapl" and "fb")
    my_filings = filings(cik_lookup=["aapl", "fb"],
                         filing_type=FilingType.FILING_10Q,
                         user_agent="Your name (your email)")
    my_filings.save('/path/to/dir')


Supported Methods
-----------------

Currently this crawler supports many different filing types. To see the full list, please refer to the docs. If you don't see a filing type you would like
to be supported, please create an issue on GitHub.

Original Documentation
--------------
To learn more about the APIs and latest changes in the project, read the `official documentation <https://sec-edgar.github.io/sec-edgar>`_.
