# Tests if filings are correctly received from EDGAR
import pytest
import datetime
import requests
from SECEdgar.utils.exceptions import FilingTypeError
from SECEdgar.filings import Filings


def test_10Q_requires_args(crawler):
    with pytest.raises(TypeError):
        return crawler.filing_10Q()


def test_10K_requires_args(crawler):
    with pytest.raises(TypeError):
        return crawler.filing_10K()


def test_SD_requires_args(crawler):
    with pytest.raises(TypeError):
        return crawler.filing_SD()


def test_8K_requires_args(crawler):
    with pytest.raises(TypeError):
        return crawler.filing_8K()


def test_13F_requires_args(crawler):
    with pytest.raises(TypeError):
        return crawler.filing_13F()


def test_4_requires_args(crawler):
    with pytest.raises(TypeError):
        return crawler.filing_4()


class TestFilings(object):
    def test_count_returns_exact(self, filing):
        if not len(filing._get_urls()) == 3:
            raise AssertionError("Count should return exact number of filings.")

    def test_date_is_sanitized(self, filing):
        date = datetime.datetime(2015, 1, 1)
        filing.dateb = date
        if not filing.dateb == '20150101':
            raise AssertionError("The dateb param was not correctly sanitized.")

    def test_txt_urls(self, filing):
        r = requests.get(filing._get_urls()[0])
        print(r.text)
        if not r.text:
            raise AssertionError("Text file returned as empty.")

    def test_valid_filing_types(self):
        with pytest.raises(FilingTypeError):
            Filings(cik='0000320193', filing_type='10j')
            Filings(cik='0000320193', filing_type='10--k')
            Filings(cik='0000320193', filing_type='ssd')
