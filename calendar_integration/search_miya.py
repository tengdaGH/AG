
import os.path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def main():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    service = build("calendar", "v3", credentials=creds)

    print(f"Searching ALL calendars for summary containing 'miya'...")
    
    calendar_list = service.calendarList().list().execute()
    for cal in calendar_list.get('items', []):
        cal_name = cal.get('summary')
        cal_id = cal.get('id')
        
        events_result = service.events().list(
            calendarId=cal_id,
            timeMin="2026-02-27T00:00:00Z",
            timeMax="2026-02-27T23:59:59Z",
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        events = events_result.get("items", [])
        for event in events:
            summary = event.get('summary', '').lower()
            if "miya" in summary:
                start = event["start"].get("dateTime", event["start"].get("date"))
                print(f"  [{cal_name}] [{start}] {event.get('summary')}")

if __name__ == "__main__":
    main()
