from secedgar.filings.daily import DailyFilings  
from secedgar.filings.company import CompanyFilings  
from secedgar.filings.filing_types import FilingType  
from secedgar.filings.quarterly import QuarterlyFilings  
from secedgar.filings.combo import ComboFilings 
from secedgar.utils import get_quarter
from datetime import date, datetime
def filings(cik_lookup=None, filing_type=None, start_date=None, end_date=date.today(), count=None, client=None, entry_filter=lambda _: True):
    # some big if tree
    if filing_type is not None:
        entry_filter = lambda x:x.form_type == filing_type
    
    if cik_lookup:
        return CompanyFilings(cik_lookup, filing_type=filing_type, start_date=start_date, end_date=end_date, count=count, client=client)
    elif not end_date:
        return DailyFilings(date=start_date, client=client, entry_filter=entry_filter)
    elif isinstance(start_date, date) and isinstance(end_date, date):
        return ComboFilings(start_date, end_date, client=client, entry_filter=entry_filter)
    else:
        raise ValueError('adafdasfda')

# Parameters


filings = MyFFancyFilingClass() <- method

filings.save()

QuarterlyFilings._get_tar()
DailyFilings._get_tar()

# 18129 KB
# 18K
# 350

'''

18000
350

1 master ~~ 50 daily

< 50 days left, grab days instead of entry filter
'''