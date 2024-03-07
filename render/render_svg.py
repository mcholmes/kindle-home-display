from PIL import Image, ImageDraw
from font_helper import FontFactory
import os
import pathlib
import logging

"""
TODO:
- decide what to do with weather. next N hours? just icon/temp? 
"""

class Renderer:

    def __init__(self, ff: FontFactory,
                 image_width: int, image_height: int, margin_x: int, margin_y: int,
                 top_row_y: int, spacing_between_sections: int,
                 bg_colour = "white",
                 ):
            
            self.logger = logging.getLogger('maginkdash')
            
            self.image = Image.new("RGB", (image_width, image_height), bg_colour)
            self.draw = ImageDraw.Draw(self.image)
            self.ff = ff

            self.image_height = image_height
            self.image_width = image_width
            self.margin_x = margin_x
            self.margin_y = margin_y
            self.top_row_y = top_row_y
            self.spacing_between_sections = spacing_between_sections
    
    def render_events(self, section_title, bullet_points, y):
        """Renders a section with a title and bullet points starting at the given y-coordinate."""

        event_title = self.ff.get("light")
        event_reg = self.ff.get("regular")

        # Title text
        title_width = event_title.width(section_title)
        title_pos_x = self.image_width//2
        self.draw.text((title_pos_x, y), section_title, font=event_title.font(), fill="gray", anchor="mm")

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
        f = event_reg.font()
        bullet_height = event_reg.height()
        for index, bullet in enumerate(bullet_points):
            if y > self.image_height - self.margin_y:
                self.draw.text((self.margin_x, y), f"     + {len(bullet_points)-index} more...", font=f, fill="black")
                break
            
            if type(bullet) == str:
                self.draw.text((self.margin_x, y), "• " + bullet, font=f, fill="black")
            elif type(bullet) == tuple:
                event_time = bullet[0] + " "
                event_text = bullet[1]

                width_time = event_reg.width(event_time)
                width_text = event_reg.width(event_text)
                width_bp = event_reg.width("• ") # bp = bulletpoint symbol

                x_bp = self.margin_x
                x_time = x_bp + width_bp 
                x_text = x_time + width_time

                self.draw.text((x_bp, y), "• ", font=f, fill="black")
                self.draw.text((x_time, y), event_time, font=f, fill="gray")
                self.draw.text((x_text, y), event_text, font=f, fill="black")
                    
            y += bullet_height + 5  # Add spacing between bullet points

        return y

    def render_date(self, day, day_of_week, month):

        date_num = self.ff.get("bold", 200)
        date_rest = self.ff.get("regular")
        
        self.draw.text((self.margin_x, self.top_row_y), day, font=date_num.font(), fill="black", anchor="ls")
        day_width = date_num.width(day)

        self.draw.text((self.margin_x + day_width + 10, self.top_row_y), day_of_week, font=date_rest.font(), fill="gray", anchor="ls")
        self.draw.text((self.margin_x + day_width + 10, self.top_row_y - date_rest.height()), month, font=date_rest.font(), fill="gray", anchor="ls")

    def render_weather(self, text, icon):

        weather_icon = self.ff.get("weather", 150)
        weather_text = self.ff.get("regular")

        self.draw.text((self.image_width - self.margin_x - weather_text.width(text), self.top_row_y), text, font=weather_text.font(), fill="gray", anchor="ls")
        self.draw.text((self.image_width - self.margin_x - weather_icon.width(icon), self.top_row_y - weather_text.height()), icon, font=weather_icon.font(), fill="black", anchor="ls")

    def render_all(self, todays_date, weather, events_today, events_tomorrow):
        
        # Render top row
        day = todays_date.strftime("%-d")
        day_of_week = todays_date.strftime("%a")
        month = todays_date.strftime("%b")
        self.render_date(day, day_of_week, month)
        # render_weather(text="Broken clouds | 11º", icon="\uf00d")
        
        # Render the "Today" section
        y = self.top_row_y + 2*self.spacing_between_sections # TODO: return this from render_top_row
        y = self.render_events("Today", events_today, y)

        # Render the "Tomorrow" section
        y += self.spacing_between_sections
        self.render_events("Tomorrow", events_tomorrow, y)

        # Save the image
        self.image.save("output.png")


font_map = {
        "light": "Lexend-Light.ttf", 
        "regular": "Lexend-Regular.ttf", 
        "bold": "Lexend-Bold.ttf",
        "extrabold": "Lexend-ExtraBold.ttf",
        "weather": "weathericons-regular-webfont.ttf"
}

f = FontFactory("/Users/mike.holmes/projects/home-display/render/font",font_map)
r = Renderer(ff=f, image_width=1072, image_height=1448, margin_x=100, margin_y=200, top_row_y=250, spacing_between_sections=50)

e_today = ["Event 1", "Event 2", "Event 3", "Event 4", "Event 5"]
e_tomorrow = ["Event 6", "Event 7", ("3.30pm", "Event 8"), "Event 9", "Event 10", "Event 11", "Event 8", "Event 9", "Event 10", "Event 11"]

from datetime import datetime as dt

r.render_all(
    todays_date=dt.now().date(), 
    weather=None,
    events_today=e_today, events_tomorrow=e_tomorrow)