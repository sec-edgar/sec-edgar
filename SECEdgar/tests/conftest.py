import pytest  # noqa: F401
from SECEdgar.crawler import SecCrawler
from SECEdgar.filings import Filing, FilingType

aapl_cik = "0000320193"


@pytest.fixture(scope="session")
def valid_make_dir_args():
    return {"company_code": "AAPL", "cik": aapl_cik,
            "priorto": "20010101", "filing_type": "10-Q"}


@pytest.fixture(scope="session")
def valid_filing_data():
    return {"company_code": "AAPL", "cik": aapl_cik,
            "priorto": "20010101", "count": 1}


@pytest.fixture(scope="session")
def valid_fetch_report_args(valid_make_dir_args, tmpdir_factory):
    return {"company_code": "AAPL", "cik": aapl_cik,
            "priorto": "20010101", "filing_type": "10-Q", "count": 1}


@pytest.fixture(scope="class", autouse=True)
def crawler():
    _crawler = SecCrawler()
    yield _crawler


@pytest.fixture(scope="class")
def valid_filing_10k():
    return Filing(aapl_cik, FilingType.FILING_10K, count=3)


@pytest.fixture(scope="class")
def valid_filing_10q():
    return Filing(aapl_cik, FilingType.FILING_10Q, count=3)


@pytest.fixture(scope="class")
def valid_filing_8k():
    return Filing(aapl_cik, FilingType.FILING_8K, count=3)


@pytest.fixture(scope="class")
def valid_filing_13f():
    return Filing(aapl_cik, FilingType.FILING_13F, count=3)


@pytest.fixture(scope="class")
def valid_companies():
    return {'aapl': '0000320193',
            'msft': '0000789019',
            'amzn': '0001018724',
            'fb': '0001326801'}
