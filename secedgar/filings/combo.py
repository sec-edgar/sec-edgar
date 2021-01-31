import logging
from datetime import date, timedelta

from secedgar.filings.daily import DailyFilings
from secedgar.filings.quarterly import QuarterlyFilings
from secedgar.utils import get_month, get_quarter

class ComboFilings:
    def __init__(self, start_date: date, end_date: date, client=None,
                 entry_filter=lambda _: True, balancing_point=30):
        self.start_date = start_date
        self.end_date = end_date
        self.master = QuarterlyFilings(year=self.start_date.year, quarter=get_quarter(
            self.start_date), client=client, entry_filter=entry_filter)
        self.daily = DailyFilings(date=self.start_date, client=client, entry_filter=entry_filter)
        self.balancing_point = balancing_point
        self.recompute()

    @staticmethod
    def add_quarter(year, quarter):
        if quarter == 4:
            quarter = 1
            year += 1
        else:
            quarter += 1
        return year, quarter
    def recompute(self):
        current_date = self.start_date
        self.master_date_list = []
        self.daily_date_list = []
        while current_date <= self.end_date:
            current_quarter = get_quarter(current_date)
            current_year = current_date.year
            next_year, next_quarter = self.add_quarter(current_year, current_quarter)
            next_start_quarter_date = date(next_year, get_month(next_quarter), 1)
            
            days_till_next_quarter = (next_start_quarter_date - current_date).days
            days_till_end = (self.end_date - current_date).days
            if days_till_next_quarter <= days_till_end:
                current_start_quarter_date = date(current_year, get_month(current_quarter), 1)
                if current_start_quarter_date == current_date:
                    self.master_date_list.append((current_year, current_quarter, lambda x: True))
                    current_date = next_start_quarter_date
                elif days_till_next_quarter > self.balancing_point:
                    self.master_date_list.append((current_year, current_quarter, lambda x: date(x['date_filed']) >= self.start_date))
                    current_date = next_start_quarter_date
                else:
                    while current_date < next_start_quarter_date:
                        self.daily_date_list.append(current_date)
                        current_date += timedelta(days=1)
            else:
                if days_till_end > self.balancing_point:
                    if days_till_next_quarter - 1 == days_till_end:
                        self.master_date_list.append((current_year, current_quarter, lambda x: True))
                        current_date = next_start_quarter_date
                    else:
                        self.master_date_list.append((current_year, current_quarter, lambda x: date(x['date_filed']) <= self.end_date))
                        current_date = self.end_date
                else:
                    while current_date <= self.end_date:
                        self.daily_date_list.append(current_date)
                        current_date += timedelta(days=1)
    def save(self,
             directory,
             dir_pattern=None,
             file_pattern="{accession_number}",
             download_all=False,
             daily_date_format="%Y%m%d"):
        """Save all filings between ``start_date`` and ``end_date``.

        Only filings that satisfy args given at initialization will
        be saved.

        Args:
            directory (str): Directory where filings should be stored.
            dir_pattern (str, optional): Format string for subdirectories. Defaults to None.
            file_pattern (str, optional): Format string for files. Defaults to "{accession_number}".
            download_all (bool, optional): Type of downloading system, if true downloads
                all data for each day, if false downloads each file in index.
                Defaults to False.
            daily_date_format (str, optional): Format string to use for the `{date}` pattern.
                Defaults to "%Y%m%d".
        """
        for (year, quarter, f) in self.master_date_list:
            self.master.year = year
            self.master.quarter = quarter
            self.master.entry_filter = f
            self.master.save(directory=directory,
                             dir_pattern=dir_pattern,
                             file_pattern=file_pattern,
                             download_all=download_all)

        for d in self.daily_date_list:
            self.daily.date = d
            self.daily.save(directory=directory,
                            dir_pattern=dir_pattern,
                            file_pattern=file_pattern,
                            download_all=download_all,
                            date_format=daily_date_format)
