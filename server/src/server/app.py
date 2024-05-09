import logging
from datetime import datetime, time, timedelta
from os import mkdir, path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse, PlainTextResponse

from server.activity import Activity, group_events_by_relative_day
from server.cal import Calendar
from server.config import AppConfig
from server.render import Renderer
from server.todoist import get_tasks_todoist

logger = logging.getLogger(__name__)


def sort_by_time(events: list[Activity]):
    return sorted(events, key=lambda x: x.time_start or time.min)


class App:
    config: AppConfig
    api_keys: dict[str]
    image_file_name: str = "dashboard.png"
    server_log_file_name: str = "server.log"
    device_log_file_name: str = "device.log"
    router: APIRouter = APIRouter()

    def __init__(self, config: AppConfig, api_keys: dict[str]):
        self.config = config
        self.api_keys = api_keys

        self.router.add_api_route(
            "/",
            response_class=HTMLResponse,
            endpoint=self.root,
            methods=["GET"])

        self.router.add_api_route(
            "/dashboard",
            response_class=Response,
            endpoint=self.get_dashboard_response,
            methods=["GET"],
        )

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

    def root(self) -> str:
        return f"For docs on how to use this API, go to localhost:{self.config.server.port}/docs."

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
            print(f"Creating new log directory: {log_dir}")  # noqa: T201
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

    def generate_image_and_save(self) -> None:
        events, current_date = self.get_dashboard_data()
        image = self.generate_image(events, current_date)
        output_filepath = path.join(
            self.config.server.server_dir, self.image_file_name
        )

        with open(output_filepath, "wb") as f:
            f.write(image)

    def get_dashboard_response(self) -> Response:
        events, current_date = self.get_dashboard_data()
        image = self.generate_image(events, current_date)

        return Response(content=image, media_type="image/png")

    def get_dashboard_data(self) -> tuple[dict[list[Activity]], datetime]:
        # list timezones: print(zoneinfo.available_timezones())
        display_timezone = ZoneInfo(self.config.calendar.display_timezone)
        current_date = datetime.now(display_timezone)

        tasks = self.get_tasks(current_date) # TODO: make this optional
        appointments = self.get_appointments(current_date)

        events_unsorted = tasks + appointments

        events = group_events_by_relative_day(events=events_unsorted, current_date=current_date)

        count_events = 0
        for day in events:
            count_events += len(events[day])

        log_msg = f"Retrieved {count_events} events across {len(events)} days"
        logger.debug(log_msg)

        return events, current_date

    def generate_image(self, events: dict[list[Activity]], current_date: datetime) -> bytes:

        events_today = sort_by_time(events.get(0, []))
        events_tomorrow = sort_by_time(events.get(1, []))

        r = Renderer(
            image_width=self.config.image.width,
            image_height=self.config.image.height,
            rotate_angle=self.config.image.rotate_angle,
            margin_x=100,
            margin_y=200,
            top_row_y=250,
            space_between_sections=100,
        )

        r.render_all(
            todays_date=current_date,
            weather=None,
            events_today=events_today,
            events_tomorrow=events_tomorrow,
        )

        logger.info("Rendered successfully")

        return r.get_png()

    def get_tasks(self, current_date: datetime) -> list[Activity]:
        config = self.config.tasks

        project_id = config.project_id

        date_end = current_date + timedelta(days=self.config.calendar.days_to_show)
        return get_tasks_todoist(
            api_key=self.api_keys["todoist"],
            project_id=project_id,
            date_end=date_end
            )

    def get_appointments(self, current_date: datetime) -> list[Activity]:
        config = self.config.calendar

        calendar_ids = config.ids.values()
        credentials = config.creds

        # TODO: do I really need a Calendar object? It doesn't do much any more
        cal = Calendar(
            credentials=credentials,
            calendar_ids=calendar_ids,
            current_date=current_date,
            days_to_show=config.days_to_show,
        )

        return cal.get_events_cal()

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
