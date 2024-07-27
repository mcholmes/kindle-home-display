from collections import defaultdict
from datetime import date, datetime, time, timedelta
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


class Activity(BaseModel):
    """
    Data exchange format for tasks & calendar events (or anything else that has a date).
    TODO: validate that
        - given time_end not None, then time_start not None
        - given date_end not None, date_start < date_end
        - date_start < today
    """
    activity_type: Literal['event', 'task']
    summary: str
    date_start: date
    date_end: Optional[date] = None  # if none then all-day. if > start_date, then multi-day
    time_start: Optional[time] = None  # if none then all-day. if populated without end time, then it's a point in time
    time_end: Optional[time] = None
    description: Optional[str] = None
    location: Optional[str] = None

    @classmethod
    def from_datetimes(
        cls,
        activity_type: str,
        summary: str,
        dt_start: datetime,
        dt_end: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ):
        return cls(
            activity_type=activity_type,
            date_start=cls.datetime_to_date(dt_start),
            date_end=cls.datetime_to_date(dt_end),
            time_start=cls.datetime_to_time(dt_start),
            time_end=cls.datetime_to_time(dt_end),
            summary=summary,
            description=description,
            location=location,
        )

    @classmethod
    def datetime_to_time(cls, dt: Union[datetime, date]) -> time:

        if dt is None:
            return None

        if isinstance(dt, datetime):
            return dt.time()

        if isinstance(dt, date):
            return None

        err = f"Input must be of type datetime or date, not {type(dt)}"
        raise TypeError(err)

    @classmethod
    def datetime_to_date(cls, dt: Union[datetime, date]) -> date:
        """
        This is tricky because of how the standard library treats dates and datetimes.
        See https://github.com/python/mypy/issues/9015

        if d is a date, and dt is a datetime:
            isinstance(d, datetime)     # False
            isinstance(dt, datetime)    # True
            isinstance(d, date)         # True
            isinstance(dt, date)        # True
        """
        if dt is None:
            return None

        if isinstance(dt, datetime):
            # This has to come first in the check because isinstance(my_datetime, date) = True!
            return dt.date()

        if isinstance(dt, date):
            return dt

        err = "Input is not a datetime or date: {dt}"
        raise ValueError(err)

    @property
    def duration(self) -> timedelta:
        if self.time_start is None or self.time_end is None:
            return None

        start_datetime = datetime.combine(self.date_start, self.time_start)
        end_datetime = datetime.combine(self.date_end, self.time_end)
        return end_datetime - start_datetime

    @property
    def is_multi_day(self) -> bool:
        return (self.date_end is not None) and (self.date_start != self.date_end)

    @property
    def is_all_day(self) -> bool:
        return (self.date_start != self.date_end) or (self.time_start is None)

    @property
    def time_start_short(self) -> str:
        return self._calculate_short_time(self.time_start)

    @property
    def time_start_end(self) -> str:
        return self._calculate_short_time(self.time_end)

    def get_relative_days_start(self, date_to_compare: datetime):
        # Multi-day events which start before the comparison date will return a negative value
        delta = self.date_start - self.datetime_to_date(date_to_compare)
        return delta.days

    @staticmethod
    def _calculate_short_time(dt_object: datetime) -> str:
        if dt_object is None:
            return None
        if not isinstance(dt_object, datetime):
            TypeError(f"Can't get short time from an object of type {type(dt_object)}")

        datetime_str = ""
        if dt_object.minute > 0:
            datetime_str = f".{dt_object.minute:02d}"

        if dt_object.hour == 0:
            datetime_str = f"12{datetime_str}am"
        elif dt_object.hour == 12:  # noqa: PLR2004
            datetime_str = f"12{datetime_str}pm"
        elif dt_object.hour > 12:  # noqa: PLR2004
            datetime_str = f"{dt_object.hour % 12!s}{datetime_str}pm"
        else:
            datetime_str = f"{dt_object.hour!s}{datetime_str}am"
        return datetime_str

def sort_by_time(events: list[Activity]):
    return sorted(events, key=lambda x: x.time_start or time.min)

def group_events_by_relative_day(events: list[Activity], current_date: datetime) -> dict[list[Activity]]:
        """
        :return: a dict of (lists of events for a day). key=0 is today, key=1 is tomorrow, etc.

        Events within a day are unsorted.
        """

        # Group events by date
        grouped_events = defaultdict(list)
        for event in events:
            # max(x, 0) caters for multi-day events starting before current date.
            relative_day = max(event.get_relative_days_start(current_date), 0)
            grouped_events[relative_day].append(event)

        # Now we have all keys, so convert defaultdict to regular dictionary
        return dict(grouped_events)
