from datetime import date

import pytest
from secedgar.client import NetworkClient
from secedgar.exceptions import FilingTypeError
from secedgar.filings import DailyFilings, QuarterlyFilings
from secedgar.filings.filings import filings


class TestFilings:
    def test_bad_filing_type(self):
        with pytest.raises(FilingTypeError):
            filings(cik_lookup='aapl', filing_type='10-k')

    def test_filing_type_plus_entry_filter_filters_both(self):
        pass

    def test_count_not_implemented(self):
        with pytest.raises(NotImplementedError):
            filings(start_date=date(2010, 1, 1), end_date=date(2020, 1, 1), count=10)

    def test_no_end_date_no_cik_lookp_returns_daily_filings(self):
        day = date(2020, 1, 1)

        f = filings(start_date=day, end_date=date(2020, 1, 1))
        assert isinstance(f, DailyFilings)
        assert f.date == day
        assert f.year == day.year
        assert f.quarter == day.month // 3 + 1

    def test_exact_quarter_returns_quarterly_filings(self):
        f = filings(start_date=date(2020, 1, 1), end_date=date(2020, 3, 31))
        assert isinstance(f, QuarterlyFilings)
        assert f.year == 2020
        assert f.quarter == 1

    @pytest.mark.parametrize(
        "kwargs,error",
        [
            (dict(), ValueError),
            (dict(end_date=date(2020, 1, 1)), ValueError),
            (dict(client=NetworkClient()), ValueError),
            (dict(entry_filter=lambda f: f.form_type == '10-k'), ValueError),

            # end_date assumed to be today - giving count tries to
            # make daily or quarterly filing, but will not be recognized
            (dict(count=10, client=NetworkClient()), NotImplementedError),
            (dict(count=10), NotImplementedError),
        ]
    )
    def test_bad_args_combination_raises_error(self, kwargs, error):
        with pytest.raises(error):
            filings(**kwargs)
