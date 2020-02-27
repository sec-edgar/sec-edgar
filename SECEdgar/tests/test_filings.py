# Tests if filings are correctly received from EDGAR
import datetime
import pytest
import requests

from SECEdgar.client import NetworkClient
from SECEdgar.filings import Filing, FilingType, CIK

from SECEdgar.tests.utils import datapath
from SECEdgar.utils.exceptions import FilingTypeError, EDGARQueryError


class MockSingleCIKNotFound:
    def __init__(self, *args):
        self.status_code = 200
        with open(datapath("CIK", "cik_not_found.html"), 'rb') as f:
            self.text = f.read()


class TestFiling(object):
    @pytest.mark.slow
    def test_count_returns_exact(self, valid_filing_10k):
        urls = valid_filing_10k.get_urls()
        if len(urls) != valid_filing_10k.client.count:
            raise AssertionError("""Count should return exact number of filings.
                                 Got {0}, but expected {1} URLs.""".format(
                    urls, valid_filing_10k.client.count))

    def test_date_is_sanitized(self, valid_filing_10k):
        date = datetime.datetime(2015, 1, 1)
        valid_filing_10k.end_date = date
        if not valid_filing_10k.end_date == '20150101':
            raise AssertionError("The end date was not correctly sanitized.")

    def test_date_is_sanitized_when_changed(self, valid_filing_10k):
        valid_filing_10k.end_date = datetime.datetime(2016, 1, 1)
        if not valid_filing_10k.end_date == '20160101':
            raise AssertionError("The end date was not correctly sanitized after change.")

    # TODO: Monkeypatch with example response
    @pytest.mark.slow
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

    @pytest.mark.slow
    def test_filing_save_single_cik(self, single_valid_cik, tmp_data_directory):
        f = Filing(single_valid_cik, FilingType.FILING_10Q, count=3)
        f.save(tmp_data_directory)

    @pytest.mark.slow
    def test_filing_get_urls_returns_single_list_of_urls(self):
        ciks = CIK(['aapl', 'msft', 'amzn'])
        f = Filing(ciks, FilingType.FILING_10Q, count=3)
        if len(f.get_urls()) != 9:
            raise AssertionError("Expected list of length 9.")
