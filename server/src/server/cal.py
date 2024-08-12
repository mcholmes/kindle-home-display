import logging
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Union

from pydantic import BaseModel, PositiveInt

from server.activity import Activity
from server.calendar_plugins.gcal import GCal

logger = logging.getLogger(__name__)

class Calendar(BaseModel):
    """
    A class to connect to a calendar provider and retrieve events which can be easily rendered.
    The function of this is mostly parsing / formatting.
    The current calendar provider is Google Calendar, but this is pluggable.
    """

    credentials: Union[Path, str]
    calendar_ids: Union[str, list[str]]
    current_date: datetime
    days_to_show: PositiveInt = 2
    exclude_default_calendar: bool = False

    @property
    def start_date(self) -> datetime:
        return datetime.combine(self.current_date, time.min)  # midnight today

    @property
    def end_date(self) -> datetime:
        return self.start_date + timedelta(days=self.days_to_show)

    def get_events_cal(self) -> list[Activity]:
        c = GCal(self.credentials)
        return c.get_events(
            date_from=self.start_date,
            date_to=self.end_date,
            additional_calendars=self.calendar_ids,
            exclude_default_calendar=self.exclude_default_calendar,
        )
