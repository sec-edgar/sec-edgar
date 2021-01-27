from datetime import date

import pytest
from secedgar.filings.combo import ComboFilings


def test_basic():
    start_date = date(2012, 1, 3)
    end_date = date(2013, 5, 3)
    _ = ComboFilings(start_date, end_date)
    return True
