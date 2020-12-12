import sys
from datetime import datetime
sys.path.append("/home/retep/repos/sec-edgar/secedgar")

import secedgar.filings.daily as d

date = datetime(2003,7,15)
inst = d.DailyFilings(date)
for i in range(3):
    print('RUN', i+1)
    inst.save('./out')