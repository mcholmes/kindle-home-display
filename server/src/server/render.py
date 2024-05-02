import io
import logging
import pathlib

# if TYPE_CHECKING:
from datetime import datetime
from os import listdir, path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field, NonNegativeInt, PositiveInt, PrivateAttr

from server.event import Event

"""
TODO:
- decide what to do with weather. next N hours? just icon/temp?
"""

logger = logging.getLogger(__name__)
script_dir = path.dirname(path.abspath(__file__))


class Font:
    """
    An abstraction over PIL's ImageFont.
    - Allows easier interrogation & reuse of calculated height.
    - Allows fonts to draw themselves, rather than passing around ImageFonts.
    """

    def __init__(self, draw: ImageDraw, file: str, size: int):
        self._draw = draw

        f = ImageFont.truetype(file, size)
        self._font = f
        self._height = f.getbbox("lq")[
            3
        ]  # max height for a line of this size, not its actual height

    def width(self, text: str) -> int:
        return self._font.getbbox(text)[2]

    def height(self, text: Optional[str] = None) -> int:
        if text is None:
            return self._height

        return self._font.getbbox(text)[3]

    def size(self, text: str) -> int:
        return self.width(text), self.height(text)

    def write(
        self,
        position: tuple,
        text: str,
        colour: str = "black",
        anchor: Optional[str] = None,
    ) -> None:
        self._draw.text(position, text, font=self._font, fill=colour, anchor=anchor)

    def image_font(self) -> ImageFont:
        return self._font


class FontFactory:
    def __init__(
        self,
        draw: ImageDraw,
        font_dir: Optional[str] = None,
        font_map: Optional[dict[str]] = None,
    ):
        self.default_size = 48

        if font_dir is None:
            current_path = str(pathlib.Path(__file__).parent.absolute())
            self.font_dir = path.join(current_path, "font")
        else:
            self.font_dir = font_dir

        if font_map is None:
            # Just use the file names as the alias
            self.font_map = {
                file: file for file in listdir(self.font_dir) if file.endswith(".ttf")
            }
        else:
            self.font_map = font_map

        self.draw = draw

        # example:
        # font_map = {
        #         "light": "Lexend-Light.ttf",
        #         "regular": "Lexend-Regular.ttf",
        #         "bold": "Lexend-Bold.ttf",
        #         "extrabold": "Lexend-ExtraBold.ttf",
        #         "weather": "weathericons-regular-webfont.ttf"
        # }

    def get(self, name: str, size: Optional[int] = None):
        if size is None:
            size = self.default_size

        if name not in self.font_map:
            err = f"Font name not in defined list. Valid values are: {self.font_map.values()}"
            raise ValueError(err)

        font_file = path.join(self.font_dir, self.font_map[name])

        return Font(self.draw, font_file, size)


