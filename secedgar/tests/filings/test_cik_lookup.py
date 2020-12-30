import pytest

from secedgar.filings import CIKLookup
from secedgar.client import NetworkClient
from secedgar.tests.conftest import MockResponse
import secedgar.utils
from secedgar.utils.exceptions import EDGARQueryError
import gzip

class MockCIKMapResponse:
    def __init__(self, *args, **kwargs):
        with gzip.open(datapath("utils", "cik_map.json.gz"), 'rt') as f:
            self.text = f.read()

@pytest.fixture
def client():
    return NetworkClient()


@pytest.fixture
def ticker_lookups():
    return ["AAPL", "FB", "GOOGL", "NFLX", "MSFT"]

@pytest.fixture
def mock_get_cik_map(monkeypatch):
    ticker_return = {'AAPL': '320193', 'MSFT': '789019', 'FB': '1326801'}
    title_return = {'AMAZON COM INC': '1018724', 'Alphabet Inc.': '1652044'}

    def _map(k):
        return ticker_return if k == 'ticker' else title_return
    monkeypatch.setattr(secedgar.utils, 'get_cik_map', _map)


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
    @pytest.mark.parametrize(
        "ticker,cik",
        [
            ("AAPL", "320193"),
            ("FB", "1326801"),
            ("MSFT", "789019")
        ]
    )
    def test_get_cik_map(self, ticker, cik, monkeypatch):
        monkeypatch.setattr(requests, 'get', MockCIKMapResponse)
        cik_map = get_cik_map()
        assert cik_map[ticker] == cik

    @pytest.mark.parametrize(
        "name,cik",
        [
            ("Apple Inc.", "320193"),
            ("NIKE, Inc.", "320187"),
            ("MICROSOFT CORP", "789019"),
        ]
    )
    def test_get_company_name_map(self, name, cik, monkeypatch):
        monkeypatch.setattr(requests, 'get', MockCIKMapResponse)
        name_map = get_cik_map(key="title")
        assert name_map[name] == cik

    @pytest.mark.parametrize(
        "key",
        [
            "Ticker",
            "Title",
            "CIK",
            "Company Name"
        ]
    )
    def test_get_cik_map_bad_keys(self, key):
        with pytest.raises(ValueError):
            get_cik_map(key=key)

    def test_client_property(self, client, ticker_lookups):
        validator = _CIKValidator(ticker_lookups, client=client)
        assert validator.client == client

    @pytest.mark.parametrize(
        "bad_lookups",
        [
            [],
            "",
            ["AAPL", 4, "FB"]
        ]
    )
    def test_empty_lookups_raises_type_error(self, bad_lookups):
        with pytest.raises(TypeError):
            _CIKValidator(lookups=bad_lookups)

    def test_lookups_property(self, ticker_lookups):
        validator = _CIKValidator(lookups=ticker_lookups)
        assert validator.lookups == ticker_lookups

    @pytest.mark.parametrize(
        "bad_lookup",
        [
            "",
            4
        ]
    )
    def test_validate_lookup(self, bad_lookup):
        with pytest.raises(TypeError):
            _CIKValidator._validate_lookup(bad_lookup)

    @pytest.mark.parametrize(
        "bad_cik",
        [
            "1234",
            1234,
            1234567890,
            "AAPL",
            "",
            None,
        ]
    )
    def test_validate_cik_on_bad_ciks(self, bad_cik):
        with pytest.raises(CIKError):
            _CIKValidator._validate_cik(bad_cik)

    def test_params_reset_after_get_cik(self, ticker_lookups, client):
        validator = _CIKValidator(lookups=ticker_lookups, client=client)
        validator._get_cik(ticker_lookups[0])
        assert validator.params.get("CIK") is None and validator.params.get("company") is None

    @pytest.mark.parametrize(
        "lookup,expected",
        [
            (['AAPL'], {'AAPL': '320193'}),
            (['AAPL', 'AMAZON COM INC'], {'AAPL': '320193', 'AMAZON COM INC': '1018724'}),
            (['Alphabet Inc.'], {'Alphabet Inc.': '1652044'}),
            (['aapl', 'msft'], {'aapl': '320193', 'msft': '789019'}),
            (['aapl', 'msft', 'Alphabet Inc.'], {
             'aapl': '320193', 'msft': '789019', 'Alphabet Inc.': '1652044'}),
        ]
    )
    def test_cik_lookup_returns_correct_values(self, lookup, expected, mock_get_cik_map):
        look = CIKLookup(lookup)
        assert look.lookup_dict == expected

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
