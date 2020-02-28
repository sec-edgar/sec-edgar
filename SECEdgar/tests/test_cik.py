import pytest

from SECEdgar.tests.utils import datapath

from SECEdgar.filings import CIK
from SECEdgar.client import NetworkClient
from SECEdgar.utils.exceptions import EDGARQueryError


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


class TestCIK(object):
    def test_cik_returns_correct_values(self, monkeypatch):
        aapl = CIK('aapl')
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKLookupResponse)
        assert aapl.ciks == ['0000320193']

    def test_multiple_results_company_name_search(self, monkeypatch):
        multiple_results_cik = CIK('paper')
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKMultipleResultsResponse)
        assert len(multiple_results_cik.ciks) == 0

    def test_multiple_results_raises_warnings(self, monkeypatch):
        multiple_results_cik = CIK('paper')
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKMultipleResultsResponse)
        with pytest.warns(UserWarning):
            _ = multiple_results_cik.ciks

    def test_validate_cik_is_string(self):
        # float and int not accepted, raising TypeError
        with pytest.raises(TypeError):
            CIK(1234567891011)
        with pytest.raises(TypeError):
            CIK(123.0)

    def test_validate_cik_after_cik_lookup(self, monkeypatch):
        # string remains unchecked until query to allow for possibility of
        # using company name, ticker, or CIK as string
        monkeypatch.setattr(NetworkClient, "get_response", MockSingleCIKNotFound)
        with pytest.raises(EDGARQueryError):
            _ = CIK('0notvalid0').ciks
