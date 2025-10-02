"""
Simplified FastAPI server for kindle-home-display.

Run with:
    fastapi run server/main.py
    # or
    uvicorn server.main:app --reload

Configuration via environment variables:
    - TODOIST_API_KEY: Your Todoist API key
    - OPENWEATHERMAP_API_KEY: Your OpenWeatherMap API key
    - LOG_LEVEL: Logging level (default: INFO)
    - CONFIG_DIR: Directory containing config.toml (default: current dir)
"""

import logging
import os
from pathlib import Path

import uvicorn

# from fastapi_radar import Radar
from fastapi import FastAPI

from server.app import App
from server.config import AppConfig


def setup_logging(config: AppConfig, log_to_console: bool = False) -> None:
    """Configure logging."""
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    log_filepath = Path(config.server.server_dir) / config.server.server_log_file_name

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s :: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    log_dir = log_filepath.parent
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    # Load configuration
    config_dir = Path(os.environ.get("CONFIG_DIR", "."))
    config = AppConfig.from_dir(config_dir)

    # Setup logging
    log_to_console = os.environ.get("LOG_TO_CONSOLE", "false").lower() == "true"
    setup_logging(config, log_to_console)

    logger = logging.getLogger(__name__)
    logger.info(f"Starting Kindle Home Display Server with config from {config_dir}")

    # Create app instance with routes
    app_instance = App.create_server(config)

    # Create FastAPI app
    app = FastAPI(
        title="Kindle Home Display Server",
        description="Generates dashboard images for Kindle display device",
        version="1.0.0",
    )

    # Include routes
    app.include_router(app_instance.router)

    # # Setup monitoring with FastAPI Radar
    # radar_db_path = Path(config.server.server_dir) / "radar.duckdb"
    # radar = Radar(
    #     app,
    #     max_requests=1000,
    #     retention_hours=240,
    #     slow_query_threshold=1000,
    #     exclude_paths=["/health"],
    #     theme="auto",
    #     db_path=str(radar_db_path),
    # )
    # radar.create_tables()

    logger.info("Server initialized")

    return app


# Create app instance for uvicorn/fastapi
app = create_app()

if __name__ == "__main__":
    uvicorn.run(app=app)
