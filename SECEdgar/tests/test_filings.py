# Tests if filings are correctly received from EDGAR
import pytest
from SECEdgar.filings import Filing10Q
import datetime
import requests


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
    def test_count_returns_exact(self, filing_10Q):
        if not len(filing_10Q._get_urls()) == 3:
            raise AssertionError("Count should return exact number of filings.")

    def test_date_is_sanitized(self, filing_10Q):
        date = datetime.datetime(2015, 1, 1)
        filing_10Q.dateb = date
        if not filing_10Q.dateb == '20150101':
            raise AssertionError("The dateb param was not correctly sanitized.")

    def test_txt_urls(self, filing_10Q):
        r = requests.get(filing_10Q._get_urls()[0])
        print(r.text)
        if not r.text:
            raise AssertionError("Text file returned as empty.")

    def test_filing_type_immutable(self, filing_10Q):
        """The filing_type property should be immutable. """
        with pytest.raises(AttributeError):
            filing_10Q.filing_type = "10-K"
