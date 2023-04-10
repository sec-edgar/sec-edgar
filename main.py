import logging
from secedgar import filings, FilingType

with open("tickers.txt", "r") as tickers:
    for ticker in tickers:
        ticker = ticker.strip()
        filings(
            cik_lookup=ticker,
            filing_type=FilingType.FILING_10K,
            user_agent="James Wang james@accrual.ai",
        ).save("/")
