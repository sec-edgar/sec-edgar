# Tests if filings are correctly received from EDGAR
import datetime
import pytest
import requests

from SECEdgar.client import NetworkClient
from SECEdgar.filings import Filing, FilingType, CIK

from SECEdgar.filings.cik_validator import CIKValidator
from SECEdgar.tests.utils import datapath
from SECEdgar.utils.exceptions import FilingTypeError, EDGARQueryError


class MockSingleCIKNotFound:
    def __init__(self, *args):
        self.status_code = 200
        with open(datapath("CIK", "cik_not_found.html"), 'rb') as f:
            self.text = f.read()


class MockSingleCIKFiling:
    def __init__(self, *args):
        self.status_code = 200
        with open(datapath('filings', 'aapl_10q_filings.xml')) as f:
            self.text = f.read()


class MockCIKValidatorGetCIKs:
    def __init__(self, *args):
        pass

    @staticmethod
    def get_ciks(self):
        return {'aapl': '0000320193'}


class TestFiling(object):
    @pytest.mark.slow
    def test_count_returns_exact(self, monkeypatch):
        aapl = Filing(cik='aapl', filing_type=FilingType.FILING_10Q, count=10)
        monkeypatch.setattr(CIKValidator, "get_ciks", MockCIKValidatorGetCIKs.get_ciks)
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKFiling)
        urls = aapl.get_urls()
        if len(urls) != aapl.client.count:
            raise AssertionError("""Count should return exact number of filings.
                                 Got {0}, but expected {1} URLs.""".format(
                    urls, aapl.client.count))

    def test_date_is_sanitized(self, monkeypatch):
        start_date = datetime.datetime(2012, 3, 1)
        end_date = datetime.datetime(2015, 1, 1)
        aapl = Filing(cik='aapl', filing_type=FilingType.FILING_10Q, count=10, start_date=start_date, end_date=end_date)
        assert aapl.params['dateb'] == '20150101'
        assert aapl.params['datea'] == '20120301'
        assert aapl.start_date == datetime.datetime(2012, 3, 1)
        assert aapl.end_date == datetime.datetime(2015, 1, 1)

    def test_date_is_sanitized_when_changed(self):
        aapl = Filing(cik='aapl', filing_type=FilingType.FILING_10Q, count=10, start_date='20150101')
        assert aapl.start_date == '20150101'
        aapl.start_date = datetime.datetime(2010, 1, 1)
        assert aapl.start_date == datetime.datetime(2010, 1, 1)
        assert aapl._params['datea'] == '20100101'

    # TODO: Monkeypatch with example response
    @pytest.mark.slow
    def test_txt_urls(self, monkeypatch):
        aapl = Filing(cik='aapl', filing_type=FilingType.FILING_10Q, count=10)
        monkeypatch.setattr(CIKValidator, "get_ciks", MockCIKValidatorGetCIKs.get_ciks)
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKFiling)
        first_txt_url = aapl.get_urls()[0]
        assert first_txt_url.split('.')[-1] == 'txt'

    def test_invalid_filing_type_enum(self):
        with pytest.raises(AttributeError):
            Filing(cik='0000320193', filing_type=FilingType.INVALID)

    def test_invalid_filing_type_types(self):
        for t in ('10j', '10-k', 'ssd', 'invalid', 1):
            with pytest.raises(FilingTypeError):
                Filing(cik='0000320193', filing_type=t)

    def test_validate_cik_type_inside_filing(self):
        with pytest.raises(TypeError):
            Filing(cik=1234567891011, filing_type=FilingType.FILING_10K)
        with pytest.raises(TypeError):
            Filing(cik=123.0, filing_type=FilingType.FILING_10K)

    def test_validate_cik_inside_filing(self, monkeypatch):
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKNotFound)
        with pytest.raises(EDGARQueryError):
            _ = Filing(cik='0notvalid0', filing_type=FilingType.FILING_10K).ciks

    @pytest.mark.slow
    def test_filing_save_multiple_ciks(self, multiple_valid_ciks, tmp_data_directory):
        f = Filing(multiple_valid_ciks, FilingType.FILING_10Q, count=3)
        f.save(tmp_data_directory)

    def test_filing_save_single_cik(self, tmp_data_directory, monkeypatch):
        f = Filing('aapl', FilingType.FILING_10Q, count=3)
        monkeypatch.setattr(CIKValidator, "get_ciks", MockCIKValidatorGetCIKs.get_ciks)
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKFiling)
        f.save(tmp_data_directory)

    @pytest.mark.slow
    def test_filing_get_urls_returns_single_list_of_urls(self):
        ciks = CIK(['aapl', 'msft', 'amzn'])
        f = Filing(ciks, FilingType.FILING_10Q, count=3)
        if len(f.get_urls()) != 9:
            raise AssertionError("Expected list of length 9.")
