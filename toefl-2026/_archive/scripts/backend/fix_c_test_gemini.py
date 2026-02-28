# ============================================================
# Purpose:       Remediate REVIEW-status C-Test items via Gemini 2.5 Flash with up to 4 retry attempts.
# Usage:         python backend/scripts/fix_c_test_gemini.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import sys
import json
import logging
import re
import google.generativeai as genai

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models.models import TestItem, ItemStatus, TaskType
from app.database.connection import SessionLocal
from scripts.gauntlet_qa import run_content_agent, run_editorial_agent

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def rewrite_c_test_gemini(cefr_level: str, topic_hint: str) -> str | None:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    api_key = os.getenv("GEMINI_API_KEY")
        
    if not api_key:
        logging.error("No GEMINI_API_KEY found.")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
You are an expert TOEFL test item creator. Create a brand new "COMPLETE_THE_WORDS" (C-Test) item for CEFR level {cefr_level}.
The topic should broadly be related to: {topic_hint[:100]}...

CRITICAL INSTRUCTIONS:
1. The `text` MUST have EXACTLY 10 missing words. Each missing word MUST have its latter half truncated and replaced by underscores '_', for example: "aw___" or "reg_ _ _" or "ex___". Ensure there are EXACTLY 10 of these truncated words in the text.
2. The FIRST SENTENCE of the `text` MUST be completely intact, with NO blanks / NO underscores in it.
3. The `questions` array MUST have EXACTLY 10 items.
4. Each question in the array must correctly target one of the blanks from the text in order (1-10). The question `text` field must match the truncated word from the passage (e.g. "aw___").
5. Each question must provide the full, correct complete word in the `correct_answer` field.

Output ONLY a raw JSON object with the following schema:
{{
  "id": "C-TEST-NEW",
  "text": "First sentence is intact. Then the sec___ sentence has exactly te_ blanks total...",
  "questions": [
    {{"question_num": 1, "text": "sec___", "correct_answer": "second"}},
    {{"question_num": 2, "text": "te_", "correct_answer": "ten"}},
    ... (must have exactly 10)
  ]
}}
Do not wrap it in markdown. Just the raw JSON.
"""
    try:
        response = model.generate_content(prompt)
        text = response.text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            json.loads(json_str) # validate
            return json_str
        else:
            logging.error(f"No JSON found in response: {text}")
    except Exception as e:
        logging.error(f"LLM Remediation failed: {e}")
    return None

def main():
    db = SessionLocal()
    
    # Find C-Test items in REVIEW status
    items = db.query(TestItem).filter(
        TestItem.lifecycle_status == ItemStatus.REVIEW,
        TestItem.task_type == TaskType.COMPLETE_THE_WORDS
    ).all()
    
    logging.info(f"Found {len(items)} COMPLETE_THE_WORDS items in REVIEW.")
    
    for item in items:
        logging.info(f"Processing Item ID: {item.id} (Level: {item.target_level})")
        
        # Extract topic hint from original prompt_content
        topic_hint = "General topic."
        if item.prompt_content:
            try:
                data = json.loads(item.prompt_content)
                topic_hint = data.get("text", "")[:150]
            except:
                pass

        success = False
        for attempt in range(4):
            logging.info(f"Attempt {attempt + 1}...")
            new_content = rewrite_c_test_gemini(item.target_level.value, topic_hint)
            if new_content:
                c_pass, c_reason = run_content_agent(item.id, new_content, item.task_type)
                e_pass, e_reason = run_editorial_agent(item.id, new_content, item.task_type)
                
                if c_pass and e_pass:
                    # Update JSON's "id" to avoid showing "C-TEST-NEW" in frontend if it relies on it
                    try:
                        valid_data = json.loads(new_content)
                        # Retain original ID inside json just in case
                        valid_data["id"] = item.id
                        new_content = json.dumps(valid_data)
                    except:
                        pass
                        
                    item.prompt_content = new_content
                    item.lifecycle_status = ItemStatus.FIELD_TEST
                    item.generation_notes = "Remediated by Gemini-2.5-Flash. Passed all structural QA checks."
                    item.version += 1
                    db.commit()
                    logging.info(f"Item {item.id} Successfully remediated and moved to FIELD_TEST.")
                    success = True
                    break
                else:
                    logging.warning(f"Generated content failed local QA. Content error: {c_reason}, Editorial error: {e_reason}")
            else:
                logging.error("LLM returned None or invalid JSON.")
                
        if not success:
            logging.error(f"Failed to remediate item {item.id} after 4 attempts.")

    db.close()

if __name__ == "__main__":
    main()
