import logging
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse, PlainTextResponse

from server.activity import Activity, group_events_by_relative_day, sort_by_time
from server.cal import Calendar
from server.config import AppConfig
from server.render import Renderer
from server.todoist import get_tasks_todoist

logger = logging.getLogger(__name__)

class App:
    config: AppConfig

    def __init__(self, config: AppConfig):
        self.config = config

    def get_logs(self, file_name) -> str:
        logs = Path(self.config.server.server_dir) / file_name
        try:
            with Path.open(logs) as f:
                output = f.read()
        except FileNotFoundError:
            output = f"No log file found at {logs}."

        return output

    def get_server_logs(self) -> str:
        return self.get_logs(self.config.server.server_log_file_name)

    def get_device_logs(self) -> str:
        # TODO: this is unused for now. Implement a way for the device to send logs back to the server
        return self.get_logs(self.config.server.device_log_file_name)

    def generate_image_and_save(self) -> None:
        events, current_date = self.get_dashboard_data()
        image = self.generate_image(events, current_date)
        output_filepath = Path(self.config.server.server_dir) / self.config.server.image_name

        with Path.open(output_filepath, "wb") as f:
            f.write(image)

    def get_dashboard_response(self) -> Response:
        events, current_date = self.get_dashboard_data()
        image = self.generate_image(events, current_date)

        return Response(content=image, media_type="image/png")

    def get_dashboard_data(self) -> tuple[dict[list[Activity]], datetime]:
        # list timezones: print(zoneinfo.available_timezones())
        display_timezone = ZoneInfo(self.config.calendar.display_timezone)
        current_date = datetime.now(display_timezone)

        logger.debug("Getting data in parallel...")

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_tasks = executor.submit(
                self.get_tasks, current_date
            )  # TODO: make this optional depending on config.toml
            future_appointments = executor.submit(self.get_appointments, current_date)

            # Wait for both API calls to complete
            wait([future_tasks, future_appointments])

            tasks = future_tasks.result()
            appointments = future_appointments.result()

        events_unsorted = tasks + appointments
        events_filtered = [event for event in events_unsorted if not event.ended_over_an_hour_ago]
        events = group_events_by_relative_day(events=events_filtered, current_date=current_date)

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
            margin_x=self.config.image.margin_x,
            margin_y=self.config.image.margin_x,
            top_row_y=250,
            space_between_sections=100,
        )

        r.render_all(
            todays_date=current_date,
            events_today=events_today,
            events_tomorrow=events_tomorrow,
        )

        logger.info("Rendered successfully")

        return r.get_png()

    def get_tasks(self, current_date: datetime) -> list[Activity]:
        config = self.config.tasks

        project_id = config.project_id
        date_end = current_date + timedelta(days=self.config.calendar.days_to_show)
        return get_tasks_todoist(api_key=self.config.api_keys["todoist"], project_id=project_id, date_end=date_end)

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

class AppServer(App):

    router: APIRouter = APIRouter()

    def __init__(self, config: AppConfig):
        self.config = config
        self.configure_routes()

    def configure_routes(self):
        self.router = APIRouter()
        self.router.add_api_route(
            "/",
            response_class=HTMLResponse,
            endpoint=self.root, methods=["GET"]
            )

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

        logger.debug("Started server.")
        # TODO: add a POST for device to send its logs back to server

    def root(self) -> str:
        return f"For docs on how to use this API, go to localhost:{self.config.server.port}/docs."
