import json
import requests

URL = "https://www.sec.gov/files/company_tickers.json"


def get_cik_map(key="ticker"):
    """Get dictionary of tickers to CIK numbers.

    Args:
        key (str): Should be either "ticker" or "title". Choosing "ticker"
            will give dict with tickers as keys. Choosing "title" will use
            company name as keys.

    Returns:
        Dictionary with either ticker or company name as keys, depending on
        ``key`` argument, and corresponding CIK as values.

    .. versionadded:: 0.1.6
    """
    response = requests.get(URL)
    json_response = json.loads(response.text)
    return {v[key]: str(v["cik_str"]) for v in json_response.values()}
