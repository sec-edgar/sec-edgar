import pytest
import shutil

from SECEdgar.filings import Filing
from SECEdgar.extractor import EDGARExtractor
from SECEdgar.utils.exceptions import FilingTypeError

class TestExtractor(object):
    def test_aapl_10k(self):
        f = Filing(cik='0000320193', filing_type='10-k')
        metadata = f.save("./data/original", True, "./data/extracted")
        if not metadata:
            raise AssertionError("Metadata was not returned.")
        shutil.rmtree("./data")
