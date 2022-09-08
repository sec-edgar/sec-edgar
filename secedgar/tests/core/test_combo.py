from datetime import date

import pytest
from secedgar.client import NetworkClient
from secedgar.core.combo import ComboFilings, fill_days


def lambda_matches(a, b):
    return a.__code__.co_code == b.__code__.co_code


def line_matches(a, b):
    return a[0] == b[0] and a[1] == b[1] and lambda_matches(a[2], b[2])


def quarterly_list_matches(l1, l2):
    return all(line_matches(a, b) for (a, b) in zip(l1, l2))


class TestComboFilings:
    @pytest.mark.parametrize(
        "include_start,include_end,expected",
        [
            (True, True, [date(2020, 1, i) for i in (1, 2, 3)]),
            (True, False, [date(2020, 1, i) for i in (1, 2)]),
            (False, False, [date(2020, 1, 2)]),
            (False, True, [date(2020, 1, i) for i in (2, 3)]),
        ]
    )
    def test_fill_days(self, include_start, include_end, expected):
        result = fill_days(start=date(2020, 1, 1),
                           end=date(2020, 1, 3),
                           include_start=include_start,
                           include_end=include_end)
        assert result == expected

    def test_user_agent_client_none(self):
        with pytest.raises(TypeError):
            _ = ComboFilings(start_date=date(2020, 1, 1),
                             end_date=date(2020, 12, 31),
                             user_agent=None,
                             client=None)

    def test_client_passed_to_objects(self, mock_user_agent):
        client = NetworkClient(user_agent=mock_user_agent)
        combo = ComboFilings(start_date=date(2020, 1, 1),
                             end_date=date(2020, 12, 31),
                             client=client)
        assert combo.client == client

    def test_combo_quarterly_only_one_year(self, mock_user_agent):
        combo = ComboFilings(start_date=date(2020, 1, 1),
                             end_date=date(2020, 12, 31),
                             user_agent=mock_user_agent)
        expected = [(2020, 1, lambda _: True), (2020, 2, lambda _: True),
                    (2020, 3, lambda _: True), (2020, 4, lambda _: True)]
        assert quarterly_list_matches(combo.quarterly_date_list, expected)
        assert len(combo.daily_date_list) == 0

    def test_combo_quarterly_only_multiple_years(self, mock_user_agent):
        combo = ComboFilings(start_date=date(2018, 10, 1),
                             end_date=date(2020, 6, 30),
                             user_agent=mock_user_agent)
        expected = [
            (2018, 4, lambda _: True),
            (2019, 1, lambda _: True),
            (2019, 2, lambda _: True),
            (2019, 3, lambda _: True),
            (2019, 4, lambda _: True),
            (2020, 1, lambda _: True),
            (2020, 2, lambda _: True),
        ]
        assert quarterly_list_matches(combo.quarterly_date_list, expected)
        assert len(combo.daily_date_list) == 0

    def test_combo_daily_only_single_day(self, mock_user_agent):
        combo = ComboFilings(start_date=date(2020, 12, 10),
                             end_date=date(2020, 12, 10),
                             user_agent=mock_user_agent)
        assert [str(s) for s in combo.daily_date_list] == ["2020-12-10"]
        assert len(combo.quarterly_date_list) == 0

    def test_combo_daily_only_multiple_days(self, mock_user_agent):
        combo = ComboFilings(start_date=date(2020, 12, 10),
                             end_date=date(2020, 12, 12),
                             user_agent=mock_user_agent)
        expected = ["2020-12-10", "2020-12-11", "2020-12-12"]
        assert [str(s) for s in combo.daily_date_list] == expected
        assert len(combo.quarterly_date_list) == 0

    @pytest.mark.parametrize(
        "start_date,end_date,quarterly_expected,daily_expected", [
            (date(2019, 12, 28), date(
                2020, 4, 1), [(2020, 1, lambda _: True)], [
                    "2019-12-28", "2019-12-29", "2019-12-30", "2019-12-31",
                    "2020-04-01"
            ]),
            (date(2020, 3, 30), date(2020, 10, 2), [
                (2020, 2, lambda _: True), (2020, 3, lambda _: True)
            ], ["2020-03-30", "2020-03-31", "2020-10-01", "2020-10-02"]),
            (date(2020, 1, 1), date(2020, 4, 2), [
                (2020, 1, lambda _: True)
            ], ["2020-04-01", "2020-04-02"]),
            (date(2020, 3, 30), date(2020, 9, 30), [
                (2020, 2, lambda _: True), (2020, 3, lambda _: True)
            ], ["2020-03-30", "2020-03-31"]),
            # (date(2020, 1, 1), date(2020, 6, 28), [], [(2020, 1, lambda _: True),
            #                                            (2020, 2, lambda x: date(x['date_filed']) <= date(2020, 6, 28))])  # noqa
        ])
    def test_combo_daily_quarterly_mixed(self, start_date,
                                         end_date,

                                         quarterly_expected,
                                         daily_expected,
                                         mock_user_agent):
        combo = ComboFilings(start_date=start_date, end_date=end_date, user_agent=mock_user_agent)
        assert [str(s) for s in combo.daily_date_list] == daily_expected
        assert quarterly_list_matches(combo.quarterly_date_list, quarterly_expected)

    def test_properties_on_init(self, mock_user_agent):
        start = date(2020, 1, 1)
        end = date(2020, 5, 30)
        bp = 25
        combo = ComboFilings(start_date=start,
                             end_date=end,
                             user_agent=mock_user_agent,
                             balancing_point=bp)

        assert combo.start_date == start
        assert combo.end_date == end
        assert combo.balancing_point == bp
        assert combo.client.user_agent == mock_user_agent

    @pytest.mark.parametrize(
        "bad_entry_filter",
        [
            None,
            [],
            (),
            0,
            ""]
    )
    def test_bad_entry_filter(self, bad_entry_filter):
        with pytest.raises(ValueError):
            _ = ComboFilings(start_date=date(2020, 1, 1),
                             end_date=date(2020, 5, 30),
                             entry_filter=bad_entry_filter)

    @pytest.mark.parametrize(
        "good_entry_filter",
        [
            lambda x: True,
            lambda x: False,
            lambda f: f.form_type.lower() == "10-k"
        ]
    )
    def test_good_entry_filter(self, good_entry_filter, mock_user_agent):
        combo = ComboFilings(date(2020, 1, 1),
                             date(2020, 5, 30),
                             entry_filter=good_entry_filter,
                             user_agent=mock_user_agent)
        assert combo.entry_filter == good_entry_filter

    def test_client_read_only(self, mock_user_agent):
        combo = ComboFilings(start_date=date(2020, 1, 1),
                             end_date=date(2020, 1, 3),
                             user_agent=mock_user_agent)
        with pytest.raises(AttributeError):
            combo.client = None

    def test_balancing_point_read_only(self, mock_user_agent):
        combo = ComboFilings(start_date=date(2020, 1, 1),
                             end_date=date(2020, 1, 3),
                             user_agent=mock_user_agent)
        with pytest.raises(AttributeError):
            combo.balancing_point = 20

    def test_combo_filings_quarterly_lambda(self, mock_user_agent):
        # Tests issue raised in GH#269.
        combo = ComboFilings(start_date=date(2022, 2, 28),
                             end_date=date(2022, 4, 15),
                             user_agent=mock_user_agent)

        # Make sure you can run ``_get_quarterly_daily_date_lists``
        quarter_list, date_list = combo._get_quarterly_daily_date_lists()

        assert len(quarter_list) > 0, "Expected quarterly list not to be empty"
        assert len(date_list) > 0, "Expected date list not to be empty"
        assert date_list == [date(2022, 4, d) for d in range(1, 16)], """
        Date list should have April 1 through 15."""
        assert len(quarter_list) == 1, "Should only have one quarter"
        assert quarter_list[0][0] == 2022, "Only quarter in list should be Q1 2022"
        assert quarter_list[0][1] == 1, "Only quarter in list should be Q1 2022"

    def test_combo_no_user_agent_raises_error(self):
        with pytest.raises(TypeError):
            _ = ComboFilings(start_date=date(2022, 2, 28),
                             end_date=date(2022, 4, 15))
