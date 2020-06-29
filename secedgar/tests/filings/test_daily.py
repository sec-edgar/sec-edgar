import os
import pytest
import requests

from datetime import datetime

from secedgar.filings.daily import DailyFilings
from secedgar.tests.utils import datapath


class MockQuarterDirectory:
    """Mock response object for all 2018 daily listings of quarter 4. """

    def __init__(self, *args):
        self.status_code = 200
        with open(datapath("filings", "daily", "daily_index_2018_QTR4.htm")) as f:
            self.text = f.read()


class MockFilingData:
    """Mock response object for filing."""

    def __init__(self, *args, **kwargs):
        self.text = "Testing..."


def mock_master_idx_file(*args):
    with open(datapath("filings", "daily", "master.20181231.idx")) as f:
        return f.read()


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

    @pytest.mark.parametrize(
        "bad_date",
        [
            1.0,
            12,
            "12/31/2018"
        ]
    )
    def test_bad_date_format_fails(self, bad_date):
        with pytest.raises(TypeError):
            DailyFilings(bad_date)

    @pytest.mark.parametrize(
        "url",
        [
            "http://www.sec.gov/Archives/edgar/data/1000228/0001209191-18-064398.txt",
            "http://www.sec.gov/Archives/edgar/data/1000275/0001140361-18-046093.txt",
            "http://www.sec.gov/Archives/edgar/data/1000275/0001140361-18-046095.txt",
            "http://www.sec.gov/Archives/edgar/data/1000275/0001140361-18-046101.txt",
            "http://www.sec.gov/Archives/edgar/data/1000275/0001140361-18-046102.txt"
        ]
    )
    def test_get_urls(self, monkeypatch, url):
        daily_filing = DailyFilings(datetime(2018, 12, 31))
        monkeypatch.setattr(DailyFilings, "_get_quarterly_directory", MockQuarterDirectory)
        monkeypatch.setattr(DailyFilings, "_get_master_idx_file", mock_master_idx_file)
        assert url in daily_filing.get_urls()

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
        monkeypatch.setattr(DailyFilings, "_get_master_idx_file", mock_master_idx_file)

        # All company names above should be in file
        assert company_name in daily_filing._get_master_idx_file()

    @pytest.mark.parametrize(
        "year,month,day,quarter",
        [
            (2018, 1, 1, 1),
            (2017, 5, 1, 2),
            (2016, 6, 30, 2),
            (2015, 7, 1, 3),
            (2014, 9, 30, 3),
            (2013, 10, 1, 4),
            (2012, 11, 20, 4),
            (2011, 12, 31, 4)
        ]
    )
    def test_path_property(self, year, month, day, quarter):
        daily_filing = DailyFilings(datetime(year, month, day))
        assert daily_filing.path == "Archives/edgar/daily-index/{year}/QTR{quarter}/".format(
            year=year, quarter=quarter)

    def test_no_params(self):
        """Params should always be empty."""
        daily_filing = DailyFilings(datetime(2020, 1, 1))
        assert not daily_filing.params

    @pytest.mark.parametrize(
        "date_tuple,formatted",
        [
            ((1994, 1, 2), "010294"),
            ((1994, 12, 31), "123194"),
            ((1995, 1, 1), "950101"),
            ((1995, 1, 2), "950102"),
            ((1998, 1, 1), "980101"),
            ((1998, 1, 2), "980102"),
            ((1998, 3, 31), "19980331"),
            ((1998, 4, 1), "19980401"),
            ((1999, 1, 1), "19990101"),
        ]
    )
    def test_master_idx_date_format(self, date_tuple, formatted):
        daily_filing = DailyFilings(datetime(*date_tuple))
        assert daily_filing._get_idx_formatted_date() == formatted

    @pytest.mark.parametrize(
        "subdir,file",
        [
            ("HENRY SCHEIN INC", "0001209191-18-064398.txt"),
            ("ROYAL BANK OF CANADA", "0001140361-18-046093.txt"),
            ("NOVAVAX INC", "0001144204-18-066754.txt"),
            ("BROOKFIELD ASSET MANAGEMENT INC.", "0001104659-18-075315.txt"),
            ("BANK OF SOUTH CAROLINA CORP", "0001225208-18-017075.txt")
        ]
    )
    def test_save(self, tmp_data_directory, monkeypatch, subdir, file):
        daily_filing = DailyFilings(datetime(2018, 12, 31))
        monkeypatch.setattr(DailyFilings, "_get_quarterly_directory", MockQuarterDirectory)
        monkeypatch.setattr(DailyFilings, '_get_master_idx_file', mock_master_idx_file)
        monkeypatch.setattr(requests, 'get', MockFilingData)
        daily_filing.save(tmp_data_directory)
        path_to_check = os.path.join(tmp_data_directory, subdir, file)
        assert os.path.exists(path_to_check)
