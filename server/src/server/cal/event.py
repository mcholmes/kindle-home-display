from pydantic import BaseModel, Field, PrivateAttr
from datetime import date, datetime, timedelta, time
from typing import Optional


class Event(BaseModel):
    """
    Data exchange format for calendar events
    """

    summary         : str
    date_start      : date
    date_end        : Optional[date] = Field(default=None) # if none then it's all-day. if > start_date, then multi-day
    time_start      : Optional[time] = Field(default=None) # if none then it's all-day.
    time_end        : Optional[time] = Field(default=None) # mandatory if start_time is populated
    description     : Optional[str] = Field(default=None)
    location        : Optional[str] = Field(default=None)

    def __post_init__(self):
        if self.time_end is not None:
            assert self.time_start is not None

        # TODO: fix this assertion error
        # if self.date_end is not None:
        #     assert self.date_start < self.date_end
            #  assert self.date_start < today()

    @classmethod
    def from_datetimes(cls, 
                             summary: str, 
                             dt_start: datetime, dt_end: datetime | None, 
                             description: str | None, location: str | None):

        return cls(
            date_start=cls.datetime_to_date(dt_start),
            date_end=cls.datetime_to_date(dt_end),
            time_start=cls.datetime_to_time(dt_start),
            time_end=cls.datetime_to_time(dt_end),
            summary=summary,
            description=description,
            location=location)

    @classmethod
    def datetime_to_time(cls, x: datetime | date) -> time:
        if isinstance(x, datetime): 
            return x.time()
        elif isinstance(x, date):
            return None
        else:
            err = f"Input must be of type datetime or date, not {type(x)}"
            raise ValueError(err)
    
    @classmethod
    def datetime_to_date(cls, dt: datetime | date) -> date:
        """
        This is tricky because of how the standard library treats dates and datetimes.
        See https://github.com/python/mypy/issues/9015

        if d is a date, and dt is a datetime:
            isinstance(d, datetime)     # False
            isinstance(dt, datetime)    # True
            isinstance(d, date)         # True
            isinstance(dt, date)        # True
        """
        if isinstance(dt, datetime):
            # This has to come first in the check because isinstance(my_datetime, date) = True!
            return dt.date()
        elif isinstance(dt, date):
            return dt
        else:
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

    