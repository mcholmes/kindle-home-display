"""
This project is designed for the Inkplate 10 display. However, since the server code is only generating an image, it can
be easily adapted to other display sizes and resolution by adjusting the config settings, HTML template and
CSS stylesheet. This code is heavily adapted from my other project (MagInkCal) so do take a look at it if you're keen.
As a dashboard, there are many other things that could be displayed, and it can be done as long as you are able to
retrieve the information. So feel free to change up the code and amend it to your needs.
"""

import logging
import sys
import json
from pytz import timezone
from gcal.gcal import Calendar

if __name__ == '__main__':
    logger = logging.getLogger('maginkdash')

    with open('api_keys.json') as apiFile:
        api = json.load(apiFile)

    
    calendar_ids = [
        "r45mcf74fb3fmv84v108q3hsgjvi46ds@import.calendar.google.com", # holmbergs todoist
        "10a2dd68e51bb17689c7ccf4f4722d1f445c59c86430577b425c33ccee27be2e@group.calendar.google.com" # holmbergs shared cal
    ]
    display_timezone = timezone("Europe/London") 
    calendar_days_to_show = 2
    
    # Create and configure logger
    logging.basicConfig(filename="logfile.log", format='%(asctime)s %(levelname)s - %(message)s', filemode='a')
    logger = logging.getLogger('maginkdash')
    logger.addHandler(logging.StreamHandler(sys.stdout))  # print logger to stdout
    logger.setLevel(logging.INFO)
    logger.info("Starting dashboard update")

    # Retrieve Calendar Data
    cal = Calendar(calendar_ids, display_timezone, calendar_days_to_show)
    
    events = cal.get_daywise_events()

    events_today = events[0]
    print(events)

    # events_tomorrow = events[1]
    # print()
    # print("Tomorrow: ", events_tomorrow)