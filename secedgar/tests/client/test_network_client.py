import pytest
import requests

from secedgar.client import NetworkClient
from secedgar.utils.exceptions import EDGARQueryError
from secedgar.tests.utils import datapath


@pytest.fixture
def client():
    return NetworkClient(pause=0.01)


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
        self.text = ""

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


class TestNetworkClient:
    def test_client_bad_response_raises_error(self, monkeypatch, client):
        monkeypatch.setattr(requests, 'get', MockNoCIKFoundBadResponse)
        with pytest.raises(EDGARQueryError):
            client.get_response('path', {})

    def test_client_good_response_single_filing_type_passes(self, monkeypatch, client):
        monkeypatch.setattr(requests, 'get', MockSingleFilingTypeGoodResponse)
        assert client.get_response('path', {})

    def test_client_good_response_multiple_cik_results_passes(self, monkeypatch, client):
        monkeypatch.setattr(requests, 'get', MockMultipleCIKResultsGoodResponse)
        assert client.get_response('path', {})

    def test_client_good_response_single_filing_passes(self, monkeypatch, client):
        monkeypatch.setattr(requests, 'get', MockSingleFilingPageGoodResponse)
        assert client.get_response('path', {})

    @pytest.mark.parametrize(
        "status_code",
        [
            203,
            400,
            401,
            500,
            501
        ]
    )
    def test_client_bad_response_codes(self, status_code, monkeypatch, client):
        monkeypatch.setattr(requests, 'get', MockBadStatusCodeResponse(status_code))
        with pytest.raises(EDGARQueryError):
            client.get_response('path', {})

    @pytest.mark.parametrize(
        "test_input,expectation",
        [
            (0.5, pytest.raises(TypeError)),
            ("2", pytest.raises(TypeError)),
            (-1, pytest.raises(ValueError))
        ]
    )
    def test_client_bad_retry_count_setter(self, test_input, expectation, client):
        with expectation:
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
            (0.5, TypeError),
            ("1", TypeError),
            (0, ValueError)
        ]
    )
    def test_client_bad_batch_size_setter(self, test_input, expectation, client):
        with pytest.raises(expectation):
            client.batch_size = test_input
