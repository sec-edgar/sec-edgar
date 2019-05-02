import pytest
from SECEdgar.crawler import SecCrawler


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
    obj = SecCrawler()
    return obj
