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
        return self.get_events(), self.starting_soon_events()

    def starting_soon_events(self):
        """
        Obtain a formatted list of events starting soon. 
        """
        starting_soon = lambda event: not is_all_day(event) and is_event_upcoming(event)
        return [f"Starting: {event['summary']}" for event in self.events if starting_soon(event)]
    
    def get_events(self, limit = 3): 
        """
        Obtain at most {limit} number of non_all_day_events.
        """
        non_all_day_events = [event for event in self.events if not is_all_day(event)]
        
        if not non_all_day_events:
            logging.info('No upcoming non-all-day-events found.')
            return []
        
        return [format_event(event) for event in non_all_day_events[:limit]]
                                        
    def obtain_interesting_calendar(self):
        """
        Return a list of calendar's id that the user is interested in, based on config.json settings.
        """
        res = []
        calendar_list = self.service.calendarList().list().execute()
        for calendar_list_entry in calendar_list['items']:
            if calendar_list_entry['summary'] in self.CALENDAR_TO_USE:
                res.append(calendar_list_entry['id'])
        return res
    
    def obtain_and_merge_events(self, calendars):
        """
        Obtain events from differents calendars and merge them togheter, sorted by start_time.
        """
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
    """
    Format a given event
    eg: 14:10 : Meeting X, 10m LEFT : Meeting
    """
    if is_event_ongoing(event):
        return f"{time_delta_from_now_formatted(event['end'])} LEFT : {event['summary']}"
    else:
        formatted_time = datetime.utcfromtimestamp(ambiguous_time_to_unix(event['start'])).strftime('%H:%M')
        return f"{formatted_time} : {event['summary']}"
    
def is_all_day(event):
    # We consider events longer then 12h as full day
    start, end = event['start'], event['end']
    return ('date' in start and 'date' in end or
        time_diff(start, end) > timedelta(hours = 12))

def time_diff(start, end):
    start = ambiguous_time_to_unix(start)
    end = ambiguous_time_to_unix(end)
    return timedelta(seconds = end - start)

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
    Time in calendar can both be a date if the event is a full-day-event or dateTime #TODO Ex
    """
    if 'date' in time:
        return to_unix(time['date'])
    elif 'dateTime' in time:
        return to_unix(time['dateTime'])
    return 0