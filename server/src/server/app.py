import logging
from os import path
from datetime import time
from zoneinfo import ZoneInfo
from datetime import datetime

from fastapi import APIRouter, Response

from .cal import Calendar
from .event import Event
from .render import Renderer
from .config import AppConfig

logger = logging.getLogger(__name__)

def sort_by_time(events: list[Event]):
    return sorted(events, key = lambda x: x.time_start or time.min)

class App():

    config: AppConfig
    image_name: str = "dashboard.png"
    router: APIRouter = APIRouter()

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.router.add_api_route("/logs", self.get_logs, methods=["GET"])
        self.router.add_api_route("/dashboard", response_class=Response, endpoint=self.run_once, methods=["GET"])
    
    def get_logs(self, limit: int = None) -> str:
        
        # TODO: too implicit? better to explicitly set the log dir on init?
        log_paths = [handler.baseFilename for handler in logger.handlers if isinstance(handler, logging.FileHandler)]

        if len(log_paths) == 0:
            return "No log file found"
        else:
            with open(log_paths[0]) as f:
                output = f.read()

        # TODO: replace dummy output, handle when no file is present
        # output = """log1
        #                 log2
        #                 log3""".splitlines()
        
        log_array = [x.strip() for x in output]
        
        if limit is not None:
            logs = log_array[-limit:] # last N elements
        else:
            logs = log_array
        
        return "\n".join(logs)

    def run_once(self, save_img=False) -> Response:

        display_timezone = ZoneInfo(self.config.calendar.display_timezone) # list timezones: print(zoneinfo.available_timezones())
        current_date = datetime.now(display_timezone)
        
        events = self.get_events(current_date)
        events_today = sort_by_time(events.get(0, []))
        events_tomorrow = sort_by_time(events.get(1, []))
        
        image: bytes = self.generate_image(current_date, events_today, events_tomorrow)

        if save_img:
            output_filepath = path.join(self.config.server.server_dir, self.image_name)
            with open(output_filepath, "wb") as f: 
                f.write(image)

        logger.info("Done")
        
        return Response(content=image, media_type="image/png")

    def get_events(self, current_date: datetime) -> list[Event]:
        
        logger.info("Getting calendar events...")
        
        config = self.config.calendar

        calendar_ids = config.ids.values()
        credentials = config.creds

        cal = Calendar(
            credentials=credentials,
            calendar_ids=calendar_ids, 
            current_date=current_date, 
            days_to_show=config.days_to_show)
        
        events = cal.get_daywise_events()

        count_events = 0
        for day in events:
            count_events += len(events[day])
        logger.info(f"  Retrieved {count_events} events across {len(events)} days")

        return events

    def get_weather():
        ...
        # owm_api_key = api["owm_api_key"]  # OpenWeatherMap API key. Required to retrieve weather forecast.
        # lat = config["lat"] # Latitude in decimal of the location to retrieve weather forecast for
        # lon = config["lon"] # Longitude in decimal of the location to retrieve weather forecast for
        # owmModule = OWMModule()
        # current_weather, hourly_forecast, daily_forecast = owmModule.get_weather(lat, lon, owm_api_key, from_cache=True)
        # # current_weather_text=string.capwords(hourly_forecast[1]["weather"][0]["description"]),
        # # current_weather_id=hourly_forecast[1]["weather"][0]["id"],
        # # current_weather_temp=round(hourly_forecast[1]["temp"]),

    def generate_image(self, current_date: datetime, events_today: list[Event], events_tomorrow: list[Event]) -> bytes:
        
        config = self.config.image

        logger.info("Rendering image...")
        r = Renderer(image_width=config.width, 
                    image_height=config.height,
                    rotate_angle=config.rotate_angle,
                    margin_x=100, margin_y=200, top_row_y=250, space_between_sections=50
                    )

        r.render_all(
            todays_date=current_date,
            weather=None,
            events_today=events_today,
            events_tomorrow=events_tomorrow)
        
        return r.get_png()