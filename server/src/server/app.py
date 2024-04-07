from __future__ import annotations

import logging
from datetime import datetime, time
from os import mkdir, path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

from server.cal import Calendar
from server.config import AppConfig
from server.event import Event
from server.render import Renderer

logger = logging.getLogger(__name__)


def sort_by_time(events: list[Event]):
    return sorted(events, key=lambda x: x.time_start or time.min)


class App:
    config: AppConfig
    image_file_name: str = "dashboard.png"
    server_log_file_name: str = "server.log"
    device_log_file_name: str = "device.log"
    router: APIRouter = APIRouter()

    def __init__(self, config: AppConfig):
        self.config = config

        self.router.add_api_route(
            "/dashboard",
            response_class=Response,
            endpoint=self.run_once,
            methods=["GET"],
        )

        # TODO: send a signal to device to break out of its check loop
        # self.router.add_api_route("/break/check", endpoint=self.check_break, methods=["GET"])
        # self.router.add_api_route("/break/set_true", endpoint=self.set_break_true, methods=["GET"])
        # self.router.add_api_route("/break/set_false", endpoint=self.set_break_false, methods=["GET"])

        self.router.add_api_route(
            "/logs/server",
            response_class=PlainTextResponse,
            endpoint=self.get_server_logs,
            methods=["GET"],
        )
        self.router.add_api_route(
            "/logs/device",
            response_class=PlainTextResponse,
            endpoint=self.get_device_logs,
            methods=["GET"],
        )
        # TODO: add a POST for device to send its logs back to server

    def check_break(self) -> bool:
        """
        For device to check if it should break from its infinite loop.
        """
        ...

    def configure_logging(self, log_level: str, log_to_console: bool = False):
        """Reconfigure the ROOT logger, not the module's logger"""
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        h_format = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s :: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(h_format)
            root_logger.addHandler(console_handler)

        log_dir = self.config.server.server_dir
        log_path = path.join(log_dir, self.server_log_file_name)
        if not path.exists(log_dir):
            print(f"Creating new log directory: {log_dir}")
            mkdir(log_dir)

        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(h_format)
        root_logger.addHandler(file_handler)

    def get_logs(self, file_name) -> str:
        log_path = path.join(self.config.server.server_dir, file_name)
        if path.exists(log_path):
            with open(log_path) as f:
                output = f.read()
        else:
            return "No log file found"

        return output

    def get_server_logs(self) -> str:
        return self.get_logs(self.server_log_file_name)

    def get_device_logs(self) -> str:
        return self.get_logs(self.device_log_file_name)

    def run_once(self, save_img=False) -> Response:
        # list timezones: print(zoneinfo.available_timezones())
        display_timezone = ZoneInfo(self.config.calendar.display_timezone)
        current_date = datetime.now(display_timezone)

        events = self.get_events(current_date)
        events_today = sort_by_time(events.get(0, []))
        events_tomorrow = sort_by_time(events.get(1, []))

        image: bytes = self.generate_image(current_date, events_today, events_tomorrow)

        if save_img:
            output_filepath = path.join(
                self.config.server.server_dir, self.image_file_name
            )
            with open(output_filepath, "wb") as f:
                f.write(image)

        logger.info("Rendered successfully")
        return Response(content=image, media_type="image/png")

    def get_events(self, current_date: datetime) -> list[Event]:
        config = self.config.calendar

        calendar_ids = config.ids.values()
        credentials = config.creds

        cal = Calendar(
            credentials=credentials,
            calendar_ids=calendar_ids,
            current_date=current_date,
            days_to_show=config.days_to_show,
        )

        events = cal.get_daywise_events()

        count_events = 0
        for day in events:
            count_events += len(events[day])

        log_msg = f"Retrieved {count_events} events across {len(events)} days"
        logger.debug(log_msg)

        return events

    def get_weather():
        ...
        # owm_api_key = api["owm_api_key"]  # OpenWeatherMap API key. Required to retrieve weather forecast.
        # lat = config["lat"] # Latitude in decimal of the location to retrieve weather forecast for
        # lon = config["lon"] # Longitude in decimal of the location to retrieve weather forecast for
        # owmModule = OWMModule(owm_api_key)
        # current_weather, hourly_forecast, daily_forecast = owmModule.get_weather(lat, lon, from_cache=True)
        # # current_weather_text=string.capwords(hourly_forecast[1]["weather"][0]["description"]),
        # # current_weather_id=hourly_forecast[1]["weather"][0]["id"],
        # # current_weather_temp=round(hourly_forecast[1]["temp"]),

    def generate_image(
        self,
        current_date: datetime,
        events_today: list[Event],
        events_tomorrow: list[Event],
    ) -> bytes:
        config = self.config.image

        r = Renderer(
            image_width=config.width,
            image_height=config.height,
            rotate_angle=config.rotate_angle,
            margin_x=100,
            margin_y=200,
            top_row_y=250,
            space_between_sections=50,
        )

        r.render_all(
            todays_date=current_date,
            weather=None,
            events_today=events_today,
            events_tomorrow=events_tomorrow,
        )

        return r.get_png()
