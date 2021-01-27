from secedgar.filings import QuarterlyFilings, DailyFilings
from datetime import date, timedelta
from secedgar.utils import get_quarter, get_month
import logging

class ComboFilings:
    def __init__(self, start: date, end: date, client=None,
                 entry_filter=lambda _: True):
        self.start = start
        self.end = end
        self.master = QuarterlyFilings(year=self.start.year, quarter=get_quarter(self.start), client=client, entry_filter=entry_filter)
        self.daily = DailyFilings(date=self.start, client=client, entry_filter=entry_filter)
        self.recompute()

    def recompute(self):
        self.master_date_list = []
        self.daily_date_list = []
        start_quarter = get_quarter(self.start)
        end_quarter = get_quarter(self.end)

        # if it isn't the start_date for the quarter, start at next quarter
        start_quarter_month = get_month(start_quarter)
        if date(self.start.year, start_quarter_month, 1) != self.start:
            start_quarter += 1 # TODO wrap around 4 quarters

        # First, add days between start and beginning of first quarter
        start_quarter_date = date(self.start.year, get_month(start_quarter), 1)
        current_position = self.start
        logging.debug('Segment 1 start:{}'.format(current_position.strftime('%Y%m%d')))
        logging.debug('Segment 1 end:{}'.format(start_quarter_date.strftime('%Y%m%d')))

        days_to_fetch = start_quarter_date - self.start
        if days_to_fetch < 50:
            # Grab each day
            while current_position < start_quarter_date:
                self.daily_date_list.append(current_position)
                current_position += timedelta(days=1)
        else:
            # Grab master with filter
            self.master_date_list([self.start.year, start_quarter - 1])
        
        # Then, add quarters
        current_quarter = start_quarter
        current_year = self.start.year
        while current_quarter < end_quarter or current_year < self.end.year:
            self.master_date_list.append((current_year, current_quarter))
            current_quarter += 1
            if current_quarter % 5 == 0:
                current_quarter = 1
                current_year += 1
        
        # Then, add days between last quarter and end
        current_position = date(current_year, get_month(current_quarter), 1)
        logging.debug('Segment 2 start:{}'.format(current_position.strftime('%Y%m%d')))
        logging.debug('Segment 2 end:{}'.format(self.end.strftime('%Y%m%d')))
        # TODO apply same logic to end days
        while current_position <= self.end:
            self.daily_date_list.append(current_position)
            current_position += timedelta(days=1)
    def save(self,
             directory,
             dir_pattern=None,
             file_pattern="{accession_number}",
             download_all=False,
             daily_date_format="%Y%m%d"):
        for (year, quarter) in self.master_date_list:
            self.master.year = year
            self.master.quarter = quarter
            self.master.save(directory=directory, dir_pattern=dir_pattern, file_pattern=file_pattern, download_all=download_all)
        
        for date in self.daily_date_list:
            self.daily._date = date
            self.daily.save(directory=directory, dir_pattern=dir_pattern, 
                file_pattern=file_pattern, download_all=download_all, date_format=daily_date_format)