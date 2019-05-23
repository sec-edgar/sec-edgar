import datetime


def _sanitize_date(date):
    """Sanitizes date to be in acceptable format for EDGAR.

    Args:
        date (Union[datetime.datetime, str]): Date to be sanitized for request.

    Returns:
        date (str): Properly formatted date in 'YYYYMMDD' format.
    """
    if isinstance(date, datetime.datetime):
        return date.strftime("%Y%m%d")
    elif isinstance(date, str):
        if len(date) != 8:
            raise TypeError('Date must be of the form YYYYMMDD')
    elif isinstance(date, int):
        if date < 10**7 or date > 10**8:
            raise TypeError('Date must be of the form YYYYMMDD')
    return date
