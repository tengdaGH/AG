import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                print("Error: credentials.json not found.")
                return
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # 1. First, get all calendars in the user's list
        print("Fetching your calendar list...")
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        if not calendars:
            print("No calendars found.")
            return

        print("\n=== Available Calendars ===")
        for cal in calendars:
            print(f"- {cal.get('summary')} (ID: {cal.get('id')})")

        print("\n=== Upcoming Events from All Calendars ===")
        # Use timezone-aware datetime for UTC
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        for cal in calendars:
            cal_id = cal.get('id')
            cal_name = cal.get('summary')
            try:
                events_result = (
                    service.events()
                    .list(
                        calendarId=cal_id,
                        timeMin=now,
                        maxResults=5,
                        singleEvents=True,
                        orderBy="startTime",
                    )
                    .execute()
                )
                events = events_result.get("items", [])
                
                if events:
                    print(f"\n[{cal_name}]:")
                    for event in events:
                        start = event["start"].get("dateTime", event["start"].get("date"))
                        print(f"  {start} - {event.get('summary', 'No Title')}")
            except HttpError as error:
                print(f"  [Error fetching {cal_name}]: {error}")

    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()
