import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PARENT_PAGE_ID = "3115eb7be7e481ef9a81cb90de03ecd7"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

db_schema = {
    "parent": {"type": "page_id", "page_id": PARENT_PAGE_ID},
    "title": [
        {
            "type": "text",
            "text": {"content": "Student Progress & Results (TOEFL & IELTS)"}
        }
    ],
    "properties": {
        "Student Name": {"title": {}},
        "Test ID": {
            "select": {
                "options": []
            }
        },
        "Section": {
            "select": {
                "options": [
                    {"name": "Reading", "color": "blue"},
                    {"name": "Listening", "color": "green"},
                    {"name": "Speaking", "color": "purple"},
                    {"name": "Writing", "color": "red"}
                ]
            }
        },
        "Raw Answers": {"rich_text": {}},
        "Score": {"number": {"format": "number"}},
        "Report Link": {"url": {}},
        "Status": {
            "select": {
                "options": [
                    {"name": "In Progress", "color": "yellow"},
                    {"name": "Completed", "color": "green"}
                ]
            }
        },
        "Timestamp": {"date": {}}
    }
}

def create_database():
    url = "https://api.notion.com/v1/databases"
    response = requests.post(url, headers=headers, json=db_schema)
    if response.status_code == 200:
        print("Success! Database created.")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    create_database()
