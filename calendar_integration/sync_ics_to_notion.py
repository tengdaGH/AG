
import os
import requests
import re
import datetime
import json
import zoneinfo
import sys

# Notion Configuration
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_DB_ID = "3125eb7b-e7e4-8057-8135-c6708b63ed5e"

# ICS Feeds
ICS_FEEDS = {
    "Miya": "https://p235-caldav.icloud.com.cn/published/2/ODE0NTU3NDA4NzgxNDU1N5a7oJG6Offg5NzyJNtGUnjgoiOkv5PFGc8AbHw6VVae6__dE6CfiFmiu9BoMcUHNwgq4C2AeVeJbuTwRlWZaoU",
    "Rita": "https://p235-caldav.icloud.com.cn/published/2/ODE0NTU3NDA4NzgxNDU1N5a7oJG6Offg5NzyJNtGUngnLMbawCT_bon3iWGIba7YM84yuUlE7Idh5jWX1bDCHZKbzA8hrxpLI2_Xowoz3NU",
    "月月": "https://p235-caldav.icloud.com.cn/published/2/ODE0NTU3NDA4NzgxNDU1N5a7oJG6Offg5NzyJNtGUnhjf_1D8Xs4kSFfKit5JqAv6xA4A4idWDEIz-quwP9634_Qo0Wp21-tGyBGvEpEi5g",
    "达哥": "https://p235-caldav.icloud.com.cn/published/2/ODE0NTU3NDA4NzgxNDU1N5a7oJG6Offg5NzyJNtGUnjL2uWOtR1ag7v1hzo5u_PgGOG5Sa6gmMjGSlEVV_JFPYzif3IWvBkmDfpwwWeiT-k"
}

SHANGHAI_TZ = zoneinfo.ZoneInfo("Asia/Shanghai")

def get_notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

def get_notion_events(time_min_date_str):
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

def parse_ics_date(date_str):
    """Parses 20260227T103000 or 20260227 into a naive datetime or date string."""
    if 'T' in date_str:
        # 20260227T103000Z or 20260227T103000
        clean_str = date_str.replace('Z', '')
        dt = datetime.datetime.strptime(clean_str[:15], "%Y%m%dT%H%M%S")
        return dt, False
    else:
        # 20260227
        dt = datetime.datetime.strptime(date_str[:8], "%Y%m%d")
        return dt, True

def format_for_notion(dt, is_all_day):
    if is_all_day:
        return dt.strftime("%Y-%m-%d")
    # iCloud dates are assumed to be Asia/Shanghai in this context or converted from UTC
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

def build_notion_properties(summary, start_dt, end_dt, is_all_day, teacher, uid):
    date_obj = {
        "start": format_for_notion(start_dt, is_all_day),
        "end": format_for_notion(end_dt, is_all_day)
    }
    if not is_all_day:
        date_obj["time_zone"] = "Asia/Shanghai"

    return {
        "Name": {"title": [{"text": {"content": summary}}]},
        "教师": {"select": {"name": teacher}},
        "UID": {"rich_text": [{"text": {"content": uid}}]},
        "Start": {"date": date_obj}
    }

def create_notion_page(summary, start_dt, end_dt, is_all_day, teacher, uid):
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": build_notion_properties(summary, start_dt, end_dt, is_all_day, teacher, uid)
    }
    resp = requests.post(url, headers=get_notion_headers(), json=payload)
    if resp.status_code != 200:
        print(f"Failed to insert {summary}: {resp.text}")
    else:
        print(f"Inserted: {summary} ({teacher})")

def update_notion_page(page_id, summary, start_dt, end_dt, is_all_day, teacher, uid):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": build_notion_properties(summary, start_dt, end_dt, is_all_day, teacher, uid)
    }
    resp = requests.patch(url, headers=get_notion_headers(), json=payload)
    if resp.status_code != 200:
        print(f"Failed to update {summary}: {resp.text}")
    else:
        print(f"Updated: {summary} ({teacher})")

def delete_notion_page(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"archived": True}
    requests.patch(url, headers=get_notion_headers(), json=payload)

def main():
    if not NOTION_TOKEN:
        print("FATAL: NOTION_TOKEN not set.")
        sys.exit(1)

    now = datetime.datetime.now(datetime.timezone.utc).astimezone(SHANGHAI_TZ)
    time_min_obj = now - datetime.timedelta(days=30)
    time_max_obj = now + datetime.timedelta(days=30)
    
    time_min_date_str = time_min_obj.strftime('%Y-%m-%d')
    
    print(f"Fetching existing Notion events from {time_min_date_str}...")
    try:
        existing_uids = get_notion_events(time_min_date_str)
        print(f"Found {len(existing_uids)} existing events in Notion database.")
    except Exception as e:
        print(f"Failed to access Notion database: {e}")
        sys.exit(1)

    seen_ics_uids = set()
    new_inserts = 0
    updates = 0

    for teacher, url in ICS_FEEDS.items():
        print(f"\n--- Syncing {teacher} ---")
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            content = resp.text
        except Exception as e:
            print(f"Failed to fetch ICS for {teacher}: {e}")
            continue

        # Unfold folded lines in ICS
        content = content.replace("\r\n ", "")
        content = content.replace("\n ", "")
        
        events = re.findall(r"BEGIN:VEVENT.*?END:VEVENT", content, re.DOTALL)
        for event_block in events:
            uid_match = re.search(r"UID:(.*?)(?:\r?\n|$)", event_block)
            summary_match = re.search(r"SUMMARY:(.*?)(?:\r?\n|$)", event_block)
            dtstart_match = re.search(r"DTSTART.*?:(\d{8}T?\d{0,6}Z?)", event_block)
            dtend_match = re.search(r"DTEND.*?:(\d{8}T?\d{0,6}Z?)", event_block)
            
            if not uid_match or not summary_match or not dtstart_match:
                continue
                
            uid = uid_match.group(1).strip()
            summary = summary_match.group(1).strip()
            start_dt, is_all_day = parse_ics_date(dtstart_match.group(1).strip())
            
            if dtend_match:
                end_dt, _ = parse_ics_date(dtend_match.group(1).strip())
            else:
                end_dt = start_dt + datetime.timedelta(hours=1)

            # Check if event is within our 60-day window
            # We use naive comparisons here since we assume iCloud dates are local or handled via Z
            if start_dt.date() < time_min_obj.date() or start_dt.date() > time_max_obj.date():
                continue

            seen_ics_uids.add(uid)

            if uid in existing_uids:
                update_notion_page(existing_uids[uid], summary, start_dt, end_dt, is_all_day, teacher, uid)
                updates += 1
            else:
                create_notion_page(summary, start_dt, end_dt, is_all_day, teacher, uid)
                new_inserts += 1

    # Clean up deleted events in Notion
    deleted = 0
    for uid, page_id in existing_uids.items():
        if uid not in seen_ics_uids:
            delete_notion_page(page_id)
            print(f"Deleted (archived) obsolete Notion event: {uid}")
            deleted += 1

    print(f"\nDone! Inserted: {new_inserts}, Updated: {updates}, Deleted: {deleted}.")

if __name__ == "__main__":
    main()
