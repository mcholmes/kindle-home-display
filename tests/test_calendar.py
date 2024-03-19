import json
from pytz import timezone
from cal.cal import Calendar

if __name__ == '__main__':

    with open('api_keys.json') as apiFile:
        api = json.load(apiFile)

    calendar_ids = [
        "r45mcf74fb3fmv84v108q3hsgjvi46ds@import.calendar.google.com", # holmbergs todoist
        "10a2dd68e51bb17689c7ccf4f4722d1f445c59c86430577b425c33ccee27be2e@group.calendar.google.com" # holmbergs shared cal
    ]
    display_timezone = timezone("Europe/London") 
    calendar_days_to_show = 2

    # Retrieve Calendar Data
    cal = Calendar(calendar_ids, display_timezone, calendar_days_to_show)
    
    events = cal.get_daywise_events()

    events_today = events[0]
    print(events)

    # events_tomorrow = events[1]
    # print()
    # print("Tomorrow: ", events_tomorrow)