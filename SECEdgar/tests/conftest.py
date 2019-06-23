import pytest
from SECEdgar.crawler import SecCrawler
from SECEdgar.filings import Filing
import shutil


@pytest.fixture(scope="session")
def valid_make_dir_args():
    return {"company_code": "AAPL", "cik": "0000320193",
            "priorto": "20010101", "filing_type": "10-Q"}


@pytest.fixture(scope="session")
def valid_filing_data():
    return {"company_code": "AAPL", "cik": "0000320193",
            "priorto": "20010101", "count": 1}


@pytest.fixture(scope="session")
def valid_fetch_report_args(valid_make_dir_args, tmpdir_factory):
    return {"company_code": "AAPL", "cik": "0000320193",
            "priorto": "20010101", "filing_type": "10-Q", "count": 1}


@pytest.fixture(scope="session", autouse=True)
def crawler():
    _crawler = SecCrawler()
    yield _crawler
    shutil.rmtree(_crawler.data_path)


@pytest.fixture(scope="class")
def filing():
    return Filing("0000320193", "10-q", count=3)
