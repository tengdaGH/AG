
import os.path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def main():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    service = build("calendar", "v3", credentials=creds)

    calendar_list = service.calendarList().list().execute()
    for cal in calendar_list.get('items', []):
        name = cal.get('summary')
        bg = cal.get('backgroundColor')
        fg = cal.get('foregroundColor')
        print(f"- {name}: BG={bg}, FG={fg}")

if __name__ == "__main__":
    main()
