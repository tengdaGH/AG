
import requests
import re
from datetime import datetime

def fetch_and_parse_ics(url):
    print(f"Fetching ICS from: {url}")
    # Replace webcal with https
    if url.startswith("webcal://"):
        url = "https://" + url[len("webcal://"):]
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text
    except Exception as e:
        print(f"Failed to fetch ICS: {e}")
        return

    # Simple parsing for VEVENT blocks
    events = re.findall(r"BEGIN:VEVENT.*?END:VEVENT", content, re.DOTALL)
    print(f"Total events in file: {len(events)}")
    
    today_str = "20260227"
    today_events = []
    
    for event in events:
        # Extract DTSTART and SUMMARY
        dtstart_match = re.search(r"DTSTART(?:;VALUE=DATE)?:(\d{8}T?\d{0,6}Z?)", event)
        summary_match = re.search(r"SUMMARY:(.*?)(?:\r?\n[A-Z]|$)", event, re.DOTALL)
        
        if dtstart_match:
            dtstart = dtstart_match.group(1)
            if dtstart.startswith(today_str):
                summary = "No Title"
                if summary_match:
                    summary = summary_match.group(1).strip().replace("\r\n ", "")
                
                # Also try to extract time if possible
                time_match = re.search(r"DTSTART:(\d{8}T(\d{4})\d{2})", event)
                time_str = ""
                if time_match:
                    time_str = f" at {time_match.group(2)[:2]}:{time_match.group(2)[2:]}"
                
                today_events.append(f"{dtstart}{time_str} - {summary}")

    print(f"\nEvents found for today ({today_str}):")
    if not today_events:
        print("No events found for today in the raw ICS feed.")
    else:
        for ev in sorted(today_events):
            print(f"  {ev}")

if __name__ == "__main__":
    url = "webcal://p235-caldav.icloud.com.cn/published/2/ODE0NTU3NDA4NzgxNDU1N5a7oJG6Offg5NzyJNtGUnjgoiOkv5PFGc8AbHw6VVae6__dE6CfiFmiu9BoMcUHNwgq4C2AeVeJbuTwRlWZaoU"
    fetch_and_parse_ics(url)
