
import requests
import re

def fetch_and_parse_ics(url):
    print(f"Fetching ICS from: {url}")
    if url.startswith("webcal://"):
        url = "https://" + url[len("webcal://"):]
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text
    except Exception as e:
        print(f"Failed to fetch ICS: {e}")
        return

    events = re.findall(r"BEGIN:VEVENT.*?END:VEVENT", content, re.DOTALL)
    print(f"Total events in file: {len(events)}")
    
    today_str = "20260227"
    today_events = []
    
    for event in events:
        # Match DTSTART with potential parameters like TZID
        # e.g. DTSTART;TZID=Asia/Shanghai:20210924T080000
        dtstart_match = re.search(r"DTSTART.*?:(\d{8}T\d{6})", event)
        summary_match = re.search(r"SUMMARY:(.*?)(?:\r?\n[A-Z]|$)", event, re.DOTALL)
        
        if dtstart_match:
            dtstart_val = dtstart_match.group(1) # e.g. 20260227T103000
            if dtstart_val.startswith(today_str):
                summary = "No Title"
                if summary_match:
                    summary = summary_match.group(1).strip().replace("\r\n ", "")
                
                time_part = dtstart_val[9:13] # HHMM
                formatted_time = f"{time_part[:2]}:{time_part[2:]}"
                
                today_events.append(f"{formatted_time} - {summary}")

    print(f"\nEvents found for today ({today_str}) in RAW ICS:")
    if not today_events:
        print("No events found for today.")
    else:
        for ev in sorted(today_events):
            print(f"  {ev}")

if __name__ == "__main__":
    url = "webcal://p235-caldav.icloud.com.cn/published/2/ODE0NTU3NDA4NzgxNDU1N5a7oJG6Offg5NzyJNtGUnjgoiOkv5PFGc8AbHw6VVae6__dE6CfiFmiu9BoMcUHNwgq4C2AeVeJbuTwRlWZaoU"
    fetch_and_parse_ics(url)
