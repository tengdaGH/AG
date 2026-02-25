# ============================================================
# Purpose:       Deterministically regenerate C-Test items in REVIEW status and re-run QA gauntlet.
# Usage:         python backend/scripts/fix_c_test_deterministic.py
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

def get_raw_text(cefr_level: str, topic_hint: str) -> str:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"Write a 40 to 50 word informative paragraph about '{topic_hint[:50]}' suitable for an English learner at CEFR level {cefr_level}. Do NOT include any blanks, underscores, or formatting. Just raw natural text."
    response = model.generate_content(prompt)
    return response.text.strip()

def build_c_test_deterministically(raw_text: str) -> dict:
    # 1. Split into first sentence and the rest
    match = re.search(r'^([A-Z].*?[.!?])\s+(.*)$', raw_text, re.DOTALL)
    if not match:
        # Fallback if no clear sentence boundary
        words = raw_text.split()
        first_sentence = " ".join(words[:10]) + "."
        rest_text = " ".join(words[10:])
    else:
        first_sentence = match.group(1)
        rest_text = match.group(2)

    # 2. Iterate through rest_text words and truncate every 2nd word until we have 10
    rest_words = re.findall(r"[\w']+|[.,!?;]", rest_text)
    
    final_words = []
    questions = []
    word_count = 0
    
    for token in rest_words:
        # If it's punctuation, just append and continue
        if re.match(r'^[.,!?;]$', token):
            if final_words:
                final_words[-1] += token # attach to previous word
            else:
                final_words.append(token)
            continue
            
        word_count += 1
        
        # Every 2nd word gets truncated, unless we already have 10
        if word_count % 2 == 0 and len(questions) < 10 and len(token) >= 2:
            # Truncate logic
            half_len = len(token) // 2
            visible_part = token[:half_len]
            hidden_part = token[half_len:]
            
            truncated_word = visible_part + "_" * len(hidden_part)
            final_words.append(truncated_word)
            
            questions.append({
                "question_num": len(questions) + 1,
                "text": truncated_word,
                "correct_answer": token
            })
        else:
            final_words.append(token)
            
    final_text = first_sentence + " " + " ".join(final_words)
    # clean up punctuation spacing
    final_text = re.sub(r'\s+([.,!?;])', r'\1', final_text)
    
    return {
        "id": "C-TEST-NEW",
        "title": "Language Exercise",
        "text": final_text,
        "questions": questions
    }

def main():
    db = SessionLocal()
    
    items = db.query(TestItem).filter(
        TestItem.lifecycle_status == ItemStatus.REVIEW,
        TestItem.task_type == TaskType.COMPLETE_THE_WORDS
    ).all()
    
    logging.info(f"Found {len(items)} COMPLETE_THE_WORDS items in REVIEW.")
    
    for item in items:
        logging.info(f"Processing Item ID: {item.id} (Level: {item.target_level})")
        
        topic_hint = "General science or daily life"
        if item.prompt_content:
            try:
                data = json.loads(item.prompt_content)
                topic_hint = data.get("text", "")[:100]
            except:
                pass

        try:
            raw_text = get_raw_text(item.target_level.value, topic_hint)
            new_data = build_c_test_deterministically(raw_text)
            new_data["id"] = item.id
            new_content = json.dumps(new_data)
            
            c_pass, c_reason = run_content_agent(item.id, new_content, item.task_type)
            e_pass, e_reason = run_editorial_agent(item.id, new_content, item.task_type)
            
            if c_pass and e_pass:
                item.prompt_content = new_content
                item.lifecycle_status = ItemStatus.FIELD_TEST
                item.generation_notes = "Remediated by deterministic script. Passed all structural QA checks."
                item.version += 1
                db.commit()
                logging.info(f"Item {item.id} Successfully remediated and moved to FIELD_TEST.")
            else:
                logging.warning(f"Failed QA. Content: {c_reason}, Editorial: {e_reason}")
                logging.warning(f"Generated JSON: {new_content}")
        except Exception as e:
            logging.error(f"Failed on item {item.id}: {e}")

    db.close()

if __name__ == "__main__":
    main()
