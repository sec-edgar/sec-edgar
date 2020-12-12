import sys
from datetime import datetime
sys.path.append("/home/retep/repos/sec-edgar/secedgar")

import secedgar.filings.daily as d

daily_filing = d.DailyFilings(datetime(2018, 12, 31))
daily_filing.save('./out')
daily_filing.extract_filings()