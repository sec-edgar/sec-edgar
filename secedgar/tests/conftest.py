import pytest

from secedgar.crawler import SecCrawler

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


@pytest.fixture(scope="session")
def tmp_data_directory(tmpdir_factory):
    return str(tmpdir_factory.mktemp("tmp_data"))
