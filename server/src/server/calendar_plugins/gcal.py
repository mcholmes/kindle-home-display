from __future__ import annotations

import logging
import os
import pickle
from typing import TYPE_CHECKING

from gcsa.google_calendar import GoogleCalendar
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow

from server.event import Event

if TYPE_CHECKING:
    from datetime import datetime

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]
USE_SERVICE_ACCOUNT = True


class GCal:
    """
    Manages connections to Google Calendar and facilitates extraction of events.
    """

    def __init__(self, creds_path):
        # Uncomment if using general oauth flow ###
        # current_path = str(pathlib.Path(__file__).parent.absolute())
        # creds_filename = 'credentials_service.json' if USE_SERVICE_ACCOUNT else 'credentials_oauth.json'
        # creds_path = os.path.join(current_path, creds_filename)
        # token_path = os.path.join(current_path, "token.pickle")
        # if not USE_SERVICE_ACCOUNT and (not self.is_token_valid(token_path)):
        #     logger.info("Invalid token, regenerating.")
        #     self.generate_oauth_token(creds_path=creds_path, token_path=token_path)
        # self.calendar = self.create_calendar_oauth(creds_path)

        if not os.path.exists(creds_path):
            err = f"No credentials file found at {creds_path}"
            raise ValueError(err)

        self.calendar = self.create_calendar_service_user(creds_path)
        self.available_calendars = self.get_available_calendars()

    @staticmethod
    def is_token_valid(token_path):
        if not os.path.exists(token_path):
            return False

        with open(token_path, "rb") as token:
            creds = pickle.load(token)

        return creds.valid

    @staticmethod
    def generate_oauth_token(creds_path, token_path):
        """
        This script needs to run first to obtain the token. Credentials.json must be in the same folder first.
        To obtain Credentials.json, follow the instructions listed in the following link.
        https://developers.google.com/calendar/api/quickstart/python
        """

        # If modifying these scopes, delete the file token.pickle.

        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(token_path):
            with open(token_path, "rb") as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, "wb") as token:
                pickle.dump(creds, token)

    def get_available_calendars(self):
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
    def create_calendar_oauth(creds_path):
        return GoogleCalendar(credentials_path=creds_path, read_only=True)

    @staticmethod
    def create_calendar_service_user(creds_path):
        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=SCOPES
        )

        return GoogleCalendar(credentials=creds, read_only=True)

    def validate_calendars(self, calendars_to_validate: list[str]):
        if (calendars_to_validate is None) or len(calendars_to_validate) == 0:
            err = "No calendars to validate."
            raise ValueError(err)

        if (self.available_calendars is None) or len(self.available_calendars) == 0:
            err = "No calendars available."
            raise ValueError(err)

        invalid_calendars = []
        # for calendar in calendars_to_validate:
        #     if calendar not in self.available_calendars:
        #         invalid_calendars.append(calendar)

        invalid_calendars = [calendar for calendar in calendars_to_validate if calendar not in self.available_calendars]

        if len(invalid_calendars) > 0:
            err = f"""Invalid calendars: {", ".join(invalid_calendars)}.
            Available calendars are: {", ".join(self.available_calendars)}"""
            raise ValueError(err)

    def query_events_api(
        self,
        calendar_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Event]:
        """
        Queries a given calendar API and converts responses into Event class.
        Defaults to primary if no calendar specified.

        For gcsa API ref see https://google-calendar-simple-api.readthedocs.io/en/latest/code/event.html
        """

        if calendar_id is None:
            response = self.calendar.get_events(
                single_events=True, time_min=date_from, time_max=date_to
            )
        else:
            response = self.calendar.get_events(
                single_events=True,
                calendar_id=calendar_id,
                time_min=date_from,
                time_max=date_to,
            )

        return [
            Event.from_datetimes(
                summary=e.summary,
                dt_start=e.start,
                dt_end=e.end,
                description=e.description,
                location=e.location,
            )
            for e in list(response)
        ]

    def get_events(
        self,
        date_from: datetime,
        date_to: datetime,
        additional_calendars: str | list | None = None,
        exclude_default_calendar: bool = False,
    ) -> list[Event]:
        min_time_str = date_from.isoformat()
        max_time_str = date_to.isoformat()

        msg = f"Retrieving events between {min_time_str} and {max_time_str}..."
        logger.debug(msg)

        events = []

        if not exclude_default_calendar:
            events_primary = self.query_events_api(date_from=date_from, date_to=date_to)
            events.extend(events_primary)

        # Convert to single-element list if it's a string
        if isinstance(additional_calendars, str):
            additional_calendars = [additional_calendars]

        if isinstance(additional_calendars, list):
            if len(additional_calendars) == 0:
                logger.warning("Empty list of calendars given.")
            else:
                self.validate_calendars(
                    additional_calendars
                )  # will throw error if an invalid calendar is detected
                for cal_id in additional_calendars:
                    events.extend(
                        self.query_events_api(
                            calendar_id=cal_id, date_from=date_from, date_to=date_to
                        )
                    )
        else:
            warn_msg = f"""Invalid input for additional calendars.
                        Expected str or list[str], but got {type(additional_calendars)}."""
            logger.warning(warn_msg)

        return events
