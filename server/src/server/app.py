import logging
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse

from server.activity import Activity, group_events_by_relative_day, sort_by_time
from server.config import AppConfig
from server.datasources.gcal import GCal
from server.datasources.todoist import get_tasks_todoist
from server.render import Renderer

logger = logging.getLogger(__name__)

class App:
    config: AppConfig
    router: APIRouter | None = None

    def __init__(self, config: AppConfig):
        self.config = config

    @classmethod
    def create_server(cls, config: AppConfig) -> "App":
        """Create an App instance configured for server mode with web routes."""
        app = cls(config)
        app.configure_routes()
        return app

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
        """
        Fetch data from all configured sources in parallel with error handling.
        Only fetches from sources that are properly configured.
        """
        # Get current time in display timezone
        display_timezone = ZoneInfo(self.config.calendar.display_timezone if self.config.calendar else "UTC")
        current_date = datetime.now(display_timezone)

        # Determine which data sources to fetch based on configuration
        data_sources = []

        if self.config.tasks and self.config.tasks.api_key:
            data_sources.append(("tasks", self.get_tasks))

        if self.config.calendar:
            data_sources.append(("appointments", self.get_appointments))

        # Add weather fetching when implemented
        # if self.config.weather and self.config.weather.api_key:
        #     data_sources.append(("weather", self.get_weather))

        source_names = [name for name, _ in data_sources]
        logger.debug("Fetching data from %d sources: %s", len(data_sources), source_names)

        # Fetch data in parallel with error handling
        all_events = []

        if data_sources:
            with ThreadPoolExecutor(max_workers=len(data_sources)) as executor:
                # Submit all tasks
                future_to_source = {
                    executor.submit(self._fetch_with_error_handling, source_name, fetch_func, current_date): source_name
                    for source_name, fetch_func in data_sources
                }

                # Collect results as they complete
                for future in wait(future_to_source.keys()).done:
                    source_name = future_to_source[future]
                    try:
                        events = future.result()
                        all_events.extend(events)
                        logger.debug("Successfully fetched %d events from %s", len(events), source_name)
                    except (RuntimeError, ValueError, ConnectionError):
                        logger.exception("Failed to fetch data from %s", source_name)
                        # Continue with other sources - graceful degradation
        else:
            logger.warning("No data sources configured or available")

        # Process and filter events
        events_filtered = [event for event in all_events if not event.ended_over_an_hour_ago]
        events_grouped = group_events_by_relative_day(events=events_filtered, current_date=current_date)

        total_events = sum(len(events_grouped[day]) for day in events_grouped)
        logger.info("Retrieved %d events across %d days", total_events, len(events_grouped))

        return events_grouped, current_date

    def _fetch_with_error_handling(self, source_name: str, fetch_func, current_date: datetime) -> list[Activity]:
        """
        Wrapper to fetch data from a source with error handling and timeout.
        Returns empty list on error to allow graceful degradation.
        """
        try:
            logger.debug("Fetching data from %s...", source_name)
            return fetch_func(current_date)
        except (RuntimeError, ValueError, ConnectionError):
            logger.exception("Error fetching from %s", source_name)
            return []  # Graceful degradation - return empty list

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
        """Fetch tasks from Todoist API."""
        config = self.config.tasks
        if not config or not config.api_key:
            logger.debug("Todoist not configured, skipping tasks")
            return []

        # Use calendar days_to_show if available, otherwise default to 2 days
        days_to_show = self.config.calendar.days_to_show if self.config.calendar else 2
        date_end = current_date + timedelta(days=days_to_show)

        logger.debug("Fetching tasks from Todoist for project %s until %s", config.project_id, date_end.date())
        return get_tasks_todoist(api_key=config.api_key, project_id=config.project_id, date_end=date_end)

    def get_appointments(self, current_date: datetime) -> list[Activity]:
        """Fetch calendar events from Google Calendar API."""
        config = self.config.calendar
        if not config:
            logger.debug("Calendar not configured, skipping appointments")
            return []

        # Calculate date range
        start_date = datetime.combine(current_date.date(), time.min)  # midnight today
        end_date = start_date + timedelta(days=config.days_to_show)

        logger.debug("Fetching calendar events from %s to %s", start_date.date(), end_date.date())

        # Use GCal directly instead of the redundant Calendar wrapper
        gcal = GCal(config.creds)
        return gcal.get_events(
            date_from=start_date,
            date_to=end_date,
            additional_calendars=list(config.ids.values()),
            exclude_default_calendar=False,
        )

    def configure_routes(self):
        """Configure FastAPI routes for server mode."""
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
            "/health",
            endpoint=self.health_check,
            methods=["GET"],
            )

        logger.debug("Started server.")

    def root(self) -> str:
        return f"For docs on how to use this API, go to localhost:{self.config.server.port}/docs."

    def health_check(self) -> dict[str, str]:
        """Health check endpoint for Docker health checks and monitoring."""
        return {"status": "healthy", "timestamp": datetime.now(tz=ZoneInfo("UTC")).isoformat()}
