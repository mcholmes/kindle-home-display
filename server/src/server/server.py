from __future__ import annotations

import argparse
import logging
import sys
from datetime import time
import zoneinfo
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import path
from datetime import datetime
from pydantic import BaseModel, Field, PrivateAttr

from .cal.cal import Calendar
from .cal.event import Event
from .render.render import Renderer
from .config.config import AppConfig

# Configure logger
script_dir = path.dirname(path.abspath(__file__))
logger = logging.getLogger(__name__)
log_path = path.join(script_dir, "logs", "server.log")
logging.basicConfig(
    filename=log_path,
    format="%(asctime)s %(levelname)s - %(message)s",
    filemode="a")
logger.addHandler(logging.StreamHandler(sys.stdout))  # print logger to stdout
logger.setLevel(logging.INFO)

# Read config
CONFIG = AppConfig.from_toml(path.join(script_dir, 'config.toml'))

"""
TODO
- change pydantic to use BaseModel instead of dataclass
- validate calendars (emails in Google Cal)
- command line arguments for
         - config & api key file location
         - log dir
         - telling kindle to break loop & reboot cleanly
"""

def main():
    
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description='Generates a png image from data retrieved from a calendar.')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    # Calendar config
    display_timezone = zoneinfo.ZoneInfo(CONFIG.calendar.display_timezone) # list timezones: print(zoneinfo.available_timezones())
    days_to_show = CONFIG.calendar.days_to_show
    calendar_ids = CONFIG.calendar.ids.values()

    # Image config
    image_width = CONFIG.image.width
    image_height = CONFIG.image.height
    rotate_angle = CONFIG.image.rotate_angle # If image is rendered portrait, rotate to fit screen
    image_name = CONFIG.image.name
    
    # Server config
    server_dir = CONFIG.server.server_dir

    # Retrieve calendar events
    logger.info("Getting calendar events...")
    date_with_tz = datetime.now(display_timezone)
    cal = Calendar(calendar_ids=calendar_ids, current_date=date_with_tz, days_to_show=days_to_show)
    events = cal.get_daywise_events()

    count_events = 0
    for day in events:
        count_events += len(events[day])
    logger.info(f"  Retrieved {count_events} events across {len(events)} days")

    def sort_by_time(events: list[Event]):
        return sorted(events, key = lambda x: x.time_start or time.min)

    events_today = sort_by_time(events.get(0, []))
    events_tomorrow = sort_by_time(events.get(1, []))

    # Render Dashboard Image
    logger.info("Rendering image...")
    r = Renderer(image_width=image_width, image_height=image_height,
                 margin_x=100, margin_y=200, top_row_y=250, space_between_sections=50,
                 rotate_angle=rotate_angle
                 )

    r.render_all(
        todays_date=cal.current_date,
        weather=None,
        events_today=events_today,
        events_tomorrow=events_tomorrow)

    output_dir = script_dir if args.debug else server_dir
    output_filepath = path.join(output_dir, image_name)
    r.save_image(output_filepath)

    logger.info("   Done")

    # # Retrieve Weather Data
    # owm_api_key = api["owm_api_key"]  # OpenWeatherMap API key. Required to retrieve weather forecast.
    # lat = config["lat"] # Latitude in decimal of the location to retrieve weather forecast for
    # lon = config["lon"] # Longitude in decimal of the location to retrieve weather forecast for
    # owmModule = OWMModule()
    # current_weather, hourly_forecast, daily_forecast = owmModule.get_weather(lat, lon, owm_api_key, from_cache=True)
    # # current_weather_text=string.capwords(hourly_forecast[1]["weather"][0]["description"]),
    # # current_weather_id=hourly_forecast[1]["weather"][0]["id"],
    # # current_weather_temp=round(hourly_forecast[1]["temp"]),

if __name__ == '__main__':
    main()

class MyRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        config = Config(path.join(script_dir, 'config.ini'))
        
        if self.path == '/' + config.image_name:
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            # Open the PNG image file and send its contents as response
            main()
            with open('path/to/your/image.png', 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Not Found</h1></body></html>')

def run(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MyRequestHandler)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()