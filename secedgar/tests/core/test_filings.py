from datetime import date

import pytest
from secedgar.client import NetworkClient
from secedgar.core import DailyFilings, QuarterlyFilings
from secedgar.core.combo import ComboFilings
from secedgar.core.filings import filings
from secedgar.exceptions import FilingTypeError


class TestFilings:

    def test_bad_filing_type(self):
        with pytest.raises(FilingTypeError):
            filings(cik_lookup='aapl', filing_type='10-k')

    def test_filing_type_plus_entry_filter_filters_both(self):
        pass

    def test_count_not_implemented(self, mock_user_agent):
        with pytest.raises(NotImplementedError):
            filings(start_date=date(2010, 1, 1),
                    end_date=date(2020, 1, 1),
                    user_agent=mock_user_agent,
                    count=10)

    def test_no_end_date_no_cik_lookp_returns_daily_filings(self, mock_user_agent):
        day = date(2020, 1, 1)

        f = filings(start_date=day, end_date=date(2020, 1, 1), user_agent=mock_user_agent)
        assert isinstance(f, DailyFilings)
        assert f.date == day
        assert f.year == day.year
        assert f.quarter == day.month // 3 + 1

    def test_exact_quarter_returns_quarterly_filings(self, mock_user_agent):
        f = filings(start_date=date(2020, 1, 1), end_date=date(
            2020, 3, 31), user_agent=mock_user_agent)
        assert isinstance(f, QuarterlyFilings)
        assert f.year == 2020
        assert f.quarter == 1

    def test_mismatch_of_quarters_returns_combo_filings(self, mock_user_agent):
        start_date = date(2020, 1, 1)
        end_date = date(2020, 5, 1)
        f = filings(start_date=start_date, end_date=end_date, user_agent=mock_user_agent)
        assert isinstance(f, ComboFilings)
        assert f.start_date == start_date
        assert f.end_date == end_date

    @pytest.mark.parametrize(
        "kwargs,error",
        [
            (dict(), ValueError),
            (dict(end_date=date(2020, 1, 1)), ValueError),
            (dict(client=NetworkClient(user_agent="Test")), ValueError),
            (dict(entry_filter=lambda f: f.form_type == '10-k'), ValueError),

            # end_date assumed to be today - giving count tries to
            # make daily or quarterly filing, but will not be recognized
            (dict(count=10, client=NetworkClient(user_agent="Test")), NotImplementedError),
            (dict(count=10), NotImplementedError),
        ])
    def test_bad_args_combination_raises_error(self, kwargs, error):
        with pytest.raises(error):
            filings(**kwargs)
