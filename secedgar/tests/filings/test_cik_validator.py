import pytest

from secedgar.filings.cik_validator import _CIKValidator
from secedgar.client import NetworkClient
from secedgar.utils.exceptions import CIKError


@pytest.fixture
def client():
    return NetworkClient()


@pytest.fixture
def ticker_lookups():
    return ["AAPL", "FB", "GOOGL", "NFLX", "MSFT"]


class TestCIKValidator:
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
