import pytest
from SECEdgar.crawler import SecCrawler


@pytest.fixture(scope='module')
def crawler():
    obj = SecCrawler()
    return obj
