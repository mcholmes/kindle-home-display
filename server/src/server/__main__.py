from __future__ import annotations

import logging
import sys
from datetime import time
from zoneinfo import ZoneInfo
from os import path
from datetime import datetime
from fastapi import FastAPI
import typer

from .cal import Calendar
from .event import Event
from .render import Renderer
from .config import AppConfig, CalendarConfig, ImageConfig


script_dir = path.dirname(path.abspath(__file__))
### Configure logger ###

logger = logging.getLogger(__name__)
log_path = path.join(script_dir, "logs", "server.log")
logging.basicConfig(
    filename=log_path,
    format="%(asctime)s %(levelname)s - %(message)s",
    filemode="a")
logger.addHandler(logging.StreamHandler(sys.stdout))  # print logger to stdout
logger.setLevel(logging.INFO)

### Read config ###
CONFIG = AppConfig.from_toml(path.join(script_dir, 'config.toml'))

"""
TODO
- command line arguments for
         - config & api key file location
         - log dir
         - telling kindle to break loop & reboot cleanly

CLI:

dashboard start
dashboard stop
dashboard once
dashboard command break
dashboard --help | -h
dashboard --version
dashboard --debug

"""

app = FastAPI()


@app.get("/")
def read_root() -> str:
    return "TODO: help text here"

@app.get("/logs")
def get_logs():
    return "TODO: log file here"

@app.get("/dashboard")
def run_once(debug=False, save_img=False):

    display_timezone = ZoneInfo(CONFIG.calendar.display_timezone) # list timezones: print(zoneinfo.available_timezones())
    current_date = datetime.now(display_timezone)
    
    events = get_events(CONFIG.calendar, current_date)
    events_today = sort_by_time(events.get(0, []))
    events_tomorrow = sort_by_time(events.get(1, []))
    
    image = generate_image(CONFIG.image, current_date, events_today, events_tomorrow)

    if save_img:
        output_dir = script_dir if debug else CONFIG.server.server_dir
        output_filepath = path.join(output_dir, "dashboard.png")
        with open(output_filepath, "wb") as f: 
            f.write(image)

    logger.info("   Done")

def sort_by_time(events: list[Event]):
        return sorted(events, key = lambda x: x.time_start or time.min)

def get_events(config: CalendarConfig, current_date: datetime) -> list[Event]:
    logger.info("Getting calendar events...")
    
    calendar_ids = config.ids.values()
    
    cal = Calendar(
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

def generate_image(config: ImageConfig, current_date: datetime, events_today: list[Event], events_tomorrow: list[Event]):
    
    logger.info("Rendering image...")
    r = Renderer(image_width=CONFIG.image.width, 
                 image_height=CONFIG.image.height,
                 rotate_angle=CONFIG.image.rotate_angle,
                 margin_x=100, margin_y=200, top_row_y=250, space_between_sections=50
                 )

    r.render_all(
        todays_date=current_date,
        weather=None,
        events_today=events_today,
        events_tomorrow=events_tomorrow)
    
    return r.get_png()

def main(config_dir: str):
    run_once(debug=True, save_img=True)

if __name__ == "__main__":
    typer.run(main)
