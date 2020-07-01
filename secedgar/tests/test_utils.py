import gzip
import pytest
import requests

from datetime import datetime

from secedgar.tests.utils import datapath
from secedgar.utils import sanitize_date, get_cik_map


class MockCIKMapResponse:
    def __init__(self, *args, **kwargs):
        with gzip.open(datapath("utils", "cik_map.json.gz"), 'rt') as f:
            self.text = f.read()


class TestUtils:
    @pytest.mark.parametrize(
        "bad_date",
        [
            "2012101",
            "201210",
            "1010",
            "2012011",
            2012011,
            2012101,
            2012,
            1010,
            201210
        ]
    )
    def test_bad_date_formats(self, bad_date):
        with pytest.raises(TypeError):
            sanitize_date(bad_date)

    @pytest.mark.parametrize(
        "good_date",
        [
            "20120101",
            20120101
        ]
    )
    def test_good_formats_no_change(self, good_date):
        """Tests formats that should not change from what is given. """
        assert sanitize_date(good_date) == good_date

    @pytest.mark.parametrize(
        "dt_date,expected",
        [
            (datetime(2018, 1, 1), "20180101"),
            (datetime(2020, 3, 4), "20200304"),
            (datetime(2020, 7, 18), "20200718")
        ]
    )
    def test_good_formats_datetime(self, dt_date, expected):
        assert sanitize_date(dt_date) == expected

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
