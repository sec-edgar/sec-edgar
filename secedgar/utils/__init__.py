import datetime
import os

# from secedgar.filings.cik_lookup import CIKLookup  # noqa: F401
# Circular Import? IDK


def sanitize_date(date):
    """Sanitizes date to be in acceptable format for EDGAR.

    Args:
        date (Union[datetime.datetime, str]): Date to be sanitized for request.

    Returns:
        date (str): Properly formatted date in 'YYYYMMDD' format.

    Raises:
        TypeError: If date is not in format YYYYMMDD as str or int.
    """
    if isinstance(date, datetime.datetime):
        return date.strftime("%Y%m%d")
    elif isinstance(date, str):
        if len(date) != 8:
            raise TypeError('Date must be of the form YYYYMMDD')
    elif isinstance(date, int):
        if date < 10 ** 7 or date > 10 ** 8:
            raise TypeError('Date must be of the form YYYYMMDD')
    return date


def make_path(path, **kwargs):
    """Make directory based on filing info.

    Args:
        path (str): Path to be made if it doesn't exist.
        **kwargs: Keyword arguments to pass to ``os.makedirs``.

    Raises:
        OSError: If there is a problem making the path.

    Returns:
        None
    """
    if not os.path.exists(path):
        os.makedirs(path, **kwargs)


def get_quarter(date):
    """Get quarter that corresponds with date.

    Args:
        date ([datetime.datetime]): Datetime object to get quarter for.
    """
    return (date.month - 1) // 3 + 1
