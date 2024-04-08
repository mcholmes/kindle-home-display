import logging
from collections import defaultdict
from datetime import datetime, time, timedelta
from typing import Union

from pydantic import BaseModel, PositiveInt

from server.calendar_plugins.gcal import GCal

from server.event import Event

logger = logging.getLogger(__name__)

class Calendar(BaseModel):
    """
    A class to connect to a calendar provider and retrieve events which can be easily rendered.
    The function of this is mostly parsing / formatting.
    The current calendar provider is Google Calendar, but this is pluggable.
    """

    credentials: str
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

    def get_daywise_events(self) -> dict[list[Event]]:
        """
        :return: a dict of (lists of events for a day). key=0 is today, key=1 is tomorrow, etc.

        Events within a day are unsorted.
        """

        c = GCal(self.credentials)
        events_unsorted: list[Event] = c.get_events(
            date_from=self.start_date,
            date_to=self.end_date,
            additional_calendars=self.calendar_ids,
            exclude_default_calendar=self.exclude_default_calendar,
        )

        # Group events by date
        grouped_events = defaultdict(list)
        for event in events_unsorted:
            # max(x, 0) caters for multi-day events starting before current date.
            relative_day = max(event.get_relative_days_start(self.current_date), 0)
            grouped_events[relative_day].append(event)

        # Now we have all keys, so convert defaultdict to regular dictionary
        return dict(grouped_events)
