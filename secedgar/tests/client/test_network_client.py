import asyncio
import math
import os
import time

import pytest
import requests
from secedgar.client import NetworkClient
from secedgar.tests.conftest import MockResponse
from secedgar.utils.exceptions import EDGARQueryError


@pytest.fixture
def client():
    return NetworkClient(pause=0.01)


@pytest.fixture
def mock_no_cik_found_bad_response(monkeypatch):
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: MockResponse(
        datapath_args=['CIK', 'cik_not_found.html']))


class MockBadStatusCodeResponse:
    """Returns mock response with bad status code."""

    def __init__(self, status_code):
        if (status_code == 200):
            raise ValueError("status_code should not equal 200.")
        self.status_code = status_code
        self.text = ""

    def __call__(self, *args, **kwargs):
        return self


@pytest.fixture
def mock_single_filing_type_good_response(monkeypatch):
    """Mock response with list of single filing type for single CIK."""
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: MockResponse(
        datapath_args=['CIK', 'single_cik_multiple_filings_10k.html']))


@pytest.fixture
def mock_multiple_cik_results_good_response(monkeypatch):
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: MockResponse(
        datapath_args=['CIK', 'cik_multiple_results.html']))


@pytest.fixture
def mock_single_filing_page_good_response(monkeypatch):
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: MockResponse(
        datapath_args=['CIK', 'single_filing_page.html']))


class TestNetworkClient:
    def test_client_bad_response_raises_error(self,
                                              mock_no_cik_found_bad_response,
                                              client):
        with pytest.raises(EDGARQueryError):
            client.get_response('path', {})

    def test_client_good_response_single_filing_type_passes(self,
                                                            mock_single_filing_type_good_response,
                                                            client):
        assert client.get_response('path', {})

    def test_client_good_response_multiple_cik_results_passes(self,
                                                              mock_multiple_cik_results_good_response,  # noqa: E501
                                                              client):
        assert client.get_response('path', {})

    def test_client_good_response_single_filing_passes(self,
                                                       mock_single_filing_page_good_response,
                                                       client):
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
            (0.5, TypeError),
            ("2", TypeError),
            (-1, ValueError)
        ]
    )
    def test_client_bad_retry_count_setter(self, test_input, expectation, client):
        with pytest.raises(expectation):
            client.retry_count = test_input

    @pytest.mark.parametrize(
        "test_input,expectation",
        [
            (0, ValueError),
            (-1, ValueError),
            (11, ValueError),
            (-1.5, ValueError),
            (11.5, ValueError)
        ]
    )
    def test_client_bad_rate_limit(self, test_input, expectation, client):
        with pytest.raises(expectation):
            client.rate_limit = test_input

    @pytest.mark.parametrize(
        "test_input,expectation",
        [
            ("2", TypeError),
            (-0.5, ValueError),
            (-1, ValueError)
        ]
    )
    def test_client_bad_pause_setter(self, test_input, expectation, client):
        with pytest.raises(expectation):
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

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "rate_limit",
        range(1, 10)
    )
    def test_rate_limit(self, tmp_data_directory, rate_limit, mock_filing_response):
        client = NetworkClient(rate_limit=rate_limit)
        min_seconds = 3
        num_requests = rate_limit * min_seconds
        inputs = [("https://google.com", os.path.join(tmp_data_directory, str(i)))
                  for i in range(num_requests)]
        loop = asyncio.get_event_loop()
        start = time.time()
        loop.run_until_complete(client.wait_for_download_async(inputs))
        end = time.time()
        assert num_requests / math.ceil(end - start) <= rate_limit
