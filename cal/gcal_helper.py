from datetime import datetime, date, time
import pickle
from gcsa.google_calendar import GoogleCalendar
from gcsa import event
import logging
import pathlib
import os

from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']

class GCal:
    """
    Manages connections to Google Calendar and facilitates extractio of events.

    TODO:
    - implement timezone logic
    """

    def __init__(self):        
        current_path = str(pathlib.Path(__file__).parent.absolute())
        creds_path = os.path.join(current_path, "credentials_service.json")
        token_path = os.path.join(current_path, "token.pickle")
        
        if not self.is_token_valid(token_path):
            logger.info("Invalid token, regenerating.")
            self.generate_token(creds_path=creds_path, token_path=token_path)

        self.calendar = self.create_calendar_service_user(creds_path)
        # self.calendar = self.create_calendar_oauth(creds_path)
        
        self.available_calendars = self.get_available_calendars()

    @staticmethod
    def is_token_valid(token_path):

        if not os.path.exists(token_path):
            return False
        else:
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
            raise ValueError("No calendars are available. If you're using a calendar shared to a GCP service account, then run `accept_shared_calendar(calendar_id)` first.")

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
            raise ValueError(f"No calendars to validate.")
        
        if (self.available_calendars is None) or len(self.available_calendars) == 0:
            raise ValueError(f"No calendars available.")

        invalid_calendars = []
        for calendar in calendars_to_validate:
            if calendar not in self.available_calendars:
                invalid_calendars.append(calendar)

        if len(invalid_calendars) > 0:        
            raise ValueError(f"Invalid calendars: {", ".join(invalid_calendars)}. Available calendars are: {", ".join(self.available_calendars)}")

    def query_calendar_events(self, id:str = None, date_from:datetime = None, date_to:datetime = None):
        # Defaults to primary if no argument given
        if id is None:
            response = self.calendar.get_events(single_events=True, time_min=date_from, time_max=date_to)
        else:
            response = self.calendar.get_events(single_events=True, calendar_id=id, time_min=date_from, time_max=date_to)

        return list(response)

    @staticmethod
    def is_event_allday(start: datetime, end: datetime) -> bool:
        delta = end - start
        return delta.days == 1 # an all-day event on 2024-03-08 is represented in google calendar as ending on 2024-03-09 (date only, no time)

    @staticmethod
    def is_event_multiday(start: datetime, end: datetime) -> bool:
        delta = end - start
        return delta.days > 1

    @staticmethod
    def get_time(x):
        if isinstance(x, datetime):
            return x.time()
        elif isinstance(x, date):
            return None
        elif isinstance(x, time):
            return x
        else:
            raise ValueError("Input must be a datetime, date object, or time")

    @staticmethod
    def to_date(x):
        if isinstance(x, datetime): # a date is a 
            return x.date()
        elif isinstance(x, date):
            return x
        else:
            ValueError(f"Can't convert {type(x)} to date.")

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

        d = {
            "start_date"    : self.to_date(start), # always populated
            "end_date"      : end_date, # only populated if multi-day
            "start_time"    : self.get_time(start), # None for all-day events
            "end_time"      : self.get_time(end), # None for all-day events
            "summary"       : e.summary + summary_suffix, 
            "description"   : e.description, 
            "location"      : e.location
        }

        return d
            
    def get_events(self, date_from: datetime, date_to: datetime, additional_calendars = None, exclude_default_calendar: bool = False):
        
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
                    raise ValueError("No calendars specified.")
                self.validate_calendars(additional_calendars) # will throw error if an invalid calendar is detected
                for id in additional_calendars:
                    events.extend(self.query_calendar_events(id=id, date_from=date_from, date_to=date_to))
            else:
                self.logger.warning(f"Invalid input for additional calendars. Expected str or list[str], but got {type(additional_calendars)}.")
    
        return [self.event_to_dict(event) for event in events] 



# g = GCal()


# today_start = datetime.combine(datetime.today(), datetime.min.time())
# tomorrow_end = datetime.combine(today_start + timedelta(days=1), datetime.max.time())

# print(today_start, tomorrow_end)

# cals = [
#     "r45mcf74fb3fmv84v108q3hsgjvi46ds@import.calendar.google.com", # holmbergs todoist
#     "10a2dd68e51bb17689c7ccf4f4722d1f445c59c86430577b425c33ccee27be2e@group.calendar.google.com" # holmbergs shared cal
# ]

# events = g.get_events(date_from=today_start, date_to=tomorrow_end, additional_calendars=cals, exclude_default_calendar=False)

# for d in events:
#     print("{")
#     for key, value in d.items():
#         print(f"    '{key}': '{value}'")
#     print("}")
    

