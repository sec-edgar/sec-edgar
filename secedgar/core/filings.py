from datetime import date, timedelta

from secedgar.core.combo import ComboFilings
from secedgar.core.company import CompanyFilings
from secedgar.core.daily import DailyFilings
from secedgar.core.filing_types import FilingType
from secedgar.core.quarterly import QuarterlyFilings
from secedgar.exceptions import FilingTypeError
from secedgar.utils import add_quarter, get_month, get_quarter


def filings(
    cik_lookup=None,
    filing_type=None,
    user_agent=None,
    start_date=None,
    end_date=date.today(),
    count=None,
    client=None,
    entry_filter=lambda _: True,
    **kwargs
):
    """Utility method to get best filing object.

    Args:
        cik_lookup (str): Central Index Key (CIK) for company of interest.
        start_date (datetime.date, optional): Date of daily filing to fetch.
        end_date (datetime.date, optional): Date of daily filing to fetch.
        filing_type (secedgar.core.filing_types.FilingType, optional): Valid filing type
            enum. Defaults to None. If None, then all filing types for CIKs will be returned.
        count (int, optional): Number of filings to fetch. Will fetch up to `count` if that
        many filings are available. Defaults to all filings available.
        client (secedgar.client.NetworkClient, optional): Client to use. Defaults to
                    ``secedgar.client.NetworkClient`` if None given.
        entry_filter (function, optional): A boolean function to determine
            if the FilingEntry should be kept. Defaults to ``lambda _: True``.
            See :class:`secedgar.core.DailyFilings` for more detail.
        kwargs: Any keyword arguments to pass to ``NetworkClient`` if no client is specified.

    Examples:
        Using the ``filings`` function from secedgar is the easiest way to retrieve filings.

        Depending on the arguments given, secedgar will return an object that will get you
        the information you want from EDGAR.

        There are 4 main classes which can be returned.

            - :class:`secedgar.ComboFilings` for fetching filings over multiple days
              that does not fall exactly into a quarter
            - :class:`secedgar.CompanyFilings` for fetching a particular
              filing type for one or more companies
            - :class:`secedgar.DailyFilings` for fetching all filings
              from a specific date
            - :class:`secedgar.QuarterlyFilings` for fetching all filings
              from a specific quarter

        To get all filings over a time span, you could use something like below.

        .. code-block:: python

            from datetime import date
            from secedgar import filings, FilingType

            # secedgar creates correct filing object for given arguments
            # this will fetch the first 50 filings found over the time span
            my_filings = filings(start_date=date(2020, 12, 10),
                                 end_date=date(2020, 12, 15),
                                 filing_type=FilingType.FILING_4,
                                 user_agent="Name (email)",
                                 count=50)

            # easy access to methods shared across all 4 different filing classes
            my_filings_urls = my_filings.get_urls()
            my_filings.save("/path/to/directory")

        To get a single filing type for one or more companies, you could use this:

        .. code-block:: python

            from secedgar import filings, FilingType

            # similar to above, but fetches filings for specific tickers
            company_filings = filings(cik_lookup=["aapl", "fb"],
                                      filing_type=sec.FilingType.FILING_10Q,
                                      user_agent="Name (email)")
            company_filings_urls = company_filings.get_urls()
            company_filings.save("/path/to/directory")

        To get filings for a single day, you could use something like this:

        .. code-block:: python

            from datetime import date
            from secedgar import filings

            # all filings for
            daily_filings = filings(start_date=date(2020, 1 ,3),
                                    end_date=date(2020, 1, 3),
                                    user_agent="Name (email)")
            daily_filings.save("/path/to/directory")

            # limit which quarterly filings to use - saves only form 4 filings
            limit_to_form4 = lambda f: f.form_type.lower() == "4"
            daily_filings_limited = filings(start_date=date(2020, 1 ,3),
                                            end_date=date(2020, 1, 3),
                                            user_agent="Name (email)",
                                            entry_filter=limit_to_form4)
            daily_filings_limited.save("/path/to/other/directory")


        For getting filings from a specific quarter, the function call would look like this:


        .. code-block:: python

            from datetime import date
            from secedgar import filings

            # all quarterly filings
            quarterly_filings = filings(start_date=date(2020, 1 ,1),
                                        end_date=date(2020, 3, 31),
                                        user_agent="Name (email)")
            quarterly_filings.save("/path/to/directory")

            # limit which quarterly filings to use
            # saves only 10-K and 10-Q filings from quarter
            limit_to_10k_10q = lambda f: f.form_type.lower() in ("10-k", "10-q")
            quarterly_filings_limited = filings(start_date=date(2020, 1 ,1),
                                                end_date=date(2020, 3, 31),
                                                user_agent="Name (email)",
                                                entry_filter=limit_to_10k_10q)
            quarterly_filings_limited.save("/path/to/other/directory")

    """
    if filing_type is not None and not isinstance(filing_type, FilingType):
        raise FilingTypeError

    if cik_lookup:
        return CompanyFilings(
            cik_lookup,
            filing_type=filing_type,
            user_agent=user_agent,
            start_date=start_date,
            end_date=end_date,
            count=count,
            client=client,
            **kwargs
        )
    # Define entry filter as original
    _entry_filter = entry_filter

    if filing_type is not None:
        # If filing type also given, add filing types to existing entry filter
        def _entry_filter(x):
            return x.form_type == filing_type and entry_filter(x)

    if count is not None:
        raise NotImplementedError(
            "Count has not yet been implemented for Daily, quarterly & Combo Filings."
        )

    if (end_date is None or end_date == start_date) and isinstance(
            start_date, date):
        return DailyFilings(date=start_date,
                            user_agent=user_agent,
                            client=client,
                            entry_filter=_entry_filter,
                            **kwargs)

    if isinstance(start_date, date) and isinstance(end_date, date):
        current_quarter = get_quarter(start_date)
        current_year = start_date.year
        start_quarter_date = date(current_year, get_month(current_quarter), 1)
        next_year, next_quarter = add_quarter(current_year, current_quarter)
        end_quarter_date = date(next_year, get_month(next_quarter),
                                1) - timedelta(days=1)
        if start_quarter_date == start_date and end_date == end_quarter_date:
            return QuarterlyFilings(year=current_year,
                                    quarter=current_quarter,
                                    client=client,
                                    user_agent=user_agent,
                                    entry_filter=_entry_filter,
                                    **kwargs)
        return ComboFilings(start_date=start_date,
                            end_date=end_date,
                            user_agent=user_agent,
                            client=client,
                            entry_filter=_entry_filter,
                            **kwargs)

    raise ValueError(
        """Invalid arguments. You must provide 'cik_lookup' OR 'start_date' \
OR ('start_date' and 'end_date').""")
