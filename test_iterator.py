import sys
from datetime import datetime
sys.path.append("/home/retep/repos/sec-edgar/secedgar")

import secedgar.filings.daily as d

daily_filing = d.DailyFilings(datetime(2000, 12, 30), entry_filter=lambda x:x.form_type == '4')
daily_filing.save('./out')
daily_filing.extract('./out', rm_infile=False, create_subdir=False)