
import datetime
import os.path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def main():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    service = build("calendar", "v3", credentials=creds)

    time_min = "2026-02-23T00:00:00Z"
    time_max = "2026-03-02T23:59:59Z"

    print(f"Searching ALL calendars with UIDs...")
    
    calendar_list = service.calendarList().list().execute()
    for cal in calendar_list.get('items', []):
        cal_name = cal.get('summary')
        cal_id = cal.get('id')
        
        if cal_name not in ["Miya", "Rita", "月月", "达哥", "露露"]:
            continue

        events_result = service.events().list(
            calendarId=cal_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=2500
        ).execute()
        
        events = events_result.get("items", [])
        print(f"\n[{cal_name}]:")
        for event in events:
            summary = event.get('summary', 'No Title')
            start = event["start"].get("dateTime", event["start"].get("date"))
            uid = event.get('id')
            print(f"  [{start}] {summary} (UID: {uid})")

if __name__ == "__main__":
    main()
