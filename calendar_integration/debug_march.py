
import datetime
import os.path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def main():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    service = build("calendar", "v3", credentials=creds)

    # Fetch events for March 2026
    time_min = "2026-03-01T00:00:00Z"
    time_max = "2026-03-07T23:59:59Z"

    print(f"Fetching events for {time_min} to {time_max}")
    
    calendar_list = service.calendarList().list().execute()
    for cal in calendar_list.get('items', []):
        cal_name = cal.get('summary')
        cal_id = cal.get('id')
        
        # Focus on Miya
        if cal_name != "Miya":
            continue
            
        events_result = service.events().list(
            calendarId=cal_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        events = events_result.get("items", [])
        print(f"\n[{cal_name}]:")
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(f"  {start} - {event.get('summary', 'No Title')}")

if __name__ == "__main__":
    main()
