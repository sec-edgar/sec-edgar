from datetime import date

from secedgar.filings.combo import ComboFilings


class TestComboFilings:
    def test_combo_quarterly_only_one_year(self):
        combo = ComboFilings(start_date=date(2020, 1, 1), end_date=date(2020, 12, 31))
        combo.recompute()
        expected = [(2020, 1), (2020, 2), (2020, 3), (2020, 4)]
        assert combo.master_date_list == expected and not combo.daily_date_list

    def test_combo_quarterly_only_multiple_years(self):
        combo = ComboFilings(start_date=date(2018, 9, 1), end_date=date(2020, 6, 30))
        combo.recompute()
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
