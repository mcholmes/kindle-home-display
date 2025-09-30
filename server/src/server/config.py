import os
from ipaddress import IPv4Address
from pathlib import Path

import toml
from pydantic import BaseModel, Field, SecretStr


class ServerConfig(BaseModel):
    host: IPv4Address = Field(
        default="127.0.0.1",
        description="Host to bind socket to. Any valid IP address",
    )
    port: int = Field(
        default=8080, ge=0, le=65535, description="Port to bind socket to"
    )
    server_dir: str = Field(
        default="/var/www/html/",
        description="Folder to write files to (e.g. image files, logs). Typical for apache2"
    )
    server_log_file_name: str = Field(default="server.log", description="File name to write server logs to")
    image_name: str = Field(default="dashboard.png", description="Image name, if writing as file")


class ImageConfig(BaseModel):
    width: int = Field(gt=0, description="Image width, in pixels")
    height: int = Field(gt=0, description="Image height, in pixels")
    margin_x: int = Field(gt=0, default=100, description="Margin from left and right edges of image, in pixels.")
    margin_y: int = Field(gt=0, default=200, description="Margin from top and bottom edges of image, in pixels.")
    rotate_angle: int = Field(default=0, description="Angle to rotate the rendered image")


class CalendarConfig(BaseModel):
    display_timezone: str = "Europe/London"
    days_to_show: int = Field(gt=0, default=2)
    ids: dict[str, str] = Field(
        description="Key-value pairs of calendar name and identifier. Intended for Google Calendar"
    )
    creds: Path = Field(
        description="Path to credentials file. Intended for Google Calendar"
    )


class TasksConfig(BaseModel):
    project_id: str
    # API key will be loaded from environment variable
    api_key: SecretStr | None = Field(
        default=None,
        description="Todoist API key. Can be set via TODOIST_API_KEY environment variable"
    )


class WeatherConfig(BaseModel):
    latitude: float
    longitude: float
    # API key will be loaded from environment variable
    api_key: SecretStr | None = Field(
        default=None,
        description="OpenWeatherMap API key. Can be set via OPENWEATHERMAP_API_KEY environment variable"
    )


class AppConfig(BaseModel):
    """
    Simplified configuration management.

    Config is loaded from a single config.toml file with sensitive data
    (API keys) loaded from environment variables following 12-factor app principles.
    """
    server: ServerConfig
    image: ImageConfig

    calendar: CalendarConfig | None = None
    weather: WeatherConfig | None = None
    tasks: TasksConfig | None = None

    @classmethod
    def from_file(cls, config_path: Path) -> "AppConfig":
        """
        Load configuration from a TOML file with environment variable overrides.

        Args:
            config_path: Path to the config.toml file

        Returns:
            AppConfig: Configured application instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If required configuration is missing
        """
        if not config_path.exists():
            msg = f"Config file not found: {config_path}"
            raise FileNotFoundError(msg)

        # Load TOML config
        with config_path.open() as f:
            config_dict = toml.load(f)

        # Apply environment variable overrides and load API keys
        cls._apply_env_overrides(config_dict)

        return cls.model_validate(config_dict)

    @classmethod
    def from_dir(cls, directory: Path | str) -> "AppConfig":
        """
        Load configuration from a directory, looking for config.toml.

        Args:
            directory: Directory containing config.toml

        Returns:
            AppConfig: Configured application instance
        """
        directory = Path(directory)
        config_path = directory / "config.toml"
        return cls.from_file(config_path)

    @staticmethod
    def _apply_env_overrides(config_dict: dict) -> None:
        """Apply environment variable overrides to configuration dictionary."""

        # Server overrides
        if "SERVER_HOST" in os.environ:
            config_dict.setdefault("server", {})["host"] = os.environ["SERVER_HOST"]
        if "SERVER_PORT" in os.environ:
            config_dict.setdefault("server", {})["port"] = int(os.environ["SERVER_PORT"])

        # Load API keys from environment variables
        todoist_key = os.environ.get("TODOIST_API_KEY")
        if todoist_key and "tasks" in config_dict:
            config_dict["tasks"]["api_key"] = todoist_key

        openweather_key = os.environ.get("OPENWEATHERMAP_API_KEY")
        if openweather_key and "weather" in config_dict:
            config_dict["weather"]["api_key"] = openweather_key
