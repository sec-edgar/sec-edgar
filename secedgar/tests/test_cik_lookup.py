import json

import pytest
import requests
from secedgar.cik_lookup import CIKLookup
from secedgar.client import NetworkClient
from secedgar.exceptions import CIKError, EDGARQueryError
from secedgar.tests.conftest import MockResponse


@pytest.fixture
def client():
    return NetworkClient()


@pytest.fixture
def ticker_lookups():
    return ["AAPL", "FB", "GOOGL", "NFLX", "MSFT"]


@pytest.fixture
def mock_single_cik_lookup_outside_map(monkeypatch):
    monkeypatch.setattr(NetworkClient, "get_response",
                        MockResponse(datapath_args=["CIK", "single_cik_search_result.html"]))


@pytest.fixture
def mock_get_cik_map(monkeypatch):
    response_json = {"0": {"cik_str": "320193", "ticker": "AAPL", "title": "Apple Inc."},
                     "1": {"cik_str": "789019", "ticker": "MSFT", "title": "MICROSOFT CORP"},
                     "2": {"cik_str": "1018724", "ticker": "AMZN", "title": "AMAZON COM INC"},
                     "3": {"cik_str": "1326801", "ticker": "FB", "title": "Facebook Inc"},
                     "4": {"cik_str": "1652044", "ticker": "GOOGL", "title": "Alphabet Inc."},
                     "5": {"cik_str": "1652044", "ticker": "GOOG", "title": "Alphabet Inc."}}
    response_json = json.dumps(response_json)
    monkeypatch.setattr(requests, 'get', MockResponse(content=bytes(response_json, "utf-8")))


@pytest.fixture
def mock_single_cik_lookup_response(monkeypatch):
    monkeypatch.setattr(NetworkClient, "get_response",
                        MockResponse(datapath_args=["CIK", "single_cik_search_result.html"]))


@pytest.fixture
def mock_single_cik_multiple_results_response(monkeypatch):
    monkeypatch.setattr(NetworkClient, "get_response",
                        MockResponse(datapath_args=["CIK", "cik_multiple_results.html"]))


@pytest.fixture
def mock_single_cik_not_found(monkeypatch):
    monkeypatch.setattr(NetworkClient, "get_response",
                        MockResponse(datapath_args=["CIK", "cik_not_found.html"]))


class TestCIKLookup(object):
    @pytest.mark.parametrize(
        "lookup,expected",
        [
            (['AAPL'], {'AAPL': '320193'}),
            (['AAPL', 'AMAZON COM INC'], {'AAPL': '320193', 'AMAZON COM INC': '1018724'}),
            (['Alphabet Inc.'], {'Alphabet Inc.': '1652044'}),
            (['aapl', 'msft'], {'aapl': '320193', 'msft': '789019'}),
            (['aapl', 'msft', 'Alphabet Inc.'],
             {'aapl': '320193', 'msft': '789019', 'Alphabet Inc.': '1652044'}),
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

    def test_client_property(self, client, ticker_lookups):
        lookup = CIKLookup(ticker_lookups, client=client)
        assert lookup.client == client

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
            CIKLookup(lookups=bad_lookups)

    def test_lookups_property(self, ticker_lookups):
        lookup = CIKLookup(lookups=ticker_lookups)
        assert lookup.lookups == ticker_lookups

    @pytest.mark.parametrize(
        "bad_lookup",
        [
            "",
            4
        ]
    )
    def test_validate_lookup(self, bad_lookup):
        with pytest.raises(TypeError):
            CIKLookup._validate_lookup(bad_lookup)

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
            CIKLookup._validate_cik(bad_cik)

    def test_params_reset_after_get_cik(self, ticker_lookups, client,
                                        mock_single_cik_lookup_outside_map):
        lookup = CIKLookup(lookups=ticker_lookups, client=client)
        lookup._get_cik(ticker_lookups[0])
        assert lookup.params.get("CIK") is None and lookup.params.get("company") is None
