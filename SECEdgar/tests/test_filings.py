# Tests if filings are correctly received from EDGAR
import pytest
import datetime
import requests
from SECEdgar.utils.exceptions import FilingTypeError, CIKError
from SECEdgar.filings import Filing, FilingType


class TestLegacySecCrawler(object):
    def test_10q_requires_args(self, crawler):
        with pytest.raises(TypeError):
            return crawler.filing_10Q()

    def test_10k_requires_args(self, crawler):
        with pytest.raises(TypeError):
            return crawler.filing_10K()

    def test_sd_requires_args(self, crawler):
        with pytest.raises(TypeError):
            return crawler.filing_SD()

    def test_8k_requires_args(self, crawler):
        with pytest.raises(TypeError):
            return crawler.filing_8K()

    def test_13f_requires_args(self, crawler):
        with pytest.raises(TypeError):
            return crawler.filing_13F()

    def test_4_requires_args(self, crawler):
        with pytest.raises(TypeError):
            return crawler.filing_4()


class TestFiling(object):
    def test_count_returns_exact(self, valid_filing_10k):
        if len(valid_filing_10k.get_urls()) != valid_filing_10k.client.count:
            raise AssertionError("Count should return exact number of filings.")

    def test_date_is_sanitized(self, valid_filing_10k):
        date = datetime.datetime(2015, 1, 1)
        valid_filing_10k.dateb = date
        if not valid_filing_10k.dateb == '20150101':
            raise AssertionError("The dateb param was not correctly sanitized.")

    def test_date_is_sanitized_when_changed(self, valid_filing_10k):
        valid_filing_10k.dateb = datetime.datetime(2016, 1, 1)
        if not valid_filing_10k.dateb == '20160101':
            raise AssertionError("The dateb param was not correctly sanitized after change.")

    def test_txt_urls(self, valid_filing_10k):
        r = requests.get(valid_filing_10k.get_urls()[0])
        if not r.text:
            raise AssertionError("Text file returned as empty.")

    def test_invalid_filing_type_enum(self):
        with pytest.raises(AttributeError):
            Filing(cik='0000320193', filing_type=FilingType.INVALID)

    def test_invalid_filing_type_types(self):
        for t in ('10j', '10-k', 'ssd', 'invalid', 1):
            with pytest.raises(FilingTypeError):
                Filing(cik='0000320193', filing_type=t)

    def test_validate_cik(self):
        with pytest.raises(CIKError):
            Filing(cik='0notvalid0', filing_type=FilingType.FILING_10K)
        with pytest.raises(CIKError):
            Filing(cik='012345678910', filing_type=FilingType.FILING_10K)
        with pytest.raises(CIKError):
            Filing(cik=1234567891011, filing_type=FilingType.FILING_10K)
        with pytest.raises(ValueError):
            Filing(cik=123.0, filing_type=FilingType.FILING_10K)
