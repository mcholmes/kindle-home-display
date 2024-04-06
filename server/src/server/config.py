from pydantic import BaseModel, Field, PositiveInt, NonNegativeInt
import toml

class ServerConfig(BaseModel):
    port: NonNegativeInt = Field(default=8080, le=65535, description="Port to open connections on")
    server_dir: str = Field(default="/var/www/html/", description="Folder to serve files, and write log to")
    image_uri: str = Field(default="/dashboard", description="Name of the URI for the image")
    command_uri: str = Field(default="/command", description="Name of the URI for sending commands, e.g. stop refreshing")

class ImageConfig(BaseModel):
    name: str = Field(default="dashboard.png", description="Image name")
    width: PositiveInt = Field(description="Image width, in pixels")
    height: PositiveInt = Field(description="Image height, in pixels")
    rotate_angle: int = Field(description="Angle to rotate the rendered image")

class CalendarConfig(BaseModel):
    display_timezone: str = "Europe/London"
    days_to_show: PositiveInt = 2
    ids: dict[str, str] = Field(description="Key-value pairs of calendar name and identifier. Intended for Google Calendar")
    creds: str = Field(description="Path to credentials file. Intended for Google Calendar")

class WeatherConfig(BaseModel):
    latitude: float
    longitude: float

class AppConfig(BaseModel):
    server: ServerConfig
    image: ImageConfig
    calendar: CalendarConfig
    weather: WeatherConfig | None

    @classmethod
    def from_toml(cls, file_path: str):
        with open(file_path, 'r') as f:
            config_dict = toml.load(f)
        return cls(**config_dict)