import logging
from collections import defaultdict
from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from .gcal_helper import GCal
from .event import Event

logger = logging.getLogger(__name__)

"""TODO
- (day n/N) for multi-day events?
- validate inputs e.g. days_to_show > 0
"""

model_config = ConfigDict(arbitrary_types_allowed=True) # needed for zoneinfo: https://github.com/pydantic/pydantic/issues/4710

@dataclass(config=model_config)
class Calendar:
    """
    A class to connect to a calendar provider and retrieve events which can be easily rendered.
    The function of this is mostly parsing / formatting.
    The current calendar provider is Google Calendar, but this is pluggable.
    """

    calendar_ids            : str | list[str]
    display_timezone        : ZoneInfo = Field(default=ZoneInfo("Europe/London"))
    days_to_show            : int = Field(default=2, gt=0)
    exclude_default_calendar: bool = False

    # Fields computed post init
    current_date            : datetime = Field(init=False)
    start_date              : datetime = Field(init=False)
    end_date                : datetime = Field(init=False)

    def __post_init__(self):
        self.current_date   = datetime.now(self.display_timezone)
        self.start_date     = datetime.combine(self.current_date, time.min) # midnight today
        self.end_date       = self.start_date + timedelta(days=self.days_to_show)

    def get_daywise_events(self) -> dict[list[Event]]:
        """
        :return: a dict of (lists of events for a day). key=0 is today, key=1 is tomorrow, etc.

        Events within a day are unsorted.
        """

        c = GCal()
        events_unsorted = c.get_events(
            date_from = self.start_date,
            date_to = self.end_date,
            additional_calendars = self.calendar_ids,
            exclude_default_calendar = False
        )

        # Group events by date
        grouped_events = defaultdict(list)
        for event in events_unsorted:
            # max(x, 0) caters for multi-day events starting before current date.
            relative_day = max(event.get_relative_days_start(self.current_date),0) 
            grouped_events[relative_day].append(event)

        # Now we have all keys, so convert defaultdict to regular dictionary
        return dict(grouped_events)