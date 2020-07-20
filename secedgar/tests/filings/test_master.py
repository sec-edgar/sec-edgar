import pytest

from datetime import datetime
from secedgar.filings.master import MasterFilings


class TestMaster:
    @pytest.mark.parametrize(
        "bad_year,expected_error",
        [
            (-1, ValueError),
            (0.0, TypeError),
            (1990, ValueError),
            (1991, ValueError),
            (1992, ValueError),
            ("1993", TypeError),
            ("1993.0", TypeError),

        ]
    )
    def test_bad_year(self, bad_year, expected_error):
        with pytest.raises(expected_error):
            _ = MasterFilings(year=bad_year, quarter=1)

    def test_good_year(self):
        for year in range(1993, datetime.today().year + 1):
            mf = MasterFilings(year=year, quarter=1)
            assert mf.year == year

    @pytest.mark.parametrize(
        "bad_quarter,expected_error",
        [
            (0.0, TypeError),
            (1.0, TypeError),
            ("1", TypeError),
            ("1.0", TypeError),
            (0, ValueError),
            (5, ValueError),
            (6, ValueError),
            (2020, ValueError)

        ]
    )
    def test_bad_quarter(self, bad_quarter, expected_error):
        with pytest.raises(expected_error):
            _ = MasterFilings(year=2020, quarter=bad_quarter)

    def test_good_quarters(self):
        for quarter in range(1, 5):
            mf = MasterFilings(year=2019, quarter=quarter)
            assert mf.quarter == quarter

    @pytest.mark.parametrize(
        "year,quarter",
        [
            (2018, 1),
            (2019, 2),
            (2020, 3)
        ]
    )
    def test_idx_filename_is_always_the_same(self, year, quarter):
        mf = MasterFilings(year=year, quarter=quarter)
        assert mf.idx_filename == "master.idx"
