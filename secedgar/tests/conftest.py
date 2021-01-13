import pytest
import requests
from secedgar.client import NetworkClient
from secedgar.filings import MasterFilings
from secedgar.tests.utils import AsyncMockResponse, MockResponse, datapath


@pytest.fixture(scope="module")
def monkeymodule():
    from _pytest.monkeypatch import MonkeyPatch
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(scope="session")
def monkeysession():
    from _pytest.monkeypatch import MonkeyPatch
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(autouse=True, scope="session")
def no_http_requests(monkeysession):
    def external_request_mock(object, *args, **kwargs):
        raise RuntimeError(
            f"""A request to an external source was about to be made by {object}.
            Please provide mock for {object}.""")

    to_avoid = (
        "requests.Session.get",
        "aiohttp.ClientSession.get"
    )

    for avoid in to_avoid:
        monkeysession.setattr(avoid, external_request_mock)


@pytest.fixture(scope="session")
def mock_filing_response(monkeysession):
    monkeysession.setattr(NetworkClient, "fetch",
                          lambda *args, **kwargs:
                          AsyncMockResponse(content=bytes("Testing...", "utf-8")).read())


@pytest.fixture(scope="session")
def mock_master_idx_file(monkeysession):
    """Mock idx file from DailyFilings."""

    def _mock_master_idx_file(*args, **kwargs):
        with open(datapath("filings", "master", "master.idx")) as f:
            return f.read()

    monkeysession.setattr(MasterFilings, "_get_master_idx_file",
                          _mock_master_idx_file)


@pytest.fixture(scope="session")
def mock_filing_data(monkeysession):
    """Mock data from filing."""
    monkeysession.setattr(requests.Session, "get",
                          MockResponse(content=bytes("Testing...", "utf-8")))


@pytest.fixture(scope="session")
def tmp_data_directory(tmpdir_factory):
    return str(tmpdir_factory.mktemp("tmp_data"))
