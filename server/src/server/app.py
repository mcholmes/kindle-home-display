import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pendulum
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
from loguru import logger

from server.activity import Activity, group_events_by_relative_day, sort_by_time
from server.cal import Calendar
from server.config import AppConfig
from server.render import RenderConfig, Renderer
from server.todoist import get_tasks_todoist


class DataFetchError(Exception):
    """Raised when all data sources fail to fetch data."""
    pass

class App:
    """Core application logic: fetches data, renders dashboard images."""

    config: AppConfig

    def __init__(self, config: AppConfig):
        self.config = config

    def get_logs(self, file_name: str) -> str:
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
        try:
            events, current_date = self.get_dashboard_data()
            image = self.generate_image(events, current_date)
        except DataFetchError as e:
            image = self.generate_error_image(str(e))

        output_filepath = Path(self.config.server.server_dir) / self.config.server.image_name

        with Path.open(output_filepath, "wb") as f:
            f.write(image)

    def get_dashboard_response(self) -> Response:
        try:
            events, current_date = self.get_dashboard_data()
            image = self.generate_image(events, current_date)
        except DataFetchError as e:
            image = self.generate_error_image(str(e))

        return Response(content=image, media_type="image/png")

    def get_dashboard_data(self) -> tuple[dict[int, list[Activity]], pendulum.DateTime]:
        current_date = pendulum.now(self.config.calendar.display_timezone)

        logger.debug("Getting data in parallel...")

        with ThreadPoolExecutor() as executor:
            future_tasks = executor.submit(
                self.get_tasks, current_date
            )  # TODO: make this optional depending on config.toml
            future_appointments = executor.submit(self.get_appointments, current_date)

            errors = []

            try:
                tasks = future_tasks.result()
            except Exception:
                logger.exception("Failed to get tasks")
                tasks = []
                errors.append(f"Tasks error:\n{traceback.format_exc()}")

            try:
                appointments = future_appointments.result()
            except Exception:
                logger.exception("Failed to get appointments")
                appointments = []
                errors.append(f"Appointments error:\n{traceback.format_exc()}")

        if len(errors) == 2:
            raise DataFetchError("\n\n".join(errors))

        events_unsorted = tasks + appointments
        events_filtered = [event for event in events_unsorted if not event.ended_over_an_hour_ago]
        events = group_events_by_relative_day(events=events_filtered, current_date=current_date)

        count_events = 0
        for day in events:
            count_events += len(events[day])

        log_msg = f"Retrieved {count_events} events across {len(events)} days"
        logger.debug(log_msg)

        return events, current_date

    def _create_renderer(self) -> Renderer:
        cfg = self.config.image
        render_config = RenderConfig(
            image_width=cfg.width,
            image_height=cfg.height,
            rotate_angle=cfg.rotate_angle,
            margin_x=cfg.margin_x,
            margin_y=cfg.margin_y,
            top_row_y=cfg.top_row_y,
            space_between_sections=cfg.space_between_sections,
        )
        return Renderer(render_config)

    def generate_image(self, events: dict[int, list[Activity]], current_date: pendulum.DateTime) -> bytes:
        events_today = sort_by_time(events.get(0, []))
        events_tomorrow = sort_by_time(events.get(1, []))

        r = self._create_renderer()

        r.render_all(
            todays_date=current_date,
            events_today=events_today,
            events_tomorrow=events_tomorrow,
        )

        logger.info("Rendered successfully")

        return r.get_png()

    def generate_error_image(self, error_text: str) -> bytes:
        r = self._create_renderer()
        r.render_error(error_text)
        return r.get_png()

    def get_tasks(self, current_date: pendulum.DateTime) -> list[Activity]:
        config = self.config.tasks

        project_id = config.project_id
        date_end = current_date.add(days=self.config.calendar.days_to_show)
        return get_tasks_todoist(api_key=self.config.api_keys["todoist"], project_id=project_id, date_end=date_end)

    def get_appointments(self, current_date: pendulum.DateTime) -> list[Activity]:
        config = self.config.calendar

        calendar_ids = list(config.ids.values())
        credentials = config.creds

        cal = Calendar(
            credentials=credentials,
            calendar_ids=calendar_ids,
            current_date=current_date,
            days_to_show=config.days_to_show,
        )

        return cal.get_events_cal()


def create_app(config: AppConfig) -> FastAPI:
    """Create and configure a FastAPI application with all routes."""
    app = App(config)
    fastapi_app = FastAPI()

    @fastapi_app.get("/", response_class=HTMLResponse)
    def root():
        return f"For docs on how to use this API, go to /docs."

    @fastapi_app.get("/dashboard")
    def dashboard():
        return app.get_dashboard_response()

    @fastapi_app.get("/logs/server", response_class=PlainTextResponse)
    def server_logs():
        return app.get_server_logs()

    @fastapi_app.get("/logs/device", response_class=PlainTextResponse)
    def device_logs():
        # TODO: add a POST for device to send its logs back to server
        return app.get_device_logs()

    logger.debug("Configured routes.")

    return fastapi_app
