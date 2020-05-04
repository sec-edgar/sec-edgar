import pytest

from datetime import datetime

from secedgar.filings.daily import DailyFilings


class TestDaily:
    @pytest.mark.parametrize(
        "date,expected",
        [
            (datetime(2020, 1, 1), 1),
            (datetime(2020, 3, 31), 1),
            (datetime(2020, 4, 1), 2),
            (datetime(2020, 6, 30), 2),
            (datetime(2020, 7, 1), 3),
            (datetime(2020, 9, 30), 3),
            (datetime(2020, 10, 1), 4),
            (datetime(2020, 12, 31), 4)
        ]
    )
    def test_quarter(self, date, expected):
        assert DailyFilings(date=date).quarter == expected

    def test_get_urls(self, monkeypatch):
        pass
