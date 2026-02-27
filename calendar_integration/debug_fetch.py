
import datetime
import os.path
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def main():
    if not os.path.exists("token.json"):
        print("token.json missing")
        return
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    service = build("calendar", "v3", credentials=creds)

    now = datetime.datetime.now(datetime.timezone.utc)
    # Start of today (Shanghai time)
    shanghai_now = now.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
    start_of_day = shanghai_now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + datetime.timedelta(days=1)
    
    time_min = start_of_day.isoformat()
    time_max = end_of_day.isoformat()

    print(f"Fetching events between {time_min} and {time_max}")
    
    calendar_list = service.calendarList().list().execute()
    for cal in calendar_list.get('items', []):
        cal_id = cal.get('id')
        cal_name = cal.get('summary')
        
        print(f"\nChecking Calendar: {cal_name} (ID: {cal_id})")
        events_result = service.events().list(
            calendarId=cal_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        events = events_result.get("items", [])
        if not events:
            print("  No events found.")
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            summary = event.get('summary', 'No Title')
            uid = event.get('id')
            print(f"  [{start}] {summary} (ID: {uid})")

if __name__ == "__main__":
    main()
