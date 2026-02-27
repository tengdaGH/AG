
import requests
import re
import datetime

ICS_FEEDS = {
    "Miya": "https://p235-caldav.icloud.com.cn/published/2/ODE0NTU3NDA4NzgxNDU1N5a7oJG6Offg5NzyJNtGUnjgoiOkv5PFGc8AbHw6VVae6__dE6CfiFmiu9BoMcUHNwgq4C2AeVeJbuTwRlWZaoU",
    "Rita": "https://p235-caldav.icloud.com.cn/published/2/ODE0NTU3NDA4NzgxNDU1N5a7oJG6Offg5NzyJNtGUngnLMbawCT_bon3iWGIba7YM84yuUlE7Idh5jWX1bDCHZKbzA8hrxpLI2_Xowoz3NU",
    "月月": "https://p235-caldav.icloud.com.cn/published/2/ODE0NTU3NDA4NzgxNDU1N5a7oJG6Offg5NzyJNtGUnhjf_1D8Xs4kSFfKit5JqAv6xA4A4idWDEIz-quwP9634_Qo0Wp21-tGyBGvEpEi5g",
    "达哥": "https://p235-caldav.icloud.com.cn/published/2/ODE0NTU3NDA4NzgxNDU1N5a7oJG6Offg5NzyJNtGUnjL2uWOtR1ag7v1hzo5u_PgGOG5Sa6gmMjGSlEVV_JFPYzif3IWvBkmDfpwwWeiT-k"
}

def parse_ics_date(date_str):
    if 'T' in date_str:
        clean_str = date_str.replace('Z', '')
        dt = datetime.datetime.strptime(clean_str[:15], "%Y%m%dT%H%M%S")
        return dt, False
    else:
        dt = datetime.datetime.strptime(date_str[:8], "%Y%m%d")
        return dt, True

def test_feeds():
    today_str = "20260227"
    for teacher, url in ICS_FEEDS.items():
        print(f"\nTesting {teacher}...")
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            content = resp.text
            content = content.replace("\r\n ", "").replace("\n ", "")
            events = re.findall(r"BEGIN:VEVENT.*?END:VEVENT", content, re.DOTALL)
            print(f"  Total events: {len(events)}")
            
            today_matches = []
            for event in events:
                dtstart_match = re.search(r"DTSTART.*?:(\d{8}T?\d{0,6}Z?)", event)
                if dtstart_match and dtstart_match.group(1).startswith(today_str):
                    summary_match = re.search(r"SUMMARY:(.*?)(?:\r?\n|$)", event)
                    summary = summary_match.group(1).strip() if summary_match else "No Title"
                    today_matches.append(summary)
            
            if today_matches:
                print(f"  Today's classes ({len(today_matches)}):")
                for m in today_matches:
                    print(f"    - {m}")
            else:
                print("  No classes found for today.")
                
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_feeds()
