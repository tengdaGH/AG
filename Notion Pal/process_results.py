import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

DATABASE_ID = "3115eb7b-e748-13a9-457e-3608099a923".replace("-", "") # Ensure ID format
# Corrected database ID from previous successful manual call
DATABASE_ID = "3115eb7be7e4813a9457e3608099a923"
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = "2022-06-28"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION
}

def generate_ai_feedback(student_name, test_id, section, raw_answers):
    # (keeps existing logic)
    feedback = f"### AI Analysis for {student_name}\n\n"
    feedback += f"**Test:** {test_id} | **Section:** {section}\n\n"
    feedback += "Great job completing the section! Based on your raw answers, here is some feedback:\n\n"
    if section == "Writing":
        feedback += "- Focus on sentence structure and vocabulary variety.\n"
        feedback += "- Ensure you address all parts of the prompt clearly.\n"
    elif section == "Reading":
        feedback += "- Good comprehension skills. Keep practicing time management.\n"
    else:
        feedback += "- Nice work on the selected section. Continue consistent practice.\n"
    feedback += "\n*Note: This is an automated analysis.*"
    return feedback

def process_pending_results():
    print("Checking for pending results...")
    
    query_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    query_payload = {
        "filter": {
            "property": "Automation Status",
            "select": {
                "equals": "Pending"
            }
        }
    }
    
    response = requests.post(query_url, headers=headers, json=query_payload)
    if response.status_code != 200:
        print(f"Error querying database: {response.status_code} - {response.text}")
        return

    results = response.json().get("results", [])
    print(f"Found {len(results)} pending results.")
    
    for page in results:
        page_id = page["id"]
        props = page.get("properties", {})
        
        student_name = "Student"
        if "Student Name" in props and props["Student Name"]["title"]:
            student_name = props["Student Name"]["title"][0]["text"]["content"]
        
        test_id = "Unknown"
        if "Test ID" in props and props["Test ID"]["select"]:
            test_id = props["Test ID"]["select"]["name"]
            
        section = "Unknown"
        if "Section" in props and props["Section"]["select"]:
            section = props["Section"]["select"]["name"]
            
        raw_answers = ""
        if "Raw Answers" in props and props["Raw Answers"]["rich_text"]:
            raw_answers = props["Raw Answers"]["rich_text"][0]["text"]["content"]
        
        print(f"Processing result for {student_name} ({test_id} - {section})...")
        
        feedback_text = generate_ai_feedback(student_name, test_id, section, raw_answers)
        
        # 1. Update Properties
        update_url = f"https://api.notion.com/v1/pages/{page_id}"
        update_payload = {
            "properties": {
                "AI Analysis": {
                    "rich_text": [{"type": "text", "text": {"content": feedback_text}}]
                },
                "Automation Status": {
                    "select": {"name": "Processed"}
                }
            }
        }
        requests.patch(update_url, headers=headers, json=update_payload)
        
        # 2. Append content
        append_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        append_payload = {
            "children": [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "AI Performance Analysis"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": feedback_text.replace('### ', '')}}]
                    }
                }
            ]
        }
        requests.patch(append_url, headers=headers, json=append_payload)
        print(f"Successfully processed {page_id}")

if __name__ == "__main__":
    process_pending_results()
