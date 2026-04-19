import io
import textwrap
from pathlib import Path

import pendulum
from PIL import Image, ImageDraw
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, PositiveFloat, PositiveInt

from server.activity import Activity
from server.font import Font, FontFactory

_script_dir = Path(__file__).resolve().parent

_DEFAULT_FONT_MAP = {
    "extralight": "Lexend-ExtraLight.ttf",
    "light": "Lexend-Light.ttf",
    "regular": "Lexend-Regular.ttf",
    "bold": "Lexend-Bold.ttf",
    "extrabold": "Lexend-ExtraBold.ttf",
}


class RenderConfig(BaseModel):
    """Validated configuration for the Renderer. Separate from drawing state."""

    model_config = ConfigDict(extra="forbid")

    image_height: PositiveInt = Field(description="Image height in pixels")
    image_width: PositiveInt = Field(description="Image width in pixels")

    background_colour: str = Field(default="white")
    fonts_file_dir: str = Field(
        default=_script_dir / "font",
        description="Path to directory containing .ttf fonts",
    )
    font_style_map: dict[str, str] = Field(
        description="Map of style names to font names",
        default_factory=lambda: dict(_DEFAULT_FONT_MAP),
    )

    activity_line_spacing: PositiveFloat = Field(
        default=1.1,
        description="Multiple of height to space apart bullet points.",
    )

    bullet_formats: dict[str, str] = Field(
        default={"event": "•", "task": ">"},
        description="Bullet point markers. Can be an empty string.",
    )

    margin_x: NonNegativeInt = Field(default=0, description="Left and right margins")
    margin_y: NonNegativeInt = Field(default=0, description="Top and bottom margins")
    top_row_y: NonNegativeInt = Field(
        default=0, description="Pixels from the top to place the date",
    )
    space_between_sections: NonNegativeInt = Field(
        default=50, description="Vertical pixels between header, today, and tomorrow",
    )
    rotate_angle: int = Field(
        default=0,
        description="Angle in degrees to rotate the image after rendering.",
    )


