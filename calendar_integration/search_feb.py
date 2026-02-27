
import datetime
import os.path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def main():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    service = build("calendar", "v3", credentials=creds)

    time_min = "2026-02-01T00:00:00Z"
    time_max = "2026-02-28T23:59:59Z"

    print(f"Searching February events for Miya...")
    
    calendar_list = service.calendarList().list().execute()
    for cal in calendar_list.get('items', []):
        if cal.get('summary') == "Miya":
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
            print(f"Found {len(events)} events.")
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                summary = event.get('summary', 'No Title')
                if "贺贺" in summary or "皮皮" in summary:
                    print(f"  [{start}] {summary}")

if __name__ == "__main__":
    main()
