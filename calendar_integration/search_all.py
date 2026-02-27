
import datetime
import os.path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def main():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    service = build("calendar", "v3", credentials=creds)

    time_min = "2026-02-20T00:00:00Z" # Start a week ago
    time_max = "2026-03-05T23:59:59Z" # End a week from now

    print(f"Searching ALL calendars for missing classes...")
    
    calendar_list = service.calendarList().list().execute()
    for cal in calendar_list.get('items', []):
        cal_name = cal.get('summary')
        cal_id = cal.get('id')
        
        events_result = service.events().list(
            calendarId=cal_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=2500
        ).execute()
        
        events = events_result.get("items", [])
        for event in events:
            summary = event.get('summary', 'No Title')
            if "贺贺" in summary or "皮皮" in summary:
                start = event["start"].get("dateTime", event["start"].get("date"))
                print(f"  [{cal_name}] [{start}] {summary}")

if __name__ == "__main__":
    main()
