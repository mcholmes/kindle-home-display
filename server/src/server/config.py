import json
from collections.abc import Iterator
from ipaddress import IPv4Address
from pathlib import Path
from typing import Optional

import toml
import yaml
from pydantic import BaseModel, Field, SecretStr


class MultipleFilesFoundError(Exception):
    pass

def find_file_in_dir(directory: Path, basename: str) -> Path:
    """
    Find a file with the given basename and supported extensions in the specified directory.

    Args:
        directory (Path): The directory to search for the file.
        basename (str): The base name of the file (i.e. without extension).

    Returns:
        Path: The path to the matching file.

    Raises:
        FileNotFoundError: If no files or multiple files are found with the given basename and supported extensions.
    """

    supported_extensions = ['.json', '.yaml', '.yml', '.toml']

    matching_files = [file for file in directory.iterdir()
                      if file.stem == basename and file.suffix.lower() in supported_extensions]

    num_matching_files = len(matching_files)
    if num_matching_files == 0:
        err = f"""
            No files found with basename '{basename}' and
            extension in {supported_extensions} in the directory {directory}."""
        raise FileNotFoundError(err)

    if num_matching_files > 1:
        err = f"""
            Multiple ({num_matching_files}) files found with basename {basename} and
            extension in {supported_extensions} in the directory {directory}."""
        raise MultipleFilesFoundError(err)

    return matching_files[0]



def get_required_fields(model: type[BaseModel], recursive: bool = False) -> Iterator[str]:  # noqa: FBT001, FBT002
    for name, field in model.model_fields.items():
        if not field.is_required():
            continue
        t = field.annotation
        if recursive and isinstance(t, type) and issubclass(t, BaseModel):
            yield from get_required_fields(t, recursive=True)
        else:
            yield name

def check_config_contains_required_fields(cls: BaseModel, config_dict: dict) -> None:
    """
    Checks that the top-level keys in config_dict match the non-optional fields of this class.
    Note that it doesn't check the lower-level fields within each; we leave that to Pydantic.
    """
    if len(config_dict) == 0:
        err = "Config provided is empty."
        raise ValueError(err) from None

    missing_sections = [field_name for field_name in get_required_fields(cls) if field_name not in config_dict]

    if len(missing_sections) > 0:
        err = f"Missing top-level configs: {', '.join(missing_sections)}"
        raise ValueError(err)


def get_dict_from_file(file_path: Path) -> dict:
    if not file_path.is_file():
        raise IsADirectoryError

    extension = str.lower(file_path.suffix)
    if extension not in [".json", ".yml", ".yaml", ".toml"]:
        err = f"Unsupported file type: {extension}. Valid types are yml/yaml, json and toml."
        raise TypeError(err)

    with Path.open(file_path) as f:
        if extension in [".yml", ".yaml"]:
            output = yaml.safe_load(f)
        elif extension == ".json":
            output = json.load(f)
        else:
            output = toml.load(f)

        return output

# TODO: use this to print help to the CLI of what can be in the config file
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
    device_log_file_name: str = Field(default="device.log", description="File name to write device logs to")
    image_name: str = Field(default="dashboard.png", description="Image name, if writing as file")

class ImageConfig(BaseModel):
    width: int = Field(gt = 0, description="Image width, in pixels")
    height: int = Field(gt = 0, description="Image height, in pixels")
    margin_x: int = Field(gt = 0, default = 100, description="Margin from left and right edges of image, in pixels.")
    margin_y: int = Field(gt = 0, default = 200, description="Margin from top and bottom edges of image, in pixels.")
    rotate_angle: int = Field(default = 0, description="Angle to rotate the rendered image")

class CalendarConfig(BaseModel):
    display_timezone: str = "Europe/London"
    days_to_show: int = Field(gt = 0, default=2)
    ids: dict[str, str] = Field(
        description="Key-value pairs of calendar name and identifier. Intended for Google Calendar"
    )
    creds: Path = Field(
        description="Path to credentials file. Intended for Google Calendar"
    )

class TasksConfig(BaseModel):
    project_id: int

class WeatherConfig(BaseModel):
    latitude: float
    longitude: float

class AppConfig(BaseModel):
    server: ServerConfig
    image: ImageConfig

    api_keys: Optional[dict[str, SecretStr]] = None
    calendar: Optional[CalendarConfig] = None
    weather: Optional[WeatherConfig] = None
    tasks: Optional[TasksConfig] = None

    @classmethod
    def from_dir(cls, directory: Path):
        """
        Load configuration from a directory.

        Args:
            directory (Path): The directory containing the configuration files.

        Returns:
            Config: An instance of the Config class initialized with the loaded configuration.

        Raises:
            NotADirectoryError: If the supplied path is not a directory.

        """
        if not directory.is_dir:
            err = "Path supplied isn't a directory."
            raise NotADirectoryError(err)

        config_basename = "config"
        api_basename = "api_keys"

        config_file = find_file_in_dir(directory, config_basename)
        config_dict = get_dict_from_file(config_file)

        try:
            api_keys_file = find_file_in_dir(directory, api_basename)
            api_keys_dict = get_dict_from_file(api_keys_file)
        except FileNotFoundError:
            api_keys_dict = None

        return cls.from_dicts(config_dict, api_keys_dict)

    @classmethod
    def from_dicts(cls, config: dict, api_keys: Optional[dict[str, SecretStr]] = None):
        """
        Instantiate this class and its fields from a dictionary, and an optional dictionary of API keys.
        Any unrecognised fields in the config will be ignored.
        """
        check_config_contains_required_fields(cls, config)

        calendar = CalendarConfig(**config["calendar"]) if "calendar" in config else None
        weather = WeatherConfig(**config["weather"]) if "weather" in config else None
        tasks = TasksConfig(**config["tasks"]) if "tasks" in config else None

        return cls(
            server = ServerConfig(**config["server"]),
            image = ImageConfig(**config["image"]),
            api_keys = api_keys, # TODO: move these into their respective Configs
            calendar = calendar,
            weather = weather,
            tasks = tasks
        )
