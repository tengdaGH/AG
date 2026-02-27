
import requests
import re

def fetch_and_search_ics(url, keywords):
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
    
    found_count = 0
    for event in events:
        summary_match = re.search(r"SUMMARY:(.*?)(?:\r?\n[A-Z]|$)", event, re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).strip().replace("\r\n ", "")
            if any(k in summary for k in keywords):
                dtstart_match = re.search(r"DTSTART(?:;VALUE=DATE)?:(\d{8}T?\d{0,6}Z?)", event)
                dtstart = dtstart_match.group(1) if dtstart_match else "Unknown"
                print(f"  [{dtstart}] {summary}")
                found_count += 1
                if found_count > 20:
                    print("... first 20 matches shown")
                    break

if __name__ == "__main__":
    url = "webcal://p235-caldav.icloud.com.cn/published/2/ODE0NTU3NDA4NzgxNDU1N5a7oJG6Offg5NzyJNtGUnjgoiOkv5PFGc8AbHw6VVae6__dE6CfiFmiu9BoMcUHNwgq4C2AeVeJbuTwRlWZaoU"
    fetch_and_search_ics(url, ["写作", "贺贺", "皮皮"])
