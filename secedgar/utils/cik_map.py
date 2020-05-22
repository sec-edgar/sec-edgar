import requests

URL = "https://www.sec.gov/files/company_tickers.json"


def get_cik_map():
    """Get dictionary of tickers to CIK numbers.

    Returns:
        Dictionary with tickers being keys and CIKs, as strings, being the values.

    .. versionadded:: 0.1.6
    """
    response = requests.get(URL).json()
    return {v["ticker"]: str(v["cik_str"]) for _, v in response.items()}


def get_company_name_map():
    """Get dictionary of tickers to CIK numbers.

    Returns:
        Dictionary with company names being keys and CIKs, as strings, being the values.

    .. versionadded:: 0.1.6
    """
    response = requests.get(URL).json()
    return {v["title"]: str(v["cik_str"]) for _, v in response.items()}
