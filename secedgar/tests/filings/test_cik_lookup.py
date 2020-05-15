import pytest

from secedgar.tests.utils import datapath

from secedgar.filings import CIKLookup
from secedgar.client import NetworkClient
from secedgar.utils.exceptions import EDGARQueryError


class MockSingleCIKLookupResponse:
    def __init__(self, *args):
        self.status_code = 200
        with open(datapath("CIK", "single_cik_search_result.html"), 'rb') as f:
            self.text = f.read()


class MockSingleCIKMultipleResultsResponse:
    def __init__(self, *args):
        self.status_code = 200
        with open(datapath("CIK", "cik_multiple_results.html"), 'rb') as f:
            self.text = f.read()


class MockSingleCIKNotFound:
    def __init__(self, *args):
        self.status_code = 200
        with open(datapath("CIK", "cik_not_found.html"), 'rb') as f:
            self.text = f.read()


class TestCIKLookup(object):
    def test_cik_lookup_returns_correct_values(self, monkeypatch):
        aapl = CIKLookup('aapl')
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKLookupResponse)
        assert aapl.ciks == ['0000320193']

    def test_cik_lookup_lookups_property(self):
        multiple_company_lookup = CIKLookup(['aapl', 'msft', 'fb'])
        assert multiple_company_lookup.lookups == ['aapl', 'msft', 'fb']

    def test_multiple_results_company_name_search(self, monkeypatch):
        multiple_results_cik = CIKLookup('paper')
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKMultipleResultsResponse)
        with pytest.warns(UserWarning):
            assert len(multiple_results_cik.ciks) == 0

    def test_multiple_results_raises_warnings(self, monkeypatch):
        multiple_results_cik = CIKLookup('paper')
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKMultipleResultsResponse)
        with pytest.warns(UserWarning):
            _ = multiple_results_cik.ciks

    @pytest.mark.parametrize(
        "bad_cik,expected",
        [
            (1234567890, pytest.raises(TypeError)),
            (123.0, pytest.raises(TypeError)),
        ]
    )
    def test_validate_cik__is_string(self, bad_cik, expected):
        # float and int not accepted, raising TypeError
        with expected:
            CIKLookup(bad_cik)

    def test_validate_cik_after_cik_lookup(self, monkeypatch):
        # string remains unchecked until query to allow for possibility of
        # using company name, ticker, or CIK as string
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKNotFound)
        with pytest.raises(EDGARQueryError):
            _ = CIKLookup('0notvalid0').ciks
