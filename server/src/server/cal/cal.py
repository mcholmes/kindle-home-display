"""
If using Google Calendar, make sure you have both the credentials.json and token.pickle in the same folder as this file.
If not, run quickstart.py first.
"""

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta

from cal.gcal_helper import GCal
from pytz import timezone

# from dataclasses import dataclass

logger = logging.getLogger(__name__)

class Calendar:

    """
    A class to connect to a calendar provider and retrieve events which can be easily rendered.
    The function of this is mostly parsing / formatting.
    The current calendar provider is Google Calendar, but this is pluggable.
    """

    def __init__(self, calendar_list: list, display_timezone: timezone, num_days_to_show: int):

        self.num_days_to_show = num_days_to_show
        self.display_timezone = display_timezone
        self.current_date    = datetime.now(display_timezone)
        self.cal_start_date  = display_timezone.localize(
            datetime.combine(self.current_date, datetime.min.time())
            )
        self.cal_end_date    = display_timezone.localize(
            datetime.combine(self.current_date + timedelta(days=num_days_to_show-1), datetime.max.time())
            )

        self.calendar_list = calendar_list

    @staticmethod
    def get_short_time(dt_object: datetime) -> str:

        if dt_object is None:
            return None
        if not isinstance(dt_object, datetime):
            ValueError(f"Can't get short time from an object of type {type(dt_object)}")

        datetime_str = ''
        if dt_object.minute > 0:
            datetime_str = f'.{dt_object.minute:02d}'

        if dt_object.hour == 0:
            datetime_str = f'12{datetime_str}am'
        elif dt_object.hour == 12:
            datetime_str = f'12{datetime_str}pm'
        elif dt_object.hour > 12:
            datetime_str = f'{dt_object.hour % 12!s}{datetime_str}pm'
        else:
            datetime_str = f'{dt_object.hour!s}{datetime_str}am'
        return datetime_str

    def get_current_date(self):
        return self.current_date

    def get_relative_days(self, event_date: datetime):
        delta = event_date - self.current_date.date()
        return max(delta.days, 0) # cater for multi-day events which will be returned

    @staticmethod
    def is_multiday(start: datetime, end: datetime):
        # check if event stretches across multiple days
        return start.date() != end.date()

    def get_events_unsorted(self):
        """
        Returns a single list of dicts with the following structure:
            "start_date"    : date
            "end_date"      : date
            "start_time"    : time or None
            "end_time"      : time or None
            "summary"       : str
            "description"   : str
            "location"      : str

            TODO: dataclass? in helper too?
        """
        c = GCal()
        return c.get_events(
            date_from = self.cal_start_date,
            date_to = self.cal_end_date,
            additional_calendars = self.calendar_list,
            exclude_default_calendar = False
        )

        # TODO: consider timezone
        # TODO: (day n/N) for multi-day events?

    # Function to extract date from datetime object
    @staticmethod
    def get_date(dt):
        if isinstance(dt, datetime):
            return dt.date()

        if isinstance(dt, date):
            return dt

        err = "Input is not a datetime or date: {dt}"
        raise ValueError(err)

    def transform_event_for_display(self, event: dict):
        relative_day = self.get_relative_days(event["start_date"])

        detail = {}

        detail["summary"] = event["summary"]

        if event["start_time"] is not None:
            start_time = event["start_time"]
            detail["start_time"] = start_time
            detail["short_time"] = self.get_short_time(start_time)

        return relative_day, detail

    def get_daywise_events(self):
        """
        :return: a dict of (lists of events for a day). index 0 corresponds to today, 1 tomorrow, etc.

        Events within a day are unsorted.
        """

        # Initialize a defaultdict to store events grouped by date
        grouped_events = defaultdict(list)

        # Group events by date
        for event in self.get_events_unsorted():
            relative_day, detail = self.transform_event_for_display(event)
            grouped_events[relative_day].append(detail)

        # Now we have all keys, so convert defaultdict to regular dictionary
        return dict(grouped_events)