class Renderer:
    """Renders a dashboard image from Activity data using a validated RenderConfig."""

    def __init__(self, config: RenderConfig):
        self._config = config
        self._image = Image.new("L", (config.image_width, config.image_height), config.background_colour)
        self._draw = ImageDraw.Draw(self._image)
        self._ff = FontFactory(self._draw, config.fonts_file_dir, config.font_style_map)

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

    def render_single_activity(
        self, position: tuple[int, int], activity_text: str, bullet: str, font: Font, prefix: str | None = None
    ):
        """
        Writes a bullet-point, some grey text (prefix), then some black text (activity_text).
        The black text is truncated with ... if it extends past the right-hand margin.
        """
        c = self._config
        x_0, y = position

        # Write the bullet
        if len(bullet) > 0:
            bullet = bullet + " "
            font.write((x_0, y), bullet)

            width_bullet = font.width(bullet)
        else:
            width_bullet = 0  # needed to know where to start writing the prefix

        # Write the prefix text
        x_prefix = x_0 + width_bullet
        if prefix is not None and len(prefix) > 0:
            prefix = prefix + " "
            font.write((x_prefix, y), prefix, colour="gray")

            width_prefix = font.width(prefix)
        else:
            width_prefix = 0

        # Write the main text
        x_activity_text = x_prefix + width_prefix
        max_width = c.image_width - (c.margin_x + x_activity_text)
        activity_text_truncated = self.truncate_with_ellipsis(
            text=activity_text, max_width=max_width, font=font
        )
        font.write((x_activity_text, y), activity_text_truncated)

    def render_activities(self, section_title: str, events: list[Activity], y: int) -> int:
        """Renders a section with a title and bullet points starting at the given y-coordinate."""
        c = self._config

        event_title = self._ff.get("light")
        event_regular = self._ff.get("regular")
        event_nothing = self._ff.get("extralight")

        # Title text
        title_width = event_title.width(section_title)
        title_pos_x = c.image_width // 2
        event_title.write((title_pos_x, y), section_title, colour="gray", anchor="mm")

        # Lines either side of title
        left_line_x_start = c.margin_x
        left_line_x_end = title_pos_x - (title_width // 2 + 50)
        right_line_x_start = title_pos_x + (title_width // 2 + 50)
        right_line_x_end = c.image_width - c.margin_x

        self._draw.line(
            [left_line_x_start, y, left_line_x_end, y], fill="gray", width=1
        )
        self._draw.line(
            [right_line_x_start, y, right_line_x_end, y], fill="gray", width=1
        )

        y += event_title.height()  # Add spacing after the title

        # Bullets
        line_height = event_regular.height()

        if len(events) == 0:
            # Can show a message if nothing to display
            text_nothing = ""
            event_nothing.write(
                (c.image_width / 2, y), text_nothing, colour="gray", anchor="ma"
            )
            y += line_height + 5
            return y

        for index, activity in enumerate(events):
            # Stop rendering events if we're past the bottom margin
            if y > c.image_height - c.margin_y:
                remaining = len(events) - index
                event_regular.write((c.margin_x, y), f"     + {remaining} more...")
                break

            text = activity.summary
            time = activity.time_start_short
            bullet = c.bullet_formats[activity.activity_type]

            position = (c.margin_x, y)
            if time is None:
                self.render_single_activity(
                    position=position,
                    activity_text=text,
                    bullet=bullet,
                    font=event_regular,
                )
            else:
                self.render_single_activity(
                    position=position,
                    prefix=time,
                    activity_text=text,
                    bullet=bullet,
                    font=event_regular,
                )

            y += (line_height * c.activity_line_spacing) + 5  # Add spacing between bullet points

        return y + c.space_between_sections

    def render_date(self, day: str, day_of_week: str, month: str):
        c = self._config
        date_num = self._ff.get("bold", 200)
        date_rest = self._ff.get("regular")

        date_num.write((c.margin_x, c.top_row_y), day, anchor="ls")
        day_width = date_num.width(day)

        date_rest.write(
            (c.margin_x + day_width + 10, c.top_row_y),
            day_of_week,
            colour="gray",
            anchor="ls",
        )
        date_rest.write(
            (c.margin_x + day_width + 10, c.top_row_y - date_rest.height()),
            month,
            colour="gray",
            anchor="ls",
        )

    def render_last_updated(self, time: str):
        c = self._config
        text = f"Refreshed {time}"
        f = self._ff.get("regular", 20)
        f.write(
            (c.image_width // 2, c.image_height - 0.5 * c.margin_y),
            text,
            colour="gray",
            anchor="ms",
        )

    def render_all(
        self,
        todays_date: pendulum.DateTime,
        events_today: list[Activity],
        events_tomorrow: list[Activity],
    ) -> None:
        c = self._config
        day = todays_date.format("D")
        day_of_week = todays_date.format("ddd")
        month = todays_date.format("MMM")
        time = todays_date.format("HH:mm")
        self.render_date(day, day_of_week, month)

        y0 = c.top_row_y + c.space_between_sections
        y1 = self.render_activities("Today", events_today, y0)
        self.render_activities("Tomorrow", events_tomorrow, y1)

        self.render_last_updated(time)

        self._image = self._image.rotate(c.rotate_angle, expand=True)

    def render_error(self, error_text: str) -> None:
        """Renders an error screen containing the traceback."""
        c = self._config
        font = self._ff.get("regular", 16)

        approx_char_width = font.width("a") or 8
        max_chars = max(40, (c.image_width - 2 * c.margin_x) // approx_char_width)

        lines = []
        for line in error_text.split('\n'):
            wrapped = textwrap.wrap(line, width=max_chars, replace_whitespace=False)
            if wrapped:
                lines.extend(wrapped)
            else:
                lines.append('')

        y = c.margin_y + c.top_row_y
        line_height = font.height()

        for line in lines:
            if y + line_height > c.image_height - c.margin_y:
                font.write((c.margin_x, y), "... (truncated)")
                break
            font.write((c.margin_x, y), line)
            y += int(line_height * 1.5)

        self._image = self._image.rotate(c.rotate_angle, expand=True)

    def get_png(self) -> bytes:
        with io.BytesIO() as output:
            self._image.save(output, format="PNG")
            return output.getvalue()

    def save_png(self, output_filepath: str) -> None:
        """
        Full path with .png extension
        """
        self._image.save(output_filepath, format="PNG")
