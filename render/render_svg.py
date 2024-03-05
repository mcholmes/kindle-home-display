from PIL import Image, ImageDraw, ImageFont

# TODO: tidy up how fonts are loaded and stored in dicts – see what you need in the actual dash

# Define font properties
font_color = "black"
font_sizes = {
    "light": 48, 
    "regular": 48,
    "bold": 200,
    "weather": 150
}

font_dir = "/Users/mike.holmes/projects/home-display/render/font/"
font_names = {
    "light": "Lexend-Light.ttf", 
    "regular": "Lexend-Regular.ttf", 
    "bold": "Lexend-Bold.ttf",
    "weather": "weathericons-regular-webfont.ttf"}

# Create font objects
fonts = {style: ImageFont.truetype(font_dir + font_names[style], font_sizes[style]) for style in font_sizes}

# Define image size and background color
image_width, image_height = 1072, 1448
background_color = "white"
margin_l = 100
margin_r = 100

centre_h = image_width/2
centre_v = image_height/2

# Create a new image with a white background
image = Image.new("RGB", (image_width, image_height), background_color)
draw = ImageDraw.Draw(image)
# draw.font = ImageFont.truetype("/Users/mike.holmes/projects/home-display/render/font/Lexend-Regular.ttf") # default


# Define current date and weather (replace these with actual values)
day_num = "24"
day_name = "Mon"
month = "Feb"
weather = "Broken clouds | 11º"
weather_icon = "\uf00d"

# Top row
toprow_baseline = 250
space_below_toprow = 150

# Date
draw.text((margin_l,toprow_baseline), f"{day_num}", font=fonts["bold"], fill="black", anchor="ls")

# TODO: 
# - get this working with multiline (i.e. day name)
# - move it left/right depending on width of date
draw.text((380,toprow_baseline), f"{month}", font=fonts["regular"], fill="gray", anchor="ls")

# Weather
# TODO: 
# - map this to openweathermap id
# - Add temperature
draw.text((image_width-margin_r,toprow_baseline), f"{weather_icon}", font=fonts["weather"], fill="black", anchor="rb")

# Cal - today
# TODO: horizontal line either side of title extending to margins
pos_today_title = toprow_baseline + space_below_toprow
draw.text((centre_h,pos_today_title), "Today", font=fonts["regular"], fill="gray", anchor="ms")

def list_to_bullets(list):
    return "\n".join([f"•   {x}" for x in list])

events_today = [
    "Today's event 1",
    "Event 2",
    "event 3",
    "event 4",
    "event 5"
]

ascent, descent = fonts["regular"].getmetrics()
height_regular_font = ascent+descent

draw.text((margin_l,pos_today_title + height_regular_font), list_to_bullets(events_today), font=fonts["regular"], fill="black", anchor="ls", align="left")

# Cal - tomorrow
pos_tomorrow_title = pos_today_title + (height_regular_font * (1+len(events_today)))
draw.text((centre_h,pos_tomorrow_title), "Tomorrow", font=fonts["regular"], fill="gray", anchor="ms")

events_tomorrow = [
    "Tomorrow's event 1",
    "Event 2",
    "event 3"
]
draw.text((margin_l,pos_tomorrow_title + height_regular_font), list_to_bullets(events_tomorrow), font=fonts["regular"], fill="black", anchor="ls", align="left")

# Save the image as PNG
image.save("dashboard_test.png")