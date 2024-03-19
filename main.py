import logging
import sys
import json
from datetime import time
from pytz import timezone
from cal.cal import Calendar
from owm.owm import OWMModule
from render.font_helper import FontFactory
from render.render_helper import Renderer

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    # Create and configure logger
    logging.basicConfig(filename="logfile.log", format='%(asctime)s %(levelname)s - %(message)s', filemode='a')
    logger.addHandler(logging.StreamHandler(sys.stdout))  # print logger to stdout
    logger.setLevel(logging.INFO)

    # Basic configuration settings (user replaceable)
    logger.info("Getting config data")
    with open('config.json') as configFile:
        config = json.load(configFile)

    with open('api_keys.json') as apiFile:
        api = json.load(apiFile)

    calendar_ids = config['calendars'] # Google Calendar IDs
    display_timezone = timezone(config['displayTZ']) # list of timezones - print(pytz.all_timezones)
    calendar_days_to_show = config['numCalDaysToShow'] # Number of days to retrieve from gcal, keep to 3 unless other parts of the code are changed too
    
    imageWidth = config['imageWidth']  # Width of image to be generated for display.
    imageHeight = config['imageHeight']  # Height of image to be generated for display.
    rotateAngle = config['rotateAngle']  # If image is rendered in portrait orientation, angle to rotate to fit screen
    
    openai_api_key = api["openai_api_key"]  # OpenAI API key. Required to retrieve response from ChatGPT
    path_to_server_image = config["path_to_server_image"]  # Location to save the generated image


    # # Retrieve Weather Data
    # owm_api_key = api["owm_api_key"]  # OpenWeatherMap API key. Required to retrieve weather forecast.
    # lat = config["lat"] # Latitude in decimal of the location to retrieve weather forecast for
    # lon = config["lon"] # Longitude in decimal of the location to retrieve weather forecast for
    # owmModule = OWMModule()
    # current_weather, hourly_forecast, daily_forecast = owmModule.get_weather(lat, lon, owm_api_key, from_cache=True)
    # # current_weather_text=string.capwords(hourly_forecast[1]["weather"][0]["description"]),
    # # current_weather_id=hourly_forecast[1]["weather"][0]["id"],
    # # current_weather_temp=round(hourly_forecast[1]["temp"]),

    # Retrieve Calendar Data
    logger.info("Getting calendar data")
    cal = Calendar(calendar_ids, display_timezone, calendar_days_to_show)
    events = cal.get_daywise_events()

    # Render Dashboard Image
    font_map = {
            "extralight": "Lexend-ExtraLight.ttf", 
            "light": "Lexend-Light.ttf", 
            "regular": "Lexend-Regular.ttf", 
            "bold": "Lexend-Bold.ttf",
            "extrabold": "Lexend-ExtraBold.ttf",
            "weather": "weathericons-regular-webfont.ttf"
        }

    f = FontFactory("/Users/mike.holmes/projects/home-display/render/font",font_map)
    r = Renderer(ff=f, image_width=imageWidth, image_height=imageHeight, 
                 margin_x=100, margin_y=200, top_row_y=250, spacing_between_sections=50,
                 output_filepath=path_to_server_image
                 )
 
    def sort_by_time(events: list[dict]):
        return sorted(events, key = lambda x: x.get("start_time", time.min))

    events_today = sort_by_time(events.get(0, []))
    events_tomorrow = sort_by_time(events.get(1, []))


    logger.info("Rendering image")
    r.render_all(
        todays_date=cal.get_current_date(), 
        weather=None,
        events_today=events_today, 
        events_tomorrow=events_tomorrow)

    logger.info("Completed dashboard update")