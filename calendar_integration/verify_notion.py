
import requests
import json
import os

token = "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"
db_id = "3125eb7b-e7e4-8057-8135-c6708b63ed5e"

def query_notion():
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Query for events in late February
    payload = {
        "filter": {
            "and": [
                {
                    "property": "Start",
                    "date": {
                        "on_or_after": "2026-02-26"
                    }
                },
                {
                    "property": "Start",
                    "date": {
                        "on_or_before": "2026-03-02"
                    }
                }
            ]
        }
    }
    
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
        return
        
    data = resp.json()
    print(f"Found {len(data['results'])} results in Notion.")
    for page in data['results']:
        props = page['properties']
        name = "".join([t['plain_text'] for t in props['Name']['title']])
        start = props['Start']['date']['start']
        teacher = props['教师']['select']['name'] if props['教师']['select'] else "None"
        print(f"  [{start}] [{teacher}] {name}")

if __name__ == "__main__":
    query_notion()
