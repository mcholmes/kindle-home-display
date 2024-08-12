from collections import defaultdict
from datetime import date, datetime, time, timezone, timedelta
from typing import Literal, Optional, Union

from pydantic import BaseModel, ValidationError, ValidationInfo, field_validator


class Activity(BaseModel):
    """
    Data exchange format for tasks & calendar events (or anything else that has a date).
    """

    activity_type: Literal['event', 'task']
    summary: str
    date_start: date
    date_end: Optional[date] = None  # if none then all-day. if > start_date, then multi-day
    time_start: Optional[time] = None  # if none then all-day. if populated without end time, then it's a point in time
    time_end: Optional[time] = None
    description: Optional[str] = None
    location: Optional[str] = None

    @field_validator('time_end')
    def validate_time_end(cls, time_end, info: ValidationInfo):  # noqa: N805
        time_start = info.data.get('time_start')
        if time_end is not None and time_start is None:
            error_msg = "time_start must be provided if time_end is specified"
            raise ValueError(error_msg)
        return time_end

    @field_validator('date_end')
    def validate_date_end(cls, date_end, info: ValidationInfo):  # noqa: N805
        date_start = info.data.get('date_start')
        if date_end is not None and date_start is not None and date_start > date_end:
            error_msg = "date_start must not be later than date_end"
            raise ValueError(error_msg)
        return date_end

    @classmethod
    def from_datetimes(
        cls,
        activity_type: str,
        summary: str,
        datetime_start: datetime,
        datetime_end: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ):
        return cls(
            activity_type=activity_type,
            date_start=datetime_to_date(datetime_start),
            date_end=datetime_to_date(datetime_end),
            time_start=datetime_to_time(datetime_start),
            time_end=datetime_to_time(datetime_end),
            summary=summary,
            description=description,
            location=location,
        )

    @property
    def ends_today(self) -> bool:
        today = datetime.now(tz=timezone.utc).date()
        return (self.date_end is None and self.date_start == today) or self.date_end == today

    @property
    def ended_over_an_hour_ago(self) -> bool:
        hour_ago = (datetime.now(tz=timezone.utc) - timedelta(hours=1)).time()

        return self.ends_today and not self.is_all_day and (
            (self.time_end is not None and self.time_end <= hour_ago) or
            (self.time_end is None and self.time_start <= hour_ago)
        )

    @property
    def is_multi_day(self) -> bool:
        """
        A multi-day event is one that starts on one day and ends on another.
        """
        return (self.date_end is not None) and (self.date_start != self.date_end)

    @property
    def is_all_day(self) -> bool:
        """
        An all-day event is one that begins and ends on the same day, without a defined start/end time.
        """
        return self.time_start is None

    @property
    def time_start_short(self) -> str:
        return calculate_short_time(self.time_start)

    @property
    def time_end_short(self) -> str:
        return calculate_short_time(self.time_end)

    def get_relative_days_start(self, date_to_compare: datetime):
        # Multi-day events which start before the comparison date will return a negative value
        delta = self.date_start - datetime_to_date(date_to_compare)
        return delta.days


def datetime_to_time(dt: Union[datetime, date]) -> time:

    if dt is None:
        return None

    if isinstance(dt, datetime):
        return dt.time()

    if isinstance(dt, date):
        return None

    err = f"Input must be of type datetime or date, not {type(dt)}"
    raise TypeError(err)

def datetime_to_date(dt: Union[datetime, date]) -> date:
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
    raise TypeError(err)

def calculate_short_time(dt_object: Union[datetime, time]) -> str:
    if dt_object is None:
        return None
    if not isinstance(dt_object, (datetime, time)):
        err = f"Can't get short time from an object of type {type(dt_object)}"
        raise TypeError(err)

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
