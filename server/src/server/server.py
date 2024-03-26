from __future__ import annotations

import json
import logging
import sys
from datetime import time
from os import path

from pytz import timezone

from .cal.cal import Calendar
from .render.font_helper import FontFactory
from .render.render_helper import Renderer

from http.server import BaseHTTPRequestHandler, HTTPServer

logger = logging.getLogger(__name__)

def main():
    script_dir = path.dirname(path.abspath(__file__))
    # Create and configure logger
    log_path = path.join(script_dir, "logs", "server.log")
    logging.basicConfig(
        filename=log_path,
        format="%(asctime)s %(levelname)s - %(message)s",
        filemode="a")
    logger.addHandler(logging.StreamHandler(sys.stdout))  # print logger to stdout
    logger.setLevel(logging.INFO)

    # Basic configuration settings (user replaceable)
    logger.info("Getting config data")
    with open(path.join(script_dir, 'config.json')) as config_file:
        config = json.load(config_file)

    with open(path.join(script_dir, 'api_keys.json')) as api_file:
        api = json.load(api_file)

    calendar_ids = config['calendars'] # Google Calendar IDs
    display_timezone = timezone(config['displayTZ']) # list of timezones - print(pytz.all_timezones)
    calendar_days_to_show = config['numCalDaysToShow'] # Number of days to retrieve from gcal

    # Image dimensions in pixels
    image_width = config['imageWidth']
    image_height = config['imageHeight']

    # If image is rendered portrait, rotate to fit screen
    rotate_angle = config['rotateAngle']

    # Retrieve Calendar Data
    logger.info("Getting calendar data")
    cal = Calendar(calendar_ids, display_timezone, calendar_days_to_show)
    events = cal.get_daywise_events()

    count_events = 0
    for day in events:
        count_events += len(events[day])
    logger.info(f"Retrieved {count_events} events across {len(events)} days.")

    # Render Dashboard Image
    font_map = {
            "extralight": "Lexend-ExtraLight.ttf",
            "light": "Lexend-Light.ttf",
            "regular": "Lexend-Regular.ttf",
            "bold": "Lexend-Bold.ttf",
            "extrabold": "Lexend-ExtraBold.ttf",
            "weather": "weathericons-regular-webfont.ttf"
        }

    # path_to_server_image = config["path_to_server_image"]
    path_to_server_image = path.join(script_dir, "dashboard.png") # TODO: comment this for production
    r = Renderer(font_map=font_map, 
                 image_width=image_width, image_height=image_height,
                 margin_x=100, margin_y=200, top_row_y=250, spacing_between_sections=50,
                 output_filepath=path_to_server_image
                 )

    def sort_by_time(events: list[dict]):
        return sorted(events, key = lambda x: x.get("start_time", time.min))

    events_today = sort_by_time(events.get(0, []))
    events_tomorrow = sort_by_time(events.get(1, []))

    logger.info("Rendering image")
    r.render_all(
        todays_date=cal.get_current_date(),
        weather=None,
        events_today=events_today,
        events_tomorrow=events_tomorrow)

    logger.info("Completed dashboard update.")

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