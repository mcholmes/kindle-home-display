import logging
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from gcsa.event import Event, Visibility
from gcsa.google_calendar import GoogleCalendar
from google.oauth2 import service_account
from pydantic import ValidationError

from server.activity import Activity

logger = logging.getLogger(__name__)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.WARNING)

SCOPES = ["https://www.googleapis.com/auth/calendar"]
USE_SERVICE_ACCOUNT = True


class GCal:
    """
    Manages connections to Google Calendar and facilitates extraction of events.
    """

    def __init__(self, creds_path: Path):

        if not Path.exists(creds_path):
            err = f"No credentials file found at {creds_path}"
            raise FileNotFoundError(err)

        self.calendar = self.create_calendar(creds_path)
        self.available_calendars = self.get_available_calendars()

    def get_available_calendars(self):

        """
        Returns a dict of available calendars.
        Note that the service user's primary calendar is not included in this list.
        """

        available_calendars = {
            c.calendar_id: c.summary_override for c in self.calendar.get_calendar_list()
        }
        if len(available_calendars) == 0:
            err = """No calendars are available.
            If you're using a calendar shared to a GCP service account,
            then first run `accept_shared_calendar(calendar_id)`."""
            raise ValueError(err)

        return available_calendars

    def accept_shared_calendar(self, calendar_id):
        """Only needed for service user.
        TODO: surface this to CLI?"""
        # https://issuetracker.google.com/issues/148804709#comment2
        calendar_list_entry = {"id": calendar_id}
        self.calendar.service.calendarList().insert(body=calendar_list_entry).execute()

    @staticmethod
    def create_calendar(creds_path):
        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=SCOPES
        )

        return GoogleCalendar(credentials=creds, read_only=True)

    def get_events(
        self,
        date_from: datetime,
        date_to: datetime,
        calendars: str | list | None = None,
        include_default_calendar: bool = False,  # noqa: FBT001, FBT002
    ) -> list[Activity]:
        """
        Queries a given calendar API and converts responses into Activity class.
        Defaults to primary if no calendar specified.

        For gcsa API ref see https://google-calendar-simple-api.readthedocs.io/en/latest/code/event.html
        """

        msg = f"Retrieving events between {date_from.isoformat()} and {date_to.isoformat()}..."
        logger.debug(msg)

        # Make sure calendars is a list
        if isinstance(calendars, str):
            calendars = [calendars]

        # Early return if no calendars to query
        if (len(calendars) == 0 or calendars is None) and not include_default_calendar:
            logger.warning("No calendars given, and default calendar is excluded. Skipping fetch.")
            return []

        # Set up list of calendars to query
        primary_calendar = self.calendar.default_calendar # 'primary' alias
        if include_default_calendar:
            logger.debug("Will fetch events from primary calendar")
            calendars.append(primary_calendar)

        # Get responses from the API
        responses: list[Event] = []

        for cal_id in calendars:
            if (cal_id != primary_calendar) and (cal_id not in self.available_calendars):
                warn_msg = f"Calendar ID {cal_id} not found in available calendars, skipping."
                logger.warning(warn_msg)
            else:
                logger.debug(f"Fetching events from calendar {cal_id}...")
                response = self.calendar.get_events(
                    single_events=True,
                    calendar_id=cal_id,
                    time_min=date_from,
                    time_max=date_to,
                )

                len_before = len(responses)

                responses.extend(response)

                count_responses = len(responses) - len_before # response is a generator, so don't exhaust it early
                logger.debug(f"Fetched {count_responses} from calendar {cal_id}") 

        # Convert to Activities
        events = []
        for r in responses:

            if r.visibility == Visibility.PRIVATE:  # noqa: SIM108
                summary = "-- Private Event --"
            else:
                summary = r.summary or "-- No Title --"

            try:
                events.append(Activity.from_datetimes(
                        activity_type="event",
                        summary=summary,
                        datetime_start=r.start,
                        datetime_end=r.end,
                        description=r.description,
                        location=r.location,
                    )
                )

            except ValidationError as ex:
                logger.exception(f"Error creating activity from event {r.id}: {ex}")
                logger.debug(f"Failed event data: {r}")

        return events
