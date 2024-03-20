from __future__ import annotations

import logging
import os
import pathlib
import pickle
from datetime import date, datetime, time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from gcsa import event

from gcsa.google_calendar import GoogleCalendar
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']
USE_SERVICE_ACCOUNT = True

class GCal:
    """
    Manages connections to Google Calendar and facilitates extractio of events.

    TODO:
    - implement timezone logic
    """

    def __init__(self):
        current_path = str(pathlib.Path(__file__).parent.absolute())

        creds_filename = 'credentials_service.json' if USE_SERVICE_ACCOUNT else 'credentials_oauth.json'
        creds_path = os.path.join(current_path, creds_filename)
        token_path = os.path.join(current_path, "token.pickle")

        if not USE_SERVICE_ACCOUNT and (not self.is_token_valid(token_path)):
            logger.info("Invalid token, regenerating.")
            self.generate_token(creds_path=creds_path, token_path=token_path)

        self.calendar = self.create_calendar_service_user(creds_path)
        # self.calendar = self.create_calendar_oauth(creds_path)

        self.available_calendars = self.get_available_calendars()

    @staticmethod
    def is_token_valid(token_path):

        if not os.path.exists(token_path):
            return False

        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

        return creds.valid

    @staticmethod
    def generate_token(creds_path, token_path):
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
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)

    def get_available_calendars(self):
        available_calendars = {c.calendar_id: c.summary_override for c in self.calendar.get_calendar_list()}
        if len(available_calendars) == 0:
            err = """No calendars are available.
            If you're using a calendar shared to a GCP service account,
            then first run `accept_shared_calendar(calendar_id)`."""
            raise ValueError(err)

        return available_calendars

    def accept_shared_calendar(self, calendar_id):
        """ Only needed for service user """
        # https://issuetracker.google.com/issues/148804709#comment2
        calendar_list_entry = {'id': calendar_id}
        self.calendar.service.calendarList().insert(body=calendar_list_entry).execute()

    @staticmethod
    def create_calendar_oauth(creds_path):
        return GoogleCalendar(credentials_path=creds_path, read_only=True)

    @staticmethod
    def create_calendar_service_user(creds_path):
        creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)

        return GoogleCalendar(credentials=creds, read_only=True)

    def validate_calendars(self, calendars_to_validate: list[str]):
        if (calendars_to_validate is None) or len(calendars_to_validate) == 0:
            err = "No calendars to validate."
            raise ValueError(err)

        if (self.available_calendars is None) or len(self.available_calendars) == 0:
            err = "No calendars available."
            raise ValueError(err)

        invalid_calendars = []
        for calendar in calendars_to_validate:
            if calendar not in self.available_calendars:
                invalid_calendars.append(calendar)

        if len(invalid_calendars) > 0:
            err = f"""Invalid calendars: {", ".join(invalid_calendars)}.
            Available calendars are: {", ".join(self.available_calendars)}"""
            raise ValueError(err)

    def query_calendar_events(self, calendar_id:Optional[str] = None,
                              date_from:Optional[datetime] = None, date_to:Optional[datetime] = None):
        # Defaults to primary if no argument given
        if calendar_id is None:
            response = self.calendar.get_events(single_events=True,
                                                time_min=date_from, time_max=date_to)
        else:
            response = self.calendar.get_events(single_events=True, calendar_id=calendar_id,
                                                time_min=date_from, time_max=date_to)

        return list(response)

    @staticmethod
    def is_event_allday(start: datetime, end: datetime) -> bool:
        # In Google Cal, an all-day event on 2024-03-08 will end on 2024-03-09 (date only, no time)
        delta = end - start
        return delta.days == 1

    @staticmethod
    def is_event_multiday(start: datetime, end: datetime) -> bool:
        delta = end - start
        return delta.days > 1

    @staticmethod
    def get_time(x):
        if isinstance(x, datetime):
            return x.time()

        if isinstance(x, date):
            return None

        if isinstance(x, time):
            return x

        err = "Input must be a datetime, date object, or time"
        raise ValueError(err)

    @staticmethod
    def to_date(x):
        if isinstance(x, datetime): # a date is a
            return x.date()

        if isinstance(x, date):
            return x

        err = f"Can't convert {type(x)} to date."
        raise ValueError(err)

    def event_to_dict(self, e: event):
        # https://google-calendar-simple-api.readthedocs.io/en/latest/code/event.html

        start = e.start
        end = e.end

        summary_suffix = ""
        if self.is_event_multiday(start, end):
            end_date = self.to_date(end)
            # summary_suffix = f" (until {end_date})"
        else:
            end_date = None

        return {
            "start_date"    : self.to_date(start), # always populated
            "end_date"      : end_date, # only populated if multi-day
            "start_time"    : self.get_time(start), # None for all-day events
            "end_time"      : self.get_time(end), # None for all-day events
            "summary"       : e.summary + summary_suffix,
            "description"   : e.description,
            "location"      : e.location
        }

    def get_events(self, date_from: datetime, date_to: datetime,
                   additional_calendars = None, exclude_default_calendar: bool = False):

        events = []

        if not exclude_default_calendar:
            events_primary = self.query_calendar_events(date_from=date_from, date_to=date_to)
            events.extend(events_primary)

        if additional_calendars is not None:

            # Convert to single-element list if it's a string
            if isinstance(additional_calendars, str):
                additional_calendars = [additional_calendars]

            if isinstance(additional_calendars, list):
                if len(additional_calendars) == 0:
                    err = "No calendars specified."
                    raise ValueError(err)
                self.validate_calendars(additional_calendars) # will throw error if an invalid calendar is detected
                for cal_id in additional_calendars:
                    events.extend(self.query_calendar_events(calendar_id=cal_id,
                                                             date_from=date_from, date_to=date_to))
            else:
                warn_msg = f"""Invalid input for additional calendars.
                            Expected str or list[str], but got {type(additional_calendars)}."""
                self.logger.warning(warn_msg)

        return [self.event_to_dict(event) for event in events]
