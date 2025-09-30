"""
Simplified FastAPI server for kindle-home-display.

Run with:
    fastapi run server/main.py
    # or
    uvicorn server.main:app --reload

Configuration via environment variables:
    - TODOIST_API_KEY: Your Todoist API key
    - OPENWEATHERMAP_API_KEY: Your OpenWeatherMap API key
    - SERVER_HOST: Server host (default: 127.0.0.1)
    - SERVER_PORT: Server port (default: 8080)
    - LOG_LEVEL: Logging level (default: INFO)
    - CONFIG_DIR: Directory containing config.toml (default: current dir)
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi_radar import Radar

from server.app import App
from server.config import AppConfig


def setup_logging():
    """Configure logging based on environment variables."""
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    log_to_console = os.environ.get("LOG_TO_CONSOLE", "false").lower() == "true"

    # Load config to get log file path
    config_dir = Path(os.environ.get("CONFIG_DIR", "."))
    config = AppConfig.from_dir(config_dir)
    log_filepath = Path(config.server.server_dir) / config.server.server_log_file_name

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s :: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    log_dir = log_filepath.parent
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler (optional)
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    return config


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    # Setup logging and load config
    config = setup_logging()

    # Create app instance with routes
    app_instance = App.create_server(config)

    # Create FastAPI app
    app = FastAPI(
        title="Kindle Home Display Server",
        description="Generates dashboard images for Kindle display device",
        version="0.5.1"
    )

    # Include routes
    app.include_router(app_instance.router)

    # Setup monitoring with FastAPI Radar
    radar = Radar(
        app,
        dashboard_path="/__radar",   # Custom dashboard path (default: "/__radar")
        max_requests=1000,           # Max requests to store (default: 1000)
        retention_hours=240,         # Data retention period (default: 24)
        slow_query_threshold=1000,   # Mark queries slower than this as slow (ms)
        exclude_paths=["/health"],   # Paths to exclude from monitoring
        theme="auto",                # Dashboard theme: "light", "dark", or "auto"
        db_path="./data/radar.duckdb",       # Custom path for radar.duckdb file (default: current directory)
    )
    radar.create_tables()

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    # For development - use `python -m server.main`
    import uvicorn
    config_dir = Path(os.environ.get("CONFIG_DIR", "."))
    config = AppConfig.from_dir(config_dir)
    uvicorn.run(
        "server.main:app",
        host=str(config.server.host),
        port=config.server.port,
        reload=True,
        log_level="info"
    )
