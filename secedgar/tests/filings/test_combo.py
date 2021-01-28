from datetime import date

import pytest
from secedgar.filings.combo import ComboFilings


class TestComboFilings:
    def test_combo_quarterly_only_one_year(self):
        combo = ComboFilings(start_date=date(2020, 1, 1), end_date=date(2020, 12, 31))
        expected = [(2020, 1), (2020, 2), (2020, 3), (2020, 4)]
        assert combo.master_date_list == expected and not combo.daily_date_list

    def test_combo_quarterly_only_multiple_years(self):
        combo = ComboFilings(start_date=date(2018, 9, 1), end_date=date(2020, 6, 30))
        expected = [
            (2018, 3),
            (2018, 4),
            (2019, 1),
            (2019, 2),
            (2019, 3),
            (2019, 4),
            (2020, 1),
            (2020, 2),
        ]
        assert combo.master_date_list == expected and not combo.daily_date_list

    def test_combo_daily_only_single_day(self):
        combo = ComboFilings(start_date=date(2020, 12, 10), end_date=date(2020, 12, 10))
        assert combo.daily_date_list == ["20201210"] and not combo.master_date_list

    def test_combo_daily_only_multiple_days(self):
        combo = ComboFilings(start_date=date(2020, 12, 10), end_date=date(2020, 12, 12))
        expected = ["20201210", "20201211", "20201212"]
        assert combo.daily_date_list == expected and not combo.master_date_list

    @pytest.mark.parametrize(
        "start_date,end_date,quarterly_expected,daily_expected",
        [
            (date(2019, 12, 28), date(2020, 4, 1), [(2020, 1)], ["20191228",
                                                                 "20191229",
                                                                 "20191230",
                                                                 "20191231",
                                                                 "20200401"]),
            (date(2020, 3, 30), date(2020, 10, 2), [(2020, 2), (2020, 3)], ["20200330",
                                                                            "20200331",
                                                                            "20201001",
                                                                            "20201002"]),
            (date(2020, 1, 1), date(2020, 4, 2), [(2020, 1)], ["20200401",
                                                               "20200402"]),
            (date(2020, 3, 30), date(2020, 9, 30), [(2020, 2), (2020, 3)], ["20200330",
                                                                            "20200331"]),
        ]
    )
    # TODO: Before making daily_date_list, should we make sure there are filings for that date?
    def test_combo_daily_quarterly_mixed(self,
                                         start_date,
                                         end_date,
                                         quarterly_expected,
                                         daily_expected):
        combo = ComboFilings(start_date=start_date, end_date=end_date)
        assert combo.daily_date_list == daily_expected and combo.master_date_list == quarterly_expected