class Renderer(BaseModel):
    class ConfigDict:
        extra = "forbid"

    # Mandatory fields
    image_height: PositiveInt = Field(description="Image height in pixels")
    image_width: PositiveInt = Field(description="Image width in pixels")

    # Optional fields
    background_colour: str = Field(default="white")
    fonts_file_dir: str = Field(
        default=path.join(script_dir, "font"),
        description="Path to directory containing .ttf fonts",
    )
    font_style_map: dict[str, str] = Field(
        description="Map of style names to font names",
        default={
            "extralight": "Lexend-ExtraLight.ttf",
            "light": "Lexend-Light.ttf",
            "regular": "Lexend-Regular.ttf",
            "bold": "Lexend-Bold.ttf",
            "extrabold": "Lexend-ExtraBold.ttf",
            "weather": "weathericons-regular-webfont.ttf",
        },
    )
    margin_x: NonNegativeInt = Field(default=0, description="Left and right margins")
    margin_y: NonNegativeInt = Field(default=0, description="Top and bottom margins")
    top_row_y: NonNegativeInt = Field(
        default=0, description="Pixels from the top to place the date & weather"
    )
    space_between_sections: NonNegativeInt = Field(
        default=0, description="Vertical pixels between header, today, and tomorrow"
    )
    rotate_angle: int = Field(
        default=0,
        description="Angle in degrees to rotate the image after rendering. Useful for multiple-column layouts?",
    )
    bullet_format: int = Field(
        default="•", description="Default for bullet point marker"
    )

    # Private fields computed post-init
    _image: Image = PrivateAttr()
    _draw: ImageDraw = PrivateAttr()
    _ff: FontFactory = PrivateAttr()

    def model_post_init(self, __context) -> None:
        self._image = Image.new("L", (self.image_width, self.image_height), self.background_colour)
        self._draw = ImageDraw.Draw(self._image)
        self._ff = FontFactory(self._draw, self.fonts_file_dir, self.font_style_map)

    @staticmethod
    def truncate_with_ellipsis(text: str, max_width: int, font: Font) -> str:
        if font.width(text) <= max_width:
            return text

        # Binary search to find the optimal truncation point
        left = 0
        right = len(text) - 1
        while left <= right:
            mid = (left + right) // 2
            if font.width(text[:mid] + "...") <= max_width:
                left = mid + 1
            else:
                right = mid - 1

        return text[: left - 1] + "..."

    def render_activity(self, position: tuple[int], activity_text: str, font: Font):
        text = f"{self.bullet_format} {activity_text}"
        truncated_text = self.truncate_with_ellipsis(
            text=text, max_width=self.image_width - 2 * self.margin_x, font=font
        )
        font.write(position, truncated_text)

    def render_activity_with_prefix(
        self, position: tuple[int], prefix: str, activity_text: str, font: Font
    ):
        x, y = position

        bullet = self.bullet_format + " "
        prefix = prefix + " "

        width_prefix = font.width(prefix)
        width_bullet = font.width(bullet)

        x_prefix = x + width_bullet
        x_activity_text = x_prefix + width_prefix

        font.write((x, y), bullet)
        font.write((x_prefix, y), prefix, colour="gray")

        max_width = self.image_width - (self.margin_x + x_activity_text)
        activity_text_truncated = self.truncate_with_ellipsis(
            text=activity_text, max_width=max_width, font=font
        )
        font.write((x_activity_text, y), activity_text_truncated)

    def render_events(self, section_title: str, events: list[Event], y: int):
        """Renders a section with a title and bullet points starting at the given y-coordinate."""

        event_title = self._ff.get("light")
        event_regular = self._ff.get("regular")
        event_nothing = self._ff.get("extralight")

        # Title text
        title_width = event_title.width(section_title)
        title_pos_x = self.image_width // 2
        event_title.write((title_pos_x, y), section_title, colour="gray", anchor="mm")

        # Lines either side of title
        left_line_x_start = self.margin_x
        left_line_x_end = title_pos_x - (title_width // 2 + 50)
        right_line_x_start = title_pos_x + (title_width // 2 + 50)
        right_line_x_end = self.image_width - self.margin_x

        self._draw.line(
            [left_line_x_start, y, left_line_x_end, y], fill="gray", width=1
        )
        self._draw.line(
            [right_line_x_start, y, right_line_x_end, y], fill="gray", width=1
        )

        y += event_title.height()  # Add spacing after the title

        # Bullets
        bullet_height = event_regular.height()

        if len(events) == 0:
            # dummy draw. Can customise message if useful
            event_nothing.write(
                (self.image_width / 2, y), "", colour="gray", anchor="ma"
            )
            y += bullet_height + 5
            return y

        for index, event in enumerate(events):
            # Stop rendering events if we're past the bottom margin
            if y > self.image_height - self.margin_y:
                remaining = len(events) - index
                event_regular.write((self.margin_x, y), f"     + {remaining} more...")
                break

            text = event.summary
            time = event.time_start_short
            position = (self.margin_x, y)
            if time is None:
                self.render_activity(
                    position=position, activity_text=text, font=event_regular
                )
            else:
                self.render_activity_with_prefix(
                    position=position,
                    prefix=time,
                    activity_text=text,
                    font=event_regular,
                )

            y += bullet_height + 5  # Add spacing between bullet points

        return y

    def render_date(self, day: str, day_of_week: str, month: str):
        date_num = self._ff.get("bold", 200)
        date_rest = self._ff.get("regular")

        date_num.write((self.margin_x, self.top_row_y), day, anchor="ls")
        day_width = date_num.width(day)

        date_rest.write(
            (self.margin_x + day_width + 10, self.top_row_y),
            day_of_week,
            colour="gray",
            anchor="ls",
        )
        date_rest.write(
            (self.margin_x + day_width + 10, self.top_row_y - date_rest.height()),
            month,
            colour="gray",
            anchor="ls",
        )

    # TODO: this won't currently work!
    def render_weather(self, text: str, icon: str):
        weather_icon = self._ff.get("weather", 150)
        weather_text = self._ff.get("regular")

        weather_text.write(
            (
                self.image_width - self.margin_x - weather_text.width(text),
                self.top_row_y,
            ),
            text,
            colour="gray",
            anchor="ls",
        )
        weather_icon.write(
            (
                self.image_width - self.margin_x - weather_icon.width(icon),
                self.top_row_y - weather_text.height(),
            ),
            icon,
            anchor="ls",
        )

    def render_last_updated(self, time: str):
        text = f"Refreshed {time}"
        f = self._ff.get("regular", 20)
        f.write(
            (self.image_width // 2, self.image_height - 0.5 * self.margin_y),
            text,
            colour="gray",
            anchor="ms",
        )

    def render_all(
        self,
        todays_date: datetime,
        weather,
        events_today: list[Event],
        events_tomorrow: list[Event],
    ) -> None:
        # Render top row
        day = todays_date.strftime("%-d")
        day_of_week = todays_date.strftime("%a")
        month = todays_date.strftime("%b")
        time = todays_date.strftime("%H:%M")
        self.render_date(day, day_of_week, month)
        # render_weather(text="Broken clouds | 11º", icon="\uf00d")

        # Render the "Today" section
        y = (
            self.top_row_y + 2 * self.space_between_sections
        )  # TODO: return this from render_top_row
        y = self.render_events("Today", events_today, y)

        # Render the "Tomorrow" section
        y += self.space_between_sections
        self.render_events("Tomorrow", events_tomorrow, y)

        self.render_last_updated(time)

        self._image = self._image.rotate(self.rotate_angle, expand=True)

    def get_png(self) -> bytes:
        with io.BytesIO() as output:
            self._image.save(output, format="PNG")
            return output.getvalue()

    def save_png(self, output_filepath: str) -> None:
        """ "
        Full path with .png extension
        """
        self._image.save(output_filepath, format="PNG")
