from __future__ import annotations

import argparse
import logging
import sys
from datetime import time
import zoneinfo
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import path

from configparser import ConfigParser

from .cal.cal import Calendar
from .cal.event import Event
from .render.render import Renderer

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


"""
TODO
- better datetime handling: https://pypi.org/project/datetype/
- command line arguments for
         - config & api key file location
         - log dir
         - telling kindle to break loop & reboot cleanly


"""


def main():

    # Parse CLI arguments
    parser = argparse.ArgumentParser(description='Generates a png image from data retrieved from a calendar.')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    """ 

    """
    args = parser.parse_args()    



    logger.info("Getting config data")
    config = ConfigParser()
    config.read(path.join(script_dir, 'config.ini'))


    # Calendar config
    display_timezone = zoneinfo.ZoneInfo(config.get("calendar", "display_timezone")) # list timezones: print(zoneinfo.available_timezones())
    days_to_show = config.getint("calendar", "days_to_show")
    calendar_ids = config.get("calendar_ids", "holmbergs")

    # Image config
    image_width = config.getint("image", "width")
    image_height = config.getint("image", "height")
    rotate_angle = config.getint("image", "rotate_angle") # If image is rendered portrait, rotate to fit screen

    # Output config
    image_name = config.get("output", "image_name")
    server_dir = config.get("output", "server_dir")

    # Retrieve calendar events
    logger.info("Getting calendar events...")
    cal = Calendar(calendar_ids=calendar_ids, display_timezone=display_timezone, days_to_show=days_to_show)
    events = cal.get_daywise_events()

    count_events = 0
    for day in events:
        count_events += len(events[day])
    logger.info(f"  Retrieved {count_events} events across {len(events)} days")

    # Render Dashboard Image
    font_map = {
            "extralight": "Lexend-ExtraLight.ttf",
            "light": "Lexend-Light.ttf",
            "regular": "Lexend-Regular.ttf",
            "bold": "Lexend-Bold.ttf",
            "extrabold": "Lexend-ExtraBold.ttf",
            "weather": "weathericons-regular-webfont.ttf"
        }

    output_dir = script_dir if args.debug else server_dir
    output_filepath = path.join(output_dir, image_name)
    
    r = Renderer(font_map=font_map,
                 image_width=image_width, image_height=image_height,
                 margin_x=100, margin_y=200, top_row_y=250, space_between_sections=50,
                 output_filepath=output_filepath,
                 rotate_angle=rotate_angle
                 )

    def sort_by_time(events: list[Event]):
        return sorted(events, key = lambda x: x.time_start or time.min)

    events_today = sort_by_time(events.get(0, []))
    events_tomorrow = sort_by_time(events.get(1, []))

    logger.info("Rendering image...")
    r.render_all(
        todays_date=cal.current_date,
        weather=None,
        events_today=events_today,
        events_tomorrow=events_tomorrow)

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
        if self.path == '/dashboard.png':
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            # Open the PNG image file and send its contents as response
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
