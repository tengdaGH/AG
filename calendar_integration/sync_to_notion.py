import datetime
import sys
import os.path
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import json

# Fetching Notion token from environment, with a fallback for local testing
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_DB_ID = "3125eb7b-e7e4-8057-8135-c6708b63ed5e"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
TARGET_CALS = ["Miya", "Rita", "月月", "tengda@gmail.com", "达哥"]

def get_notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

def get_notion_events(time_min_date_str):
    """Fetch existing UIDs from Notion, filtering to pages starting after time_min to avoid deleting past events"""
    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    existing_events = {}
    has_more = True
    next_cursor = None

    while has_more:
        payload = {
            "page_size": 100,
            "filter": {
                "property": "Start",
                "date": {
                    "on_or_after": time_min_date_str
                }
            }
        }
        if next_cursor:
            payload["start_cursor"] = next_cursor
        
        response = requests.post(url, headers=get_notion_headers(), json=payload)
        response.raise_for_status()
        data = response.json()
        
        for page in data.get("results", []):
            props = page.get("properties", {})
            page_id = page["id"]
            
            uid_prop = props.get("UID", {}).get("rich_text", [])
            if uid_prop:
                uid = uid_prop[0].get("plain_text")
                existing_events[uid] = page_id
                
        has_more = data.get("has_more")
        next_cursor = data.get("next_cursor")

    return existing_events

import zoneinfo
import datetime as dt

def format_for_notion(iso_str):
    if not iso_str:
        return None
    # Google sometimes sends "Z" for UTC. Python's fromisoformat in older versions needs +00:00
    if iso_str.endswith("Z"):
        iso_str = iso_str[:-1] + "+00:00"
        
    date_obj = dt.datetime.fromisoformat(iso_str)
    shanghai_tz = zoneinfo.ZoneInfo("Asia/Shanghai")
    dt_shanghai = date_obj.astimezone(shanghai_tz)
    
    # Notion requires strictly no-offset ISO string if time_zone property is explicitly provided
    return dt_shanghai.strftime("%Y-%m-%dT%H:%M:%S")

def build_notion_properties(event, cal_name, uid):
    start_time_iso = event["start"].get("dateTime")
    is_all_day = False
    if not start_time_iso:
        # It's an all-day event
        start_time_iso = event["start"].get("date")
        is_all_day = True
    else:
        start_time_iso = format_for_notion(start_time_iso)
        
    end_time_iso = event["end"].get("dateTime")
    if not end_time_iso:
        end_time_iso = event["end"].get("date")
    else:
        end_time_iso = format_for_notion(end_time_iso)

    title = event.get("summary", "Untitled Course")
    
    if cal_name == "tengda@gmail.com":
        cal_name = "达哥"

    # Explicitly set time_zone so Notion knows this is Shanghai time,
    # preventing it from showing UTC in the UI popup.
    date_obj = {
        "start": start_time_iso,
        "end": end_time_iso
    }
    if not is_all_day:
        date_obj["time_zone"] = "Asia/Shanghai"

    return {
        "Name": {"title": [{"text": {"content": title}}]},
        "教师": {"select": {"name": cal_name}},
        "UID": {"rich_text": [{"text": {"content": uid}}]},
        "Start": {"date": date_obj}
    }

def create_notion_page(event, cal_name, uid):
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": build_notion_properties(event, cal_name, uid)
    }
    resp = requests.post(url, headers=get_notion_headers(), json=payload)
    if resp.status_code != 200:
        print(f"Failed to insert {event.get('summary')}: {resp.text}")
    else:
        print(f"Inserted: {event.get('summary')}")

def update_notion_page(page_id, event, cal_name, uid):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": build_notion_properties(event, cal_name, uid)
    }
    resp = requests.patch(url, headers=get_notion_headers(), json=payload)
    if resp.status_code != 200:
        print(f"Failed to update {event.get('summary')}: {resp.text}")
    else:
        print(f"Updated: {event.get('summary')}")

def delete_notion_page(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"archived": True}
    requests.patch(url, headers=get_notion_headers(), json=payload)

def main():
    google_token_env = os.environ.get("GOOGLE_TOKEN_JSON")
    if google_token_env:
        # Load credentials directly from the environment variable (for GitHub Actions)
        token_info = json.loads(google_token_env)
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)
    else:
        # Fallback to local token.json file
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
    service = build("calendar", "v3", credentials=creds)

    # Sync window: 30 days in the past + 30 days in the future (60-day rolling window)
    now = datetime.datetime.now(datetime.timezone.utc)
    time_min_obj = now - datetime.timedelta(days=30)

    time_min_date_str = time_min_obj.strftime('%Y-%m-%d')
    time_min = time_min_obj.isoformat()
    time_max = (now + datetime.timedelta(days=30)).isoformat()

    print(f"Fetching existing Notion events strictly from {time_min_date_str} to avoid archiving old data...")
    try:
        existing_uids = get_notion_events(time_min_date_str)
        print(f"Found {len(existing_uids)} existing events in Notion database.")
    except Exception as e:
        print(f"Failed to access Notion database: {e}")
        print("FATAL: Aborting sync due to Notion API error. Check NOTION_TOKEN secret.")
        sys.exit(1)

    calendar_list = service.calendarList().list().execute()
    calendars = calendar_list.get('items', [])

    print("\n=== Syncing events (One-Way: Google -> Notion) ===")
    
    seen_google_uids = set()
    new_inserts = 0
    updates = 0

    for cal in calendars:
        cal_id = cal.get('id')
        cal_name = cal.get('summary')
        
        if cal_name not in TARGET_CALS and cal_id not in TARGET_CALS:
            continue
            
        try:
            page_token = None
            while True:
                events_result = service.events().list(
                    calendarId=cal_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=2500,
                    singleEvents=True,
                    orderBy="startTime",
                    pageToken=page_token
                ).execute()
                
                events = events_result.get("items", [])
                for event in events:
                    uid = event.get('id')
                    seen_google_uids.add(uid)

                    if uid in existing_uids:
                        # ALWAYS UPDATE existing records to overwrite them based on Google's final truth
                        update_notion_page(existing_uids[uid], event, cal_name, uid)
                        updates += 1
                    else:
                        create_notion_page(event, cal_name, uid)
                        new_inserts += 1
                
                page_token = events_result.get('nextPageToken')
                if not page_token:
                    break

        except Exception as error:
            print(f"  [Error fetching {cal_name}]: {error}")

    # Remove events in Notion that were deleted in Google Calendar
    deleted = 0
    for uid, page_id in existing_uids.items():
        if uid not in seen_google_uids:
            delete_notion_page(page_id)
            print(f"Deleted (archived) obsolete Notion event for UID: {uid}")
            deleted += 1
            
    print(f"\nDone! Inserted: {new_inserts}, Updated: {updates}, Deleted: {deleted}.")

if __name__ == "__main__":
    main()
