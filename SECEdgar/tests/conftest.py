import pytest
from SECEdgar.crawler import SecCrawler
from SECEdgar.filings import Filings


@pytest.fixture(scope='module')
def valid_make_dir_args():
    return {'company_code': 'AAPL', 'cik': '0000320193',
            'priorto': '20010101', 'filing_type': '10-Q'}


@pytest.fixture(scope='module')
def valid_filing_data():
    return {'company_code': 'AAPL', 'cik': '0000320193',
            'priorto': '20010101', 'count': 1}


@pytest.fixture(scope='module')
def valid_fetch_report_args(valid_make_dir_args):
    return {'company_code': 'AAPL', 'cik': '0000320193',
            'priorto': '20010101', 'filing_type': '10-Q', 'count': 1}


@pytest.fixture(scope='module')
def crawler():
    return SecCrawler()


@pytest.fixture(scope='class')
def filing():
    return Filings('0000320193', "10q", count=3)
