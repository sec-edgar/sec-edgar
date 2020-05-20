import requests

URL = "https://www.sec.gov/files/company_tickers.json"


def get_cik_map():
    """Get map of tickers to CIK numbers."""
    response = requests.get(URL).json()
    return {v["ticker"]: str(v["cik_str"]) for _, v in response.items()}


def get_company_name_map():
    response = requests.get(URL).json()
    return {v["title"]: str(v["cik_str"]) for _, v in response.items()}
