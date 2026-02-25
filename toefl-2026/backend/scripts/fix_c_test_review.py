# ============================================================
# Purpose:       Rewrite REVIEW-status C-Test items via Gemini 1.5 Pro to fix structural QA failures.
# Usage:         python backend/scripts/fix_c_test_review.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import sys
import json
import logging
import re
from google import genai
from google.genai import types

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models.models import TestItem, ItemStatus, TaskType
from app.database.connection import SessionLocal
from scripts.gauntlet_qa import run_content_agent, run_editorial_agent

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def rewrite_c_test(original_content: str, fail_reason: str) -> str | None:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    api_key = os.getenv("GEMINI_API_KEY")
        
    if not api_key:
        logging.error("No GEMINI_API_KEY found.")
        return None

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
You are an expert TOEFL test item creator. The following "COMPLETE_THE_WORDS" (C-Test) item failed Quality Assurance.
Failure Reason: {fail_reason}

Original Content JSON:
{original_content}

CRITICAL INSTRUCTIONS:
1. You MUST rewrite the `text` and `questions` array so they match exactly.
2. The `text` MUST have EXACTLY 10 missing words. Each missing word MUST be represented by one or more underscores '_', for example: "aw_ _ _" or "reg_ _ _" or "ex___". Ensure there are EXACTLY 10 of these truncated words in the text.
3. The FIRST SENTENCE of the `text` MUST be completely intact, with NO blanks / NO underscores in it.
4. The `questions` array MUST have EXACTLY 10 items.
5. Each question in the array must correctly target one of the blanks from the text in order (1-10). The question `text` field must match the truncated word from the passage (e.g. "aw___").
6. Each question must provide the full, correct complete word in the `correct_answer` field.

Return ONLY a valid JSON object matching the original "prompt_content" schema. Do not wrap it in markdown. Just the raw JSON.
"""
    try:
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.7,
            )
        )
        content_text = response.text
        match = re.search(r'\{.*\}', content_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            json.loads(json_str) # validate
            return json_str
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
        logging.info(f"Processing Item ID: {item.id}")
        fail_reason = item.generation_notes or "Failed C-test criteria."
        
        # Try up to 3 times to get a valid generation
        success = False
        for attempt in range(3):
            logging.info(f"Attempt {attempt + 1}...")
            new_content = rewrite_c_test(item.prompt_content, fail_reason)
            if new_content:
                # Run QA locally to see if it passes
                c_pass, c_reason = run_content_agent(item.id, new_content, item.task_type)
                e_pass, e_reason = run_editorial_agent(item.id, new_content, item.task_type)
                
                if c_pass and e_pass:
                    item.prompt_content = new_content
                    item.lifecycle_status = ItemStatus.FIELD_TEST
                    item.generation_notes = "Remediated by Gemini 1.5 Pro. Passed all structural QA checks."
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
            logging.error(f"Failed to remediate item {item.id} after 3 attempts. Deleting it.")
            # db.delete(item)
            # db.commit()

    db.close()

if __name__ == "__main__":
    main()
