
import os.path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def main():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    service = build("calendar", "v3", credentials=creds)

    print(f"Full list of all calendars in the account...")
    
    calendar_list = service.calendarList().list().execute()
    for cal in calendar_list.get('items', []):
        name = cal.get('summary')
        id = cal.get('id')
        primary = cal.get('primary', False)
        print(f"- Name: '{name}', ID: '{id}', Primary: {primary}")

if __name__ == "__main__":
    main()
