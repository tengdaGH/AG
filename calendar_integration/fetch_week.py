import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def main():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    service = build("calendar", "v3", credentials=creds)

    calendar_list = service.calendarList().list().execute()
    calendars = calendar_list.get('items', [])
    
    # Let's fetch events for the specific week of Feb 22 to Feb 28, 2026
    time_min = "2026-02-22T00:00:00Z"
    time_max = "2026-02-28T23:59:59Z"

    print("=== Events for Feb 22 - 28, 2026 ===")
    
    for cal in calendars:
        cal_id = cal.get('id')
        cal_name = cal.get('summary')
        
        # skip primary
        if cal_id == "tengda@gmail.com":
            continue
            
        try:
            events_result = (
                service.events()
                .list(
                    calendarId=cal_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=50,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])
            
            if events:
                print(f"\n[{cal_name}] ({len(events)} events):")
                for event in events:
                    start = event["start"].get("dateTime", event["start"].get("date"))
                    print(f"  {start} - {event.get('summary', 'No Title')}")
            else:
                print(f"\n[{cal_name}]: No events found in this date range.")
        except Exception as error:
            print(f"  [Error fetching {cal_name}]: {error}")

if __name__ == "__main__":
    main()
