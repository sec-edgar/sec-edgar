import json
import requests


def get_cik_map():
    """Get map of tickers to CIK numbers."""
    url = "https://www.sec.gov/files/company_tickers.json"
    response = requests.get(url).json()
    return {v["ticker"]: str(v["cik_str"]) for _, v in response.items()}
