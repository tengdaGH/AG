# ============================================================
# Purpose:       Remediate remaining REVIEW items using Gemini 2.5 Flash with JSON response + key balancing + QA.
# Usage:         python backend/scripts/remediate_remaining.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import sys
import os
import json
import logging
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from app.database.connection import SessionLocal
from app.models.models import TestItem, ItemStatus, ItemVersionHistory
from scripts.gauntlet_qa import qa_single_item

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def fix_with_llm(item_id, original_json, fail_reason, task_type):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("No Gemini API key found")
        return None
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
The following TOEFL test item of type '{task_type}' failed quality assurance.
Failure Reason: {fail_reason}

Original Content JSON:
{original_json}

Please provide a rewritten JSON object for "prompt_content" that fully fixes the failure reason while maintaining the original meaning as much as possible.
Ensure EXACT compliance with all TOEFL 2026 specs.
For C-Test (Complete the Words), there MUST be EXACTLY 10 blanks (words with underscores like 'b_s'), and the first sentence MUST be completely intact with no blanks.
For Reading, passages must be the correct length.
If the error is about an option being 'too short', rewrite the options to be longer and more descriptive (at least 5 characters). Keep the options logically distinct.
If the error is about a 'distressing topic' such as religion, rewrite the passage and questions to remove the topic completely. Use a neutral alternative.
If the error is 'text length error', rewrite the text to be within the specified word count limits. Do not truncate the plot or logical flow abruptly.

Return ONLY a valid JSON object. Do not wrap it in markdown block.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.7,
                response_mime_type="application/json",
            )
        )
        return response.text
    except Exception as e:
        logging.error(f"Error: {e}")
        return None

def balance_keys(data):
    if "questions" not in data:
        return data
        
    questions = data["questions"]
    n = len(questions)
    
    import random
    targets = []
    for i in range(n):
        targets.append(i % 4)
    random.shuffle(targets)
    
    for i, q in enumerate(questions):
        options = q.get("options", [])
        if not options or len(options) != 4:
            continue
            
        correct_idx = q.get("correct_answer", 0)
        correct_text = options[correct_idx]
        target_idx = targets[i]
        
        new_options = list(options)
        new_options.remove(correct_text)
        new_options.insert(target_idx, correct_text)
        
        q["options"] = new_options
        q["correct_answer"] = target_idx
        
    return data

def main():
    db = SessionLocal()
    items = db.query(TestItem).filter(TestItem.lifecycle_status == ItemStatus.REVIEW).all()
    
    for item in items:
        logging.info(f"Processing remaining item {item.id[:8]} - {item.generation_notes}")
        new_json_str = fix_with_llm(item.id, item.prompt_content, item.generation_notes, item.task_type.value)
        if not new_json_str:
            logging.error(f"Failed to get LLM response for {item.id}")
            continue
            
        try:
            data = json.loads(new_json_str)
        except Exception as e:
            logging.error(f"Failed to parse LLM JSON for {item.id}: {e}\n{new_json_str}")
            continue
            
        data = balance_keys(data)
        
        item.prompt_content = json.dumps(data)
        item.lifecycle_status = ItemStatus.DRAFT
        db.add(ItemVersionHistory(item_id=item.id, version_number=item.version, prompt_content=item.prompt_content, changed_by="Auto-Remediator"))
        item.version += 1
        db.commit()
        
        logging.info(f"Running QA on {item.id}")
        res = qa_single_item(item.id)
        logging.info(f"QA Result: {res}")
        
    db.close()

if __name__ == "__main__":
    main()
