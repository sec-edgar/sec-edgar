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
        client (secedgar.client._base, optional): Client to use. Defaults to
                    ``secedgar.client.NetworkClient`` if None given.
        entry_filter (function, optional): A boolean function to determine
            if the FilingEntry should be kept. Defaults to ``lambda _: True``.
            See :class:`secedgar.core.DailyFilings` for more detail.
        kwargs: Any keyword arguments to pass to ``NetworkClient`` if no client is specified.

    Examples:
        .. code-block:: python

            from datetime import date
            from secedgar.core import filings, FilingType

            engine = filings(start_date=date(2020, 12, 10), end_date=date(2020, 12, 10),
                filing_type=FilingType.FILING_4, count=50)
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
