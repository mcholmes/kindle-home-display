"""
If using Google Calendar, make sure you have both the credentials.json and token.pickle in the same folder as this file. 
If not, run quickstart.py first.
"""

from cal.gcal_helper import GCal
import logging
from datetime import timedelta, datetime, date, time
from pytz import timezone
from collections import defaultdict
# from dataclasses import dataclass

class Calendar:

    """
    A class to connect to a calendar provider and retrieve events which can be easily rendered.
    The function of this is mostly parsing / formatting.
    The current calendar provider is Google Calendar, but this is pluggable.
    """

    def __init__(self, calendar_list: list, display_timezone: timezone, num_days_to_show: int):
        self.logger = logging.getLogger('maginkdash')

        self.num_days_to_show = num_days_to_show
        self.display_timezone = display_timezone
        self.current_date    = datetime.now(display_timezone)
        self.cal_start_date  = display_timezone.localize(datetime.combine(self.current_date, datetime.min.time()))
        self.cal_end_date    = display_timezone.localize(datetime.combine(self.current_date + timedelta(days=num_days_to_show-1), datetime.max.time()))

        self.calendar_list = calendar_list

    @staticmethod
    def get_short_time(datetimeObj: datetime) -> str:

        if datetimeObj is None:
            return None
        if not isinstance(datetimeObj, datetime):
            ValueError(f"Can't get short time from an object of type {type(datetimeObj)}")

        datetime_str = ''
        if datetimeObj.minute > 0:
            datetime_str = '.{:02d}'.format(datetimeObj.minute)

        if datetimeObj.hour == 0:
            datetime_str = '12{}am'.format(datetime_str)
        elif datetimeObj.hour == 12:
            datetime_str = '12{}pm'.format(datetime_str)
        elif datetimeObj.hour > 12:
            datetime_str = '{}{}pm'.format(str(datetimeObj.hour % 12), datetime_str)
        else:
            datetime_str = '{}{}am'.format(str(datetimeObj.hour), datetime_str)
        return datetime_str

    def get_current_date(self):
        return self.current_date

    def get_relative_days(self, eventDate: datetime):
        delta = eventDate - self.current_date.date()
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
        calHelper = GCal()
        eventList = calHelper.get_events(
            date_from = self.cal_start_date, 
            date_to = self.cal_end_date, 
            additional_calendars = self.calendar_list, 
            exclude_default_calendar = False
        )
        return eventList
        # TODO: consider timezone
        # TODO: (day n/N) for multi-day events?
    
    # Function to extract date from datetime object
    @staticmethod
    def get_date(dt):
        if isinstance(dt, datetime):
            return dt.date()
        elif isinstance(dt, date):
            return dt
        else:
            ValueError("Input is not a datetime or date")

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
        grouped_events = dict(grouped_events)


        
        return grouped_events