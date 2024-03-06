from PIL import Image, ImageDraw
from font_helper import FontFactory
import os
import pathlib
import logging

"""
TODO:
- decide what to do with weather. next N hours? just icon/temp? 
"""


# Constants
IMAGE_WIDTH, IMAGE_HEIGHT = 1072, 1448
TOP_ROW_Y = 250  # y-coordinate for the baseline of the top row
SPACING_BETWEEN_SECTIONS = 50  # spacing between sections
MARGIN_X = 100
MARGIN_Y = 200
BACKGROUND_COLOR = "white"

class Renderer:

    def __init__(self,
                 image_width, image_height,
                 margin_x, margin_y,
                 top_row_y, spacing_between_sections,
                 bg_colour="white",
                 font_map=None):
            
            self.logger = logging.getLogger('maginkdash')
            self.image = Image.new("RGB", (image_width, image_height), bg_colour)
            self.draw = ImageDraw.Draw(image)

# Create the SVG image
image = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), BACKGROUND_COLOR)
draw = ImageDraw.Draw(image)
    
def render_events(section_title, bullet_points, y):
    """Renders a section with a title and bullet points starting at the given y-coordinate."""

    event_title = ff.get("light")
    event_reg = ff.get("regular")

    # Title
    title_width = event_title.width(section_title)
    title_pos_x = IMAGE_WIDTH//2
    draw.text((title_pos_x, y), section_title, font=event_title.font(), fill="gray", anchor="mm")

    line_x_l = title_pos_x - (title_width//2 + 50)
    line_x_r = title_pos_x + (title_width//2 + 50)

    draw.line([MARGIN_X,y,line_x_l,y], fill="gray", width=1)
    draw.line([line_x_r,y,IMAGE_WIDTH-MARGIN_X,y], fill="gray", width=1)
    
    y += event_title.height()  # Add spacing after the title

    # Bullets
    f = event_reg.font()
    bullet_height = event_reg.height()
    for index, bullet in enumerate(bullet_points):
        if y > IMAGE_HEIGHT - MARGIN_Y:
            draw.text((MARGIN_X, y), f"     + {len(bullet_points)-index} more...", font=f, fill="black")
            break
        
        if type(bullet) == str:
            draw.text((MARGIN_X, y), "• " + bullet, font=f, fill="black")
        elif type(bullet) == tuple:
            event_time = bullet[0] + " "
            event_text = bullet[1]

            width_time = event_reg.width(event_time)
            width_text = event_reg.width(event_text)
            width_bp = event_reg.width("• ") # bp = bulletpoint symbol

            x_bp = MARGIN_X
            x_time = x_bp + width_bp 
            x_text = x_time + width_time

            draw.text((x_bp, y), "• ", font=f, fill="black")
            draw.text((x_time, y), event_time, font=f, fill="gray")
            draw.text((x_text, y), event_text, font=f, fill="black")
                
        y += bullet_height + 5  # Add spacing between bullet points

    return y

def render_date(day, day_of_week, month):

    date_num = ff.get("bold", 200)
    date_rest = ff.get("regular")
    
    draw.text((MARGIN_X, TOP_ROW_Y), day, font=date_num.font(), fill="black", anchor="ls")
    day_width = date_num.width(day)

    draw.text((MARGIN_X + day_width + 10, TOP_ROW_Y), day_of_week, font=date_rest.font(), fill="gray", anchor="ls")
    draw.text((MARGIN_X + day_width + 10, TOP_ROW_Y - date_rest.height()), month, font=date_rest.font(), fill="gray", anchor="ls")

def render_weather(text, icon):

    weather_icon = ff.get("weather", 150)
    weather_text = ff.get("regular")

    draw.text((IMAGE_WIDTH-MARGIN_X-weather_text.width(text), TOP_ROW_Y), text, font=weather_text.font(), fill="gray", anchor="ls")
    draw.text((IMAGE_WIDTH-MARGIN_X-weather_icon.width(icon), TOP_ROW_Y - weather_text.height()), icon, font=weather_icon.font(), fill="black", anchor="ls")

font_map = {
        "light": "Lexend-Light.ttf", 
        "regular": "Lexend-Regular.ttf", 
        "bold": "Lexend-Bold.ttf",
        "extrabold": "Lexend-ExtraBold.ttf",
        "weather": "weathericons-regular-webfont.ttf"
}

ff = FontFactory("/Users/mike.holmes/projects/home-display/render/font",font_map)

# Render top row
render_date(day="24", day_of_week="Mon", month="Feb")
# render_weather(text="Broken clouds | 11º", icon="\uf00d")

# Render the "Today" section
events_today = ["Event 1", "Event 2", "Event 3", "Event 4", "Event 5"]
y = TOP_ROW_Y + SPACING_BETWEEN_SECTIONS
y = render_events("Today", events_today, y)

# Render the "Tomorrow" section
events_tomorrow = ["Event 6", "Event 7", ("3.30pm", "Event 8"), "Event 9", "Event 10", "Event 11", "Event 8", "Event 9", "Event 10", "Event 11"]
y += SPACING_BETWEEN_SECTIONS
render_events("Tomorrow", events_tomorrow, y)

# Save the image
image.save("output.png")