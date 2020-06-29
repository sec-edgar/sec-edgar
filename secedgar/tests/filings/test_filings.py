# Tests if filings are correctly received from EDGAR
import datetime
import pytest

from secedgar.client import NetworkClient
from secedgar.filings import Filing, FilingType

from secedgar.filings.cik_validator import _CIKValidator
from secedgar.tests.utils import datapath
from secedgar.utils.exceptions import FilingTypeError, EDGARQueryError


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


class MockCIKValidatorMultipleCIKs:
    def __init__(self, *args):
        pass

    @staticmethod
    def get_ciks(self):
        return {'aapl': '0000320193', 'msft': '', 'amzn': ''}


class TestFiling(object):
    @pytest.mark.slow
    def test_count_returns_exact(self, monkeypatch):
        count = 10
        aapl = Filing(cik_lookup='aapl', filing_type=FilingType.FILING_10Q, count=count)
        monkeypatch.setattr(_CIKValidator, "get_ciks", MockCIKValidatorGetCIKs.get_ciks)
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKFiling)
        urls = aapl.get_urls()['aapl']
        if len(urls) != count:
            raise AssertionError("""Count should return exact number of filings.
                                 Got {0}, but expected {1} URLs.""".format(
                urls, count))

    def test_date_is_sanitized(self):
        start_date = datetime.datetime(2012, 3, 1)
        end_date = datetime.datetime(2015, 1, 1)
        aapl = Filing(cik_lookup='aapl',
                      filing_type=FilingType.FILING_10Q,
                      count=10,
                      start_date=start_date,
                      end_date=end_date)
        assert aapl.params['dateb'] == '20150101'
        assert aapl.params['datea'] == '20120301'
        assert aapl.start_date == datetime.datetime(2012, 3, 1)
        assert aapl.end_date == datetime.datetime(2015, 1, 1)

    def test_date_is_sanitized_when_changed(self):
        aapl = Filing(cik_lookup='aapl',
                      filing_type=FilingType.FILING_10Q,
                      count=10,
                      start_date='20150101')
        assert aapl.start_date == '20150101'
        aapl.start_date = datetime.datetime(2010, 1, 1)
        assert aapl.start_date == datetime.datetime(2010, 1, 1)
        assert aapl.params['datea'] == '20100101'

    @pytest.mark.parametrize(
        "date,expected",
        [
            ("20120101", "20120101"),
            (20120101, 20120101),
            (datetime.datetime(2012, 1, 1), "20120101")
        ]
    )
    def test_end_date_setter(self, date, expected):
        f = Filing('aapl', FilingType.FILING_10Q, start_date=datetime.datetime(
            2010, 1, 1), end_date=datetime.datetime(2015, 1, 1))
        f.end_date = date
        assert f.end_date == date and f.params.get("dateb") == expected

    @pytest.mark.slow
    def test_txt_urls(self, monkeypatch):
        aapl = Filing(cik_lookup='aapl', filing_type=FilingType.FILING_10Q, count=10)
        monkeypatch.setattr(_CIKValidator, "get_ciks", MockCIKValidatorGetCIKs.get_ciks)
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKFiling)
        first_txt_url = aapl.get_urls()['aapl'][0]
        assert first_txt_url.split('.')[-1] == 'txt'

    @pytest.mark.parametrize(
        "new_filing_type",
        (
            FilingType.FILING_10K,
            FilingType.FILING_8K,
            FilingType.FILING_13F,
            FilingType.FILING_SD
        )
    )
    def test_filing_type_setter(self, new_filing_type):
        f = Filing(cik_lookup='aapl', filing_type=FilingType.FILING_10Q)
        f.filing_type = new_filing_type
        assert f.filing_type == new_filing_type

    @pytest.mark.parametrize(
        "bad_filing_type",
        (
            '10-k',
            '10k',
            '10-q',
            '10q',
            123
        )
    )
    def test_bad_filing_type_setter(self, bad_filing_type):
        f = Filing(cik_lookup='aapl', filing_type=FilingType.FILING_10Q)
        with pytest.raises(FilingTypeError):
            f.filing_type = bad_filing_type

    @pytest.mark.parametrize(
        "bad_filing_type",
        (
            "10-j",
            "10-k",
            "ssd",
            "invalid",
            1
        )
    )
    def test_invalid_filing_type_types(self, bad_filing_type):
        with pytest.raises(FilingTypeError):
            Filing(cik_lookup='0000320193', filing_type=bad_filing_type)

    @pytest.mark.parametrize(
        "bad_cik_lookup",
        (
            1234567891011,
            12345,
            123.0
        )
    )
    def test_validate_cik_type_inside_filing(self, bad_cik_lookup):
        with pytest.raises(TypeError):
            Filing(cik_lookup=bad_cik_lookup, filing_type=FilingType.FILING_10K)

    def test_validate_cik_inside_filing(self, monkeypatch):
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKNotFound)
        with pytest.raises(EDGARQueryError):
            _ = Filing(cik_lookup='0notvalid0', filing_type=FilingType.FILING_10K).cik_lookup.ciks

    @pytest.mark.parametrize(
        "no_urls",
        (
            {},
            {'aapl': [], 'fb': [], 'msft': []}
        )
    )
    def test_save_no_filings_raises_error(self, tmp_data_directory, monkeypatch, no_urls):
        monkeypatch.setattr(Filing, "get_urls", lambda x: no_urls)
        f = Filing(cik_lookup='aapl', filing_type=FilingType.FILING_10K)
        with pytest.raises(ValueError):
            f.save(tmp_data_directory)

    def test_filing_save_multiple_ciks(self, tmp_data_directory, monkeypatch):
        monkeypatch.setattr(_CIKValidator, "get_ciks", MockCIKValidatorMultipleCIKs.get_ciks)
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKFiling)
        f = Filing(['aapl', 'amzn', 'msft'], FilingType.FILING_10Q, count=3)
        f.save(tmp_data_directory)

    def test_filing_save_single_cik(self, tmp_data_directory, monkeypatch):
        f = Filing('aapl', FilingType.FILING_10Q, count=3)
        monkeypatch.setattr(_CIKValidator, "get_ciks", MockCIKValidatorGetCIKs.get_ciks)
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKFiling)
        f.save(tmp_data_directory)

    def test_filing_get_urls_returns_single_list_of_urls(self, monkeypatch):
        monkeypatch.setattr(_CIKValidator, "get_ciks", MockCIKValidatorMultipleCIKs.get_ciks)
        # Use same response for each request
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKFiling)
        f = Filing(cik_lookup=['aapl', 'msft', 'amzn'], filing_type=FilingType.FILING_10Q, count=5)
        assert all(len(f.get_urls().get(key)) == 5 for key in f.get_urls().keys())

    @pytest.mark.parametrize(
        "count",
        [
            10,
            25,
            30
        ]
    )
    def test_filing_returns_correct_number_of_urls(self, monkeypatch, count):
        monkeypatch.setattr(_CIKValidator, "get_ciks", MockCIKValidatorMultipleCIKs.get_ciks)
        # Use same response for each request
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKFiling)
        f = Filing(cik_lookup=['aapl', 'msft', 'amzn'], filing_type=FilingType.FILING_10Q,
                   count=count, client=NetworkClient(batch_size=10))
        assert all(len(f.get_urls().get(key)) == count for key in f.get_urls().keys())
