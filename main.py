import logging
from secedgar import filings, FilingType

ACCOUNTING_FILING_TYPES = [
    FilingType.FILING_10K,
    FilingType.FILING_CORRESP
]

with open("tickers.txt", "r") as tickers:
    for ticker in tickers:
        for filing_type in ACCOUNTING_FILING_TYPES:
            ticker = ticker.strip()
            filings(
                cik_lookup=ticker,
                filing_type=filing_type,
                user_agent="James Wang james@accrual.ai",
            ).save("/")
