import pytest

from secedgar.filings import CIKLookup
from secedgar.client import NetworkClient
from secedgar.tests.conftest import MockResponse
from secedgar.utils.exceptions import EDGARQueryError


@pytest.fixture
def mock_single_cik_lookup_response(monkeypatch):
    def _mock_single_cik_lookup_response(*args, **kwargs):
        return MockResponse(datapath_args=["CIK", "single_cik_search_result.html"],
                            file_read_args="rb")
    monkeypatch.setattr(NetworkClient, "get_response", _mock_single_cik_lookup_response)


@pytest.fixture
def mock_single_cik_multiple_results_response(monkeypatch):
    def _mock_single_cik_multiple_results_response(*args, **kwargs):
        return MockResponse(datapath_args=["CIK", "cik_multiple_results.html"], file_read_args="rb")
    monkeypatch.setattr(NetworkClient, "get_response", _mock_single_cik_multiple_results_response)


@pytest.fixture
def mock_single_cik_not_found(monkeypatch):
    def _mock_single_cik_not_found(*args, **kwargs):
        return MockResponse(datapath_args=["CIK", "cik_not_found.html"], file_read_args="rb")
    monkeypatch.setattr(NetworkClient, "get_response", _mock_single_cik_not_found)


class TestCIKLookup(object):
    def test_cik_lookup_returns_correct_values(self, mock_single_cik_lookup_response):
        aapl = CIKLookup('aapl')
        assert aapl.ciks == ['0000320193']

    def test_cik_lookup_lookups_property(self):
        multiple_company_lookup = CIKLookup(['aapl', 'msft', 'fb'])
        assert multiple_company_lookup.lookups == ['aapl', 'msft', 'fb']

    def test_multiple_results_company_name_search(self, mock_single_cik_multiple_results_response):
        multiple_results_cik = CIKLookup('paper')
        with pytest.warns(UserWarning):
            assert len(multiple_results_cik.ciks) == 0

    def test_multiple_results_raises_warnings(self, mock_single_cik_multiple_results_response):
        multiple_results_cik = CIKLookup('paper')
        with pytest.warns(UserWarning):
            _ = multiple_results_cik.ciks

    @pytest.mark.parametrize(
        "bad_cik",
        [
            1234567890,
            123.0,
        ]
    )
    def test_validate_cik__is_string(self, bad_cik):
        with pytest.raises(TypeError):
            CIKLookup(bad_cik)

    def test_validate_cik_after_cik_lookup(self, mock_single_cik_not_found):
        # string remains unchecked until query to allow for possibility of
        # using company name, ticker, or CIK as string
        with pytest.raises(EDGARQueryError):
            _ = CIKLookup('0notvalid0').ciks
