import pytest

from datetime import datetime

from secedgar.filings.daily import DailyFilings
from secedgar.tests.utils import datapath


class MockQuarterDirectory:
    """Mock response object for all 2018 daily listings of quarter 4. """

    def __init__(self, *args):
        self.status_code = 200
        with open(datapath("filings", "daily", "daily_index_2018_QTR4.htm")) as f:
            self.text = f.read()


class MockMasterIdxFile:
    """Mock response object for master.20181231.idx file. """

    def __init__(self, *args):
        self.status_code = 200
        with open(datapath("filings", "daily", "master.20181231.idx")) as f:
            self.text = f.read()


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

    def test_get_quarterly_directory(self, monkeypatch):
        monkeypatch.setattr(DailyFilings, "_get_quarterly_directory", MockQuarterDirectory)
        assert DailyFilings(datetime(2018, 12, 31))._get_quarterly_directory().status_code == 200
        assert "master.20181231.idx" in DailyFilings(
            datetime(2018, 12, 31))._get_quarterly_directory().text

    @pytest.mark.parametrize(
        "company_name",
        [
            "HENRY SCHEIN INC",
            "ROYAL BANK OF CANADA",
            "NOVAVAX INC",
            "BROOKFIELD ASSET MANAGEMENT INC.",
            "PERUSAHAAN PERSEROAN PERSERO PT TELEKOMUNIKASI INDONESIA TBK"
        ]
    )
    def test_get_master_idx_file(self, monkeypatch, company_name):
        daily_filing = DailyFilings(datetime(2018, 12, 31))
        monkeypatch.setattr(DailyFilings, "_get_quarterly_directory", MockQuarterDirectory)
        monkeypatch.setattr(DailyFilings, "_get_master_idx_file", MockMasterIdxFile)

        # All company names above should be in file
        assert company_name in daily_filing._get_master_idx_file().text
