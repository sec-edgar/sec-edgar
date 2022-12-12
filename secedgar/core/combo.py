import datetime
from functools import reduce
from typing import Union

from secedgar.client import NetworkClient
from secedgar.core.daily import DailyFilings
from secedgar.core.quarterly import QuarterlyFilings
from secedgar.exceptions import EDGARQueryError, NoFilingsError
from secedgar.utils import add_quarter, get_month, get_quarter


def fill_days(start, end, include_start=False, include_end=False):
    """Get dates for days in between start and end date.

    Args:
        start (``datetime.date``): Start date.
        end (``datetime.date``): End date.
        include_start (bool, optional): Whether or not to include start date in range.
            Defaults to False.
        include_end (bool, optional): Whether or not to include end date in range.
            Defaults to False.

    Returns:
        list of ``datetime.date``: List of dates between ``start`` and ``end``.
    """
    start_range = 0 if include_start else 1
    end_range = (end - start).days + 1 if include_end else (end - start).days
    return [start + datetime.timedelta(days=d) for d in range(start_range, end_range)]


class ComboFilings:
    """Class for retrieving all filings between specified dates.

    Args:
        start_date (Union[str, ``datetime.datetime``, ``datetime.date``], optional): Date before
            which not to fetch reports. Stands for "date after."
            Defaults to None (will fetch all filings before ``end_date``).
        end_date (Union[str, ``datetime.datetime``, ``datetime.date``], optional):
            Date after which not to fetch reports.
            Stands for "date before." Defaults to today.
        user_agent (Union[str, NoneType]): Value used for HTTP header "User-Agent" for all requests.
            If given None, a valid client with user_agent must be given.
            See the SEC's statement on
            `fair access <https://www.sec.gov/os/accessing-edgar-data>`_
            for more information.
        client (Union[NoneType, secedgar.client.NetworkClient], optional): Client to use for
            fetching data. If None is given, a user_agent must be given to pass to
            :class:`secedgar.client.NetworkClient`.
            Defaults to ``secedgar.client.NetworkClient`` if none is given.
        entry_filter (function, optional): A boolean function to determine
            if the FilingEntry should be kept. Defaults to `lambda _: True`.
            The ``FilingEntry`` object exposes 7 variables which can be
            used to filter which filings to keep. These are "cik", "company_name",
            "form_type", "date_filed", "file_name", "path", and "num_previously_valid".
        balancing_point (int): Number of days from which to change lookup method from using
            ``DailyFilings`` to ``QuarterlyFilings``. If ``QuarterlyFilings`` is used, an
            additional filter will be added to limit which days are included.
            Defaults to 30.
        kwargs: Any keyword arguments to pass to ``NetworkClient`` if no client is specified.

    .. versionadded:: 0.4.0

    Examples:
        To download all filings from January 6, 2020 until November 5, 2020, you could do following:

        .. code-block:: python

            from datetime import date
            from secedgar import ComboFilings

            combo_filings = ComboFilings(start_date=date(2020, 1, 6),
                                         end_date=date(2020, 11, 5)
            combo_filings.save('/my_directory')
    """

    def __init__(self,
                 start_date: datetime.date,
                 end_date: datetime.date,
                 user_agent: Union[str, None] = None,
                 client=None,
                 entry_filter=lambda _: True,
                 balancing_point=30,
                 **kwargs):
        self.entry_filter = entry_filter
        self.start_date = start_date
        self.end_date = end_date
        self.user_agent = user_agent
        self._client = client or NetworkClient(user_agent=user_agent, **kwargs)
        self._balancing_point = balancing_point

    @property
    def entry_filter(self):
        """A boolean function to be tested on each listing entry.

        This is tested regardless of download method.
        """
        return self._entry_filter

    @entry_filter.setter
    def entry_filter(self, fn):
        if callable(fn):
            self._entry_filter = fn
        else:
            raise ValueError('entry_filter must be a function or lambda.')

    @property
    def client(self):
        """``secedgar.client.NetworkClient``: Client to use to make requests."""
        return self._client

    @property
    def start_date(self):
        """Union([datetime.date]): Date before which no filings fetched."""
        return self._start_date

    @start_date.setter
    def start_date(self, val):
        if val:
            self._start_date = val
        else:
            self._start_date = None

    @property
    def end_date(self):
        """Union([datetime.date]): Date after which no filings fetched."""
        return self._end_date

    @end_date.setter
    def end_date(self, val):
        self._end_date = val

    @property
    def balancing_point(self):
        """int: Point after which to use ``QuarterlyFilings`` with ``entry_filter`` to get data."""
        return self._balancing_point

    def _get_quarterly_daily_date_lists(self):
        """Break down date range into combination of quarters and single dates.

        Returns:
            tuple of lists: Quarterly date list and daily date list.
        """
        # Initialize quarter and date lists
        current_date = self.start_date
        quarterly_date_list = []
        daily_date_list = []

        while current_date <= self.end_date:
            current_quarter = get_quarter(current_date)
            current_year = current_date.year
            next_year, next_quarter = add_quarter(current_year, current_quarter)
            next_start_quarter_date = datetime.date(next_year, get_month(next_quarter), 1)

            days_till_next_quarter = (next_start_quarter_date -
                                      current_date).days
            days_till_end = (self.end_date - current_date).days

            # If there are more days until the end date than there are
            # in the quarter, add
            if days_till_next_quarter <= days_till_end:
                current_start_quarter_date = datetime.date(current_year,
                                                           get_month(current_quarter), 1)
                if current_start_quarter_date == current_date:
                    quarterly_date_list.append(
                        (current_year, current_quarter, lambda x: True))
                    current_date = next_start_quarter_date
                elif days_till_next_quarter > self.balancing_point:
                    quarterly_date_list.append(
                        (current_year, current_quarter,
                         lambda x: datetime.datetime.strptime(
                             x.date_filed, '%Y-%m-%d'
                         ).date() >= self.start_date))
                    current_date = next_start_quarter_date
                else:
                    daily_date_list.extend(fill_days(start=current_date,
                                                     end=next_start_quarter_date,
                                                     include_start=True,
                                                     include_end=False))
                    current_date = next_start_quarter_date
            else:
                if days_till_end > self.balancing_point:
                    if days_till_next_quarter - 1 == days_till_end:
                        quarterly_date_list.append(
                            (current_year, current_quarter, lambda x: True))
                        current_date = next_start_quarter_date
                    else:
                        quarterly_date_list.append(
                            (current_year, current_quarter,
                             lambda x: datetime.datetime.strptime(
                                 x.date_filed, '%Y-%m-%d'
                             ).date() <= self.end_date))
                        current_date = self.end_date
                else:
                    daily_date_list.extend(fill_days(start=current_date,
                                                     end=self.end_date,
                                                     include_start=True,
                                                     include_end=True))
                    break
        return quarterly_date_list, daily_date_list

    @property
    def quarterly_date_list(self):
        """List of tuples: List of tuples with year, quarter, and ``entry_filter`` to use."""
        return self._get_quarterly_daily_date_lists()[0]  # 0 = quarterly

    @property
    def daily_date_list(self):
        """List of ``datetime.date``: List of dates for which to fetch daily data."""
        return self._get_quarterly_daily_date_lists()[1]  # 1 = daily

    def get_urls(self):
        """Get all urls between ``start_date`` and ``end_date``."""
        # Use functools.reduce for speed
        # see https://stackoverflow.com/questions/10461531/merge-and-sum-of-two-dictionaries
        def _reducer(accumulator, dictionary):
            for key, value in dictionary.items():
                accumulator[key] = accumulator.get(key, []) + value
            return accumulator

        list_of_dicts = []
        for (year, quarter, f) in self.quarterly_date_list:
            q = QuarterlyFilings(year=year,
                                 quarter=quarter,
                                 user_agent=self.user_agent,
                                 client=self.client,
                                 entry_filter=lambda x: f(x) and self.entry_filter(x))
            list_of_dicts.append(q.get_urls())

        for _date in self.daily_date_list:
            d = DailyFilings(date=_date,
                             user_agent=self.user_agent,
                             client=self.client,
                             entry_filter=self.entry_filter)
            try:
                list_of_dicts.append(d.get_urls())
            except EDGARQueryError:  # continue if no URLs available for given day
                continue

        complete_dictionary = reduce(_reducer, list_of_dicts, {})
        return complete_dictionary

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
        # Go through all quarters and dates and save filings using appropriate class
        for (year, quarter, f) in self.quarterly_date_list:
            q = QuarterlyFilings(year=year,
                                 quarter=quarter,
                                 user_agent=self.client.user_agent,
                                 client=self.client,
                                 entry_filter=lambda x: f(x) and self.entry_filter(x))
            q.save(directory=directory,
                   dir_pattern=dir_pattern,
                   file_pattern=file_pattern,
                   download_all=download_all)

        for date_ in self.daily_date_list:
            d = DailyFilings(date=date_,
                             user_agent=self.client.user_agent,
                             client=self.client,
                             entry_filter=self.entry_filter)
            try:
                d.save(directory=directory,
                       dir_pattern=dir_pattern,
                       file_pattern=file_pattern,
                       download_all=download_all,
                       date_format=daily_date_format)
            except (EDGARQueryError, NoFilingsError):  # continue if no filings for given day
                continue
