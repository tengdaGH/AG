import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
creds = Credentials.from_authorized_user_file("token.json", SCOPES)
service = build("calendar", "v3", credentials=creds)

TARGET_CALS = ["Miya", "Rita", "月月", "tengda@gmail.com", "达哥"]

calendar_list = service.calendarList().list().execute()
for cal in calendar_list.get('items', []):
    cal_name = cal.get('summary')
    cal_id = cal.get('id')
    if cal_name in TARGET_CALS or cal_id in TARGET_CALS:
        print("Checking calendar:", cal_name)
        events_result = service.events().list(
            calendarId=cal_id,
            timeMin="2026-02-25T00:00:00Z",
            timeMax="2026-03-05T00:00:00Z",
            maxResults=3,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        for event in events_result.get('items', []):
            print("  Found:", event.get('summary'))
            print("  Start:", event['start'])
