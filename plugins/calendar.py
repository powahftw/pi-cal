import json
from .plugin import Plugin
import os
import pickle
import iso8601
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import time
from datetime import timedelta
from datetime import datetime
import logging

CONFIG = json.load(open("config.json"))
logging = logging.getLogger(__name__)

class Calendar(Plugin):
    
    name = "CALENDAR"
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    CALENDAR_TO_USE = set(CONFIG['CAL_TO_USE'])

    def __init__(self, position):
        Plugin.__init__(self, position)
        ## Default Google Code to handle auth.
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port = 0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        try:
            logging.info("Service connection established for CALENDAR PLUGIN")
            self.service = build('calendar', 'v3', credentials = creds)
        except Exception as e:
            logging.info(f"Something went wrong while obtaining the Calendar connection. {e}")
    
    def update(self):
        calendars = self.obtain_interesting_calendar()
        self.events = self.obtain_and_merge_events(calendars)
        return self.get_events(), self.get_notification()

    def get_notification(self):
        return [f"Starting: {event['summary']}" for event in self.events if not is_all_day(event) and is_event_upcoming(event)]
    
    def get_events(self, limit = 3): 
        #all_day_events = [event for event in self.events if is_all_day(event)]
        non_all_day_events = [event for event in self.events if not is_all_day(event)]
        
        if not non_all_day_events:
            logging.info('No upcoming non-all-day-events found.')
            return []
        
        for event in non_all_day_events:
            if is_event_ongoing(event):
                print("Ongoing {}, {} min left".format(event['summary'], time_delta_from_now_formatted(event['end'])))
            else:
                print("Upcoming {}, {} min to start".format(event['summary'], time_delta_from_now_formatted(event['start'])))
        return [format_event(event) for event in non_all_day_events[:limit]]
                                        
    def obtain_interesting_calendar(self):
        res = []
        calendar_list = self.service.calendarList().list().execute()
        for calendar_list_entry in calendar_list['items']:
            if calendar_list_entry['summary'] in self.CALENDAR_TO_USE:
                res.append(calendar_list_entry['id'])
        return res
    
    def obtain_and_merge_events(self, calendars):
         # Call the Calendar API
        now = datetime.utcnow()
        now_tz = now.isoformat() + 'Z'
        max_tz = (now + timedelta(2)).isoformat() + 'Z'
        res_events = []
        for calendar in calendars:
            events_result = self.service.events().list(maxResults = 10,
                                              calendarId = calendar,
                                              timeMin = now_tz,
                                              timeMax = max_tz,
                                              singleEvents = True,
                                              orderBy = 'startTime').execute()
            events = events_result.get('items', [])
            res_events.extend(events)
            for event in events:
                if 'start' not in event: json.dumps(event, indent = 4)
        res_events.sort(key = lambda event: ambiguous_time_to_unix(event['start']))
        return res_events

### Helpers function

def format_event(event):
    if is_event_ongoing(event):
            return f"{time_delta_from_now_formatted(event['end'])}m LEFT {event['summart']}"
    else:
        formatted_time = datetime.utcfromtimestamp(ambiguous_time_to_unix(event['start'])).strftime('%H:%M')
        return f"{formatted_time} : {event['summary']}"
    
def is_all_day(event):
    return 'date' in event['start'] and 'date' in event['end']

def time_delta_from_now(time):
    now = datetime.now().timestamp()
    time = ambiguous_time_to_unix(time)
    return timedelta(seconds = time - now)

def time_delta_from_now_formatted(time):
    return format_duration(time_delta_from_now(time))

def format_duration(duration):
    """
    Nicely format an event duration eg 1H:10M
    """
    hours, remainder = divmod(duration.total_seconds(), 3600)
    minutes, _ = divmod(remainder, 60)
    res = ((str(int(hours)) + "H:") if hours > 0 else "") + str(int(minutes)) + "M"
    return res

def is_event_ongoing(event):
    return ambiguous_time_to_unix(event['start']) < \
            datetime.now().timestamp() < \
            ambiguous_time_to_unix(event['end'])

def to_unix(rfc3339time):
    return iso8601.parse_date(rfc3339time).timestamp()

def is_event_upcoming(event):
    UPCOMING_EVENT_THRESHOLD = 900
    return time_delta_from_now(event['start']).total_seconds() < UPCOMING_EVENT_THRESHOLD

def ambiguous_time_to_unix(time):
    """
    Time in calendar can both be a date if the event is a full-day-event or dateTime
    """
    if 'date' in time:
        return to_unix(time['date'])
    elif 'dateTime' in time:
        return to_unix(time['dateTime'])
    return 0