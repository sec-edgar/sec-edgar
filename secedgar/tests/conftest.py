import pytest
import requests

from secedgar.client import NetworkClient
from secedgar.filings import DailyFilings, MasterFilings
from secedgar.filings.cik_validator import _CIKValidator
from secedgar.tests.utils import datapath


class MockResponse:
    def __init__(self, datapath_args=[],
                 status_code=200,
                 file_read_args='r',
                 text=None,
                 *args,
                 **kwargs):
        self.status_code = status_code
        if text is not None:
            self.text = text
        else:
            with open(datapath(*datapath_args), file_read_args, **kwargs) as f:
                self.text = f.read()


@pytest.fixture
def mock_single_cik_not_found(monkeypatch):
    """NetworkClient's get_response method will return html with CIK not found message."""
    monkeypatch.setattr(NetworkClient, "get_response", lambda *args, **
                        kwargs: MockResponse(datapath_args=["CIK", "cik_not_found.html"],
                                             file_read_args='rb'))


@pytest.fixture
def mock_single_cik_filing(monkeypatch):
    """Returns mock response of filinghrefs for getting filing URLs."""
    monkeypatch.setattr(NetworkClient, "get_response", lambda *args, **
                        kwargs: MockResponse(datapath_args=["filings", "aapl_10q_filings.xml"]))


class MockSingleCIKFilingLimitedResponses:
    def __init__(self, num_responses):
        self._called_count = 0
        self._num_responses = num_responses

    def __call__(self, *args):
        if self._called_count * 10 < self._num_responses:
            self._called_count += 1
            return MockResponse(datapath_args=["filings", "aapl_10q_filings.xml"])
        else:
            return MockResponse(text="")


# FIXME: This may not be working as expected. Need to look into this more.
@pytest.fixture
def mock_single_cik_filing_limited_responses(monkeypatch):
    """Mocks when only a limited number of filings are available."""
    mock_limited_responses = MockSingleCIKFilingLimitedResponses(num_responses=10)

    monkeypatch.setattr(NetworkClient, "get_response", lambda *args,
                        **kwargs: mock_limited_responses())


@pytest.fixture
def mock_daily_quarter_directory(monkeypatch):
    """Mocks directory of all daily filings for quarter."""
    monkeypatch.setattr(DailyFilings, "get_listings_directory", lambda *args, **
                        kwargs: MockResponse(datapath_args=["filings", "daily",
                                                            "daily_index_2018_QTR4.htm"]))


@pytest.fixture
def mock_master_quarter_directory(monkeypatch):
    """Mock directory of all filings for quarter.

    Use for MasterFilings object.
    """
    monkeypatch.setattr(MasterFilings, "get_listings_directory", lambda *args, **
                        kwargs: MockResponse(datapath_args=["filings", "master",
                                                            "master_index_1993_QTR4.html"]))


@pytest.fixture
def mock_daily_idx_file(monkeypatch):
    """Mock idx file from DailyFilings."""

    def _mock_daily_idx_file(*args, **kwargs):
        with open(datapath("filings", "daily", "master.20181231.idx")) as f:
            return f.read()

    monkeypatch.setattr(DailyFilings, "_get_master_idx_file", _mock_daily_idx_file)


@pytest.fixture
def mock_master_idx_file(monkeypatch):
    """Mock idx file from DailyFilings."""

    def _mock_master_idx_file(*args, **kwargs):
        with open(datapath("filings", "master", "master.idx")) as f:
            return f.read()

    monkeypatch.setattr(MasterFilings, "_get_master_idx_file", _mock_master_idx_file)


@pytest.fixture
def mock_cik_validator_get_single_cik(monkeypatch):
    """Mocks response for getting a single CIK."""
    monkeypatch.setattr(_CIKValidator, "get_ciks", lambda *args, **kwargs: {'aapl': '0000320193'})


@pytest.fixture
def mock_cik_validator_get_multiple_ciks(monkeypatch):
    """Mocks response for getting a single CIK."""
    monkeypatch.setattr(_CIKValidator, "get_ciks", lambda *args, **
                        kwargs: {'aapl': '0000320193', 'msft': '1234', 'amzn': '5678'})


@pytest.fixture
def mock_filing_data(monkeypatch):
    """Mock data from filing."""
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: MockResponse(text="Testing..."))


@pytest.fixture(scope="session")
def tmp_data_directory(tmpdir_factory):
    return str(tmpdir_factory.mktemp("tmp_data"))
