import requests

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_DB_ID = "3125eb7b-e7e4-8057-8135-c6708b63ed5e"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

payload = {
    "properties": {
        "UID": {"rich_text": {}},
        "教师": {
            "select": {
                "options": [
                    {"name": "Miya", "color": "blue"},
                    {"name": "Rita", "color": "red"},
                    {"name": "月月", "color": "green"},
                    {"name": "达哥", "color": "purple"}
                ]
            }
        },
        "Start": {"date": {}}
    }
}

url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}"
r = requests.patch(url, headers=headers, json=payload)

if r.status_code == 200:
    print("Successfully updated database schema!")
else:
    print(f"Failed: {r.status_code}")
    print(r.text)
