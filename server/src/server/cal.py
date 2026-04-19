import logging
from pathlib import Path

import pendulum
from pydantic import PositiveInt

from server.activity import Activity
from server.calendar_plugins.gcal import GCal

logger = logging.getLogger(__name__)


class Calendar:
    """
    Connects to a calendar provider and retrieves events as Activity objects.
    Computes the query date window from the current date and days_to_show.
    """

    def __init__(
        self,
        credentials: Path | str,
        calendar_ids: str | list[str],
        current_date: pendulum.DateTime,
        days_to_show: PositiveInt = 2,
        exclude_default_calendar: bool = False,  # noqa: FBT001, FBT002
    ):
        self.credentials = credentials
        self.calendar_ids = calendar_ids
        self.current_date = current_date
        self.days_to_show = days_to_show
        self.exclude_default_calendar = exclude_default_calendar

    @property
    def start_date(self) -> pendulum.DateTime:
        return self.current_date.start_of("day")

    @property
    def end_date(self) -> pendulum.DateTime:
        return self.start_date.add(days=self.days_to_show)

    def get_events_cal(self) -> list[Activity]:
        c = GCal(self.credentials)
        return c.get_events(
            date_from=self.start_date,
            date_to=self.end_date,
            additional_calendars=self.calendar_ids,
            exclude_default_calendar=self.exclude_default_calendar,
        )
