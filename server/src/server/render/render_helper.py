from __future__ import annotations

import logging
from os import path
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw
from .font_helper import FontFactory, Font

if TYPE_CHECKING:    
    from datetime import datetime

"""
TODO:
- decide what to do with weather. next N hours? just icon/temp?
"""

logger = logging.getLogger(__name__)
script_dir = path.dirname(path.abspath(__file__))

class Renderer:

    def __init__(self, font_map: dict[str],
                 image_width: int, image_height: int, margin_x: int, margin_y: int,
                 top_row_y: int, spacing_between_sections: int,
                 output_filepath: str
                 ):

            self.output_filepath = output_filepath # needs to be full path with .png extension

            self.image = Image.new("RGB", (image_width, image_height), "white")
            self.draw = ImageDraw.Draw(self.image)

            fonts_file_dir = path.join(script_dir, "font")
            self.ff = FontFactory(self.draw, fonts_file_dir, font_map)

            self.image_height = image_height
            self.image_width = image_width
            self.margin_x = margin_x
            self.margin_y = margin_y
            self.top_row_y = top_row_y
            self.spacing_between_sections = spacing_between_sections

            self.bullet_format = "•"

    @staticmethod
    def truncate_with_ellipsis(text: str, max_width: int, font: Font) -> str:
        
        if font.width(text) <= max_width:
            return text

        # Binary search to find the optimal truncation point
        left = 0
        right = len(text) - 1
        while left <= right:
            mid = (left + right) // 2
            if font.width(text[:mid] + '...') <= max_width:
                left = mid + 1
            else:
                right = mid - 1

        return text[:left - 1] + '...'

    def render_event_text_only(self, position: tuple[int], event_text : str, font : Font):
        text = f"{self.bullet_format} {event_text}"
        truncated_text = self.truncate_with_ellipsis(text=text, max_width=self.image_width-2*self.margin_x, font=font)    
        font.write(position, truncated_text)

    def render_event_with_time(self, position: tuple[int], event_time : str, event_text : str, font: Font):
        x,y = position

        bullet = self.bullet_format + " "
        event_time = event_time + " "

        width_time = font.width(event_time)
        width_bp = font.width(bullet)

        x_time = x + width_bp
        x_text = x_time + width_time

        font.write((x, y), bullet)
        font.write((x_time, y), event_time, colour="gray")
        
        max_width = self.image_width - (self.margin_x + x_text)
        event_text_truncated = self.truncate_with_ellipsis(text=event_text, max_width=max_width, font=font)
        font.write((x_text, y), event_text_truncated)

    def render_events(self, section_title: str, events: list[dict], y: int):
        """Renders a section with a title and bullet points starting at the given y-coordinate."""


        event_title = self.ff.get("light")
        event_regular = self.ff.get("regular")
        event_nothing = self.ff.get("extralight")

        # Title text
        title_width = event_title.width(section_title)
        title_pos_x = self.image_width//2
        event_title.write((title_pos_x, y), section_title, colour="gray", anchor="mm")

        # Lines either side of title
        left_line_x_start = self.margin_x
        left_line_x_end = title_pos_x - (title_width//2 + 50)
        right_line_x_start = title_pos_x + (title_width//2 + 50)
        right_line_x_end = self.image_width - self.margin_x

        self.draw.line([left_line_x_start, y,
                        left_line_x_end, y],
                        fill="gray", width=1)
        self.draw.line([right_line_x_start, y,
                        right_line_x_end, y],
                        fill="gray", width=1)

        y += event_title.height()  # Add spacing after the title

        # Bullets
        bullet_height = event_regular.height()

        if len(events) == 0:
            # dummy draw. Can customise message if useful
            event_nothing.write((self.image_width/2, y), "", colour="gray", anchor="ma") 
            y += bullet_height + 5
            return y

        for index, event in enumerate(events):

            # Stop rendering events if we're past the bottom margin
            if y > self.image_height - self.margin_y:
                remaining = len(events) - index
                event_regular.write((self.margin_x, y), f"     + {remaining} more...")
                break

            text = event["summary"]
            time = event.get("short_time", None)
            position = (self.margin_x, y)
            if time is None:
                self.render_event_text_only(position=position, event_text=text, font=event_regular)
            else:
                self.render_event_with_time(position=position, event_time=time, event_text=text, font=event_regular)

            y += bullet_height + 5  # Add spacing between bullet points

        return y

    def render_date(self, day, day_of_week, month):

        date_num = self.ff.get("bold", 200)
        date_rest = self.ff.get("regular")

        date_num.write((self.margin_x, self.top_row_y), day, anchor="ls")
        day_width = date_num.width(day)

        date_rest.write((self.margin_x + day_width + 10, self.top_row_y),
                       day_of_week,
                       colour="gray", anchor="ls")
        date_rest.write((self.margin_x + day_width + 10, self.top_row_y - date_rest.height()),
                       month,
                       colour="gray", anchor="ls")

    def render_weather(self, text, icon):

        weather_icon = self.ff.get("weather", 150)
        weather_text = self.ff.get("regular")

        weather_text.write((self.image_width - self.margin_x - weather_text.width(text), self.top_row_y),
                       text,
                       colour="gray", anchor="ls")
        weather_icon.write((self.image_width - self.margin_x - weather_icon.width(icon), self.top_row_y - weather_text.height()),
                       icon, 
                       anchor="ls")

    def render_last_updated(self, time: str):
        text = f"Refreshed {time}"
        f = self.ff.get("regular", 20)
        f.write((self.image_width//2, self.image_height - 0.5*self.margin_y), text, colour="gray", anchor="ms")

    def render_all(self, todays_date: datetime, weather, events_today, events_tomorrow):

        # Render top row
        day = todays_date.strftime("%-d")
        day_of_week = todays_date.strftime("%a")
        month = todays_date.strftime("%b")
        time = todays_date.strftime("%H:%M")
        self.render_date(day, day_of_week, month)
        # render_weather(text="Broken clouds | 11º", icon="\uf00d")

        # Render the "Today" section
        y = self.top_row_y + 2*self.spacing_between_sections # TODO: return this from render_top_row
        y = self.render_events("Today", events_today, y)

        # Render the "Tomorrow" section
        y += self.spacing_between_sections
        self.render_events("Tomorrow", events_tomorrow, y)

        self.render_last_updated(time)

        # Save the image
        fn = self.output_filepath
        if not path.exists(fn):
            f = open(fn, "x")
            f.close()

        self.image.save(fn)
