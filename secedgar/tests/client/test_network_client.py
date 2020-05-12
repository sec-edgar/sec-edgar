import pytest
import requests

from secedgar.client import NetworkClient
from secedgar.utils.exceptions import EDGARQueryError
from secedgar.tests.utils import datapath


@pytest.fixture
def client():
    return NetworkClient()


class MockNoCIKFoundBadResponse:
    """Returns response with 'No matching CIK' message."""

    def __init__(self, *args, **kwargs):
        self.status_code = 200
        with open(datapath('CIK', 'cik_not_found.html')) as f:
            self.text = f.read()


class MockBadStatusCodeResponse:
    """Returns mock response with bad status code."""

    def __init__(self, status_code):
        if (status_code == 200):
            raise ValueError("status_code should not equal 200.")
        self.status_code = status_code

    def __call__(self, *args, **kwargs):
        return self


class MockMultipleFilingTypesGoodResponse:
    """Returns response with list of filings (multiple types) for single CIK."""

    def __init__(self, *args, **kwargs):
        self.status_code = 200
        with open(datapath('CIK', 'single_cik_search_result.html'), encoding='iso-8859-1') as f:
            self.text = f.read()


class MockSingleFilingTypeGoodResponse:
    """Returns response with list of single filing type for single CIK."""

    def __init__(self, *args, **kwargs):
        self.status_code = 200
        with open(datapath('CIK', 'single_cik_multiple_filings_10k.html')) as f:
            self.text = f.read()


class MockMultipleCIKResultsGoodResponse:
    """Returns page with multiple results for CIK when validating CIK."""

    def __init__(self, *args, **kwargs):
        self.status_code = 200
        with open(datapath('CIK', 'cik_multiple_results.html')) as f:
            self.text = f.read()


class MockSingleFilingPageGoodResponse:
    """Returns page for one filing for one company."""

    def __init__(self, *args, **kwargs):
        self.status_code = 200
        with open(datapath('CIK', 'single_filing_page.html')) as f:
            self.text = f.read()


class TestClient:
    def test_client_bad_response_raises_error(self, monkeypatch, client):
        monkeypatch.setattr(requests, 'get', MockNoCIKFoundBadResponse)
        with pytest.raises(EDGARQueryError):
            client.get_response('path', {})

    @pytest.mark.parametrize(
        "response",
        [
            MockSingleFilingTypeGoodResponse,
            MockMultipleCIKResultsGoodResponse,
            MockSingleFilingPageGoodResponse
        ]
    )
    def test_good_responses(self, monkeypatch, client, response):
        monkeypatch.setattr(requests, 'get', response)
        assert client.get_response('path', {})

    @pytest.mark.parametrize(
        "status_code",
        [
            204,
            400,
            401,
            403,
            404,
            500,
            501,
            502
        ]
    )
    def test_client_bad_response_codes(self, status_code, monkeypatch, client):
        monkeypatch.setattr(requests, 'get', MockBadStatusCodeResponse(status_code))
        with pytest.raises(EDGARQueryError):
            client.get_response('path', {})

    @pytest.mark.parametrize(
        "test_input,error",
        [
            (0.5, TypeError),
            ("2", TypeError),
            (-1, ValueError)
        ]
    )
    def test_client_bad_retry_count_setter(self, test_input, error, client):
        with pytest.raises(error):
            client.retry_count = test_input

    @pytest.mark.parametrize(
        "test_input,expectation",
        [
            ("2", pytest.raises(TypeError)),
            (-0.5, pytest.raises(ValueError)),
            (-1, pytest.raises(ValueError))
        ]
    )
    def test_client_bad_pause_setter(self, test_input, expectation, client):
        with expectation:
            client.pause = test_input

    @pytest.mark.parametrize(
        "test_input,expectation",
        [
            (0.5, pytest.raises(TypeError)),
            ("1", pytest.raises(TypeError)),
            (0, pytest.raises(ValueError))
        ]
    )
    def test_client_bad_count_setter(self, test_input, expectation, client):
        with expectation:
            client.count = test_input
