import sys
from datetime import datetime
sys.path.append("/home/retep/repos/sec-edgar/secedgar")

import secedgar.filings.master as d

day = datetime(2000, 8, 14)
daily_filing = d.MasterFilings(year=2000, quarter=3, entry_filter=lambda x:x.form_type == '4')
# daily_filing = d.DailyFilings(day, entry_filter=lambda x:x.form_type == '4')
daily_filing.save('./out', download_all=False)
daily_filing.extract('./out', rm_infile=False, create_subdir=True)