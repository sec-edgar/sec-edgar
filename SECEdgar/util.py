import datetime

def _sanitize_date(date):
    if isinstance(date, datetime.datetime):
        return date.strftime("%Y%m%d")
    elif isinstance(date, str):
        if len(date) != 8:
            raise TypeError('Date must be of the form YYYYMMDD')
    elif isinstance(date, int):
        if date < 10**7 or date > 10**8:
            raise TypeError('Date must be of the form YYYYMMDD')