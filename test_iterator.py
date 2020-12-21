import sys
from datetime import datetime
sys.path.append("/home/retep/repos/sec-edgar/secedgar")
from timeit import default_timer as timer

import secedgar.filings.master as m
import secedgar.filings.daily as d

# daily_filing = d.DailyFilings(date=datetime(2000, 8,14), entry_filter=lambda x:x.form_type == '4')
# start = timer()
# daily_filing.save('./out', download_all=False)
# stop = timer()
# print(stop-start)
# daily_filing.save('./out', download_all=True)
# stop2 = timer()
# print(stop2-stop)

master_filing = m.MasterFilings(year=2000, quarter=3, entry_filter=lambda x:x.form_type == '4', rate_limit=8)
start = timer()
master_filing.save('./out', download_all=False)
stop = timer()
print(stop-start)
master_filing.save('./out', download_all=True)
stop2 = timer()
print(stop2-stop)
