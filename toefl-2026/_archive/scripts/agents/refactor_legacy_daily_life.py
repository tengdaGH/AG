# ============================================================
# Purpose:       Refactor legacy "Read in Daily Life" items: fix corporate/legal jargon, enforce CEFR A1-B2, and shuffle answer options.
# Usage:         python agents/scripts/refactor_legacy_daily_life.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
Refactor legacy "Read in Daily Life" items to meet TOEFL 2026 specifications.
Detects corporate/legal jargon and refactors it into accessible daily life contexts.
Forces CEFR levels to A1-B2 and shuffles options.
"""
import os
import sys
import json
import uuid
import re
import random
import datetime

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.append(backend_dir)

from google import genai
from google.genai import types
from app.database.connection import SessionLocal, engine, Base
from app.models.models import TestItem, SectionType, CEFRLevel, TaskType

Base.metadata.create_all(bind=engine)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Please set GEMINI_API_KEY.")
    sys.exit(1)

LEGACY_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/read-in-daily-life-passages.json'))

def shuffle_options(question, truth_key="correct_answer"):
    """
    Shuffles the options of a question and updates the correct_answer index accordingly.
    truth_key: The key currently holding the index of the correct answer.
    """
    options = question.get("options", [])
    if not options or len(options) < 2:
        return
    
    correct_idx = question.get(truth_key)
    if correct_idx is None or not isinstance(correct_idx, int) or correct_idx >= len(options):
        return
        
    correct_val = options[correct_idx]
    random.shuffle(options)
    
    question["options"] = options
    question["correct_answer"] = options.index(correct_val)
    
    # Clean up redundant legacy keys
    if "correct" in question:
        del question["correct"]

def needs_refactor(item):
    """
    Heuristic to detect if legacy item needs LLM refactor.
    Corporate/Legal keywords or high CEFR.
    """
    text = str(item).lower()
    corporate_keywords = ["policy", "contract", "legal", "amendment", "statutory", "legislation", "liability", "terms of use", "correspondence"]
    for kw in corporate_keywords:
        if kw in text:
            return True
    
    difficulty = item.get("difficulty", "B1")
    if difficulty in ["C1", "C2"]:
        return True
    
    return False

def refactor_item(client, item):
    """
    Sends the legacy item to LLM to be refactored into a daily life context.
    """
    original_json = json.dumps(item, indent=2)
    prompt = f"""You are a TOEFL 2026 Item Designer. 
Your task is to REFACTOR a legacy reading item into a compliant "Read in Daily Life" item.

CRITICAL RULES:
1. AVOID Corporate/Legal jargon: If the text is about contracts, legal amendments, or corporate policies, CHANGE it to a daily life/campus scenario (e.g., club notice, personal email, neighborhood flyer, text chain).
2. CEFR Level: Must be between A1 and B2. If it's C1/C2, downgrade it.
3. Length: 15-150 words.
4. Correct Answer: Ensure it paraphrases the text, not word-matching.
5. Format: Keep the same item ID but update the content.

LEGACY ITEM JSON:
{original_json}

JSON schema for output:
{{"id": "...", "type": "...", "title": "...", "text": "...", "difficulty": "...", "questions": [{{"text": "...", "options": ["A","B","C","D"], "correct_answer": 0}}]}}

Output ONLY the raw JSON. No markdown.
"""
    try:
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=[prompt],
            config=types.GenerateContentConfig(
                system_instruction="You are an ETS-certified Language Assessment Designer.",
                temperature=0.7,
            )
        )
        content = response.text
        
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"  ✗ Refactor error: {e}")
    return None

def run():
    client = genai.Client(api_key=GEMINI_API_KEY)
    db = SessionLocal()
    
    if not os.path.exists(LEGACY_DATA_PATH):
        print(f"Legacy data not found at {LEGACY_DATA_PATH}")
        return

    with open(LEGACY_DATA_PATH, 'r') as f:
        data = json.load(f)

    total_restored = 0
    
    all_passages = []
    for set_key, s in data.get("sets", {}).items():
        all_passages.extend(s.get("passages", []))

    print(f"Found {len(all_passages)} legacy Daily Life passages. Starting audit/refactor...")

    for p in all_passages:
        source_id = p["id"]
        print(f"Processing {source_id}...")
        
        if needs_refactor(p):
            print(f"  -> Needs refactor (Corporate/High CEFR). Consulting AI...")
            refactored = refactor_item(client, p)
            if refactored:
                p = refactored
                p["refactored"] = True
            else:
                print(f"  ⚠ Skipping {source_id} due to refactor failure.")
                continue
        else:
            print(f"  -> Compliant Daily Life context. Shuffling.")
            # Map legacy 'correct' to 'correct_answer' for uniform schema
            for q in p.get("questions", []):
                shuffle_options(q, truth_key="correct")

        # Map CEFR properly
        cefr_str = p.get("difficulty", "B1")
        if cefr_str not in [c.value for c in CEFRLevel]:
            cefr_str = "B1" # Fallback
        
        pc = {
            "type": p.get("type", "Notice"),
            "title": p.get("title", "Legacy Item"),
            "text": p.get("text") or p.get("content") or json.dumps(p.get("messages", [])),
            "questions": p.get("questions", [])
        }

        # For refactored items, they already have 'correct_answer' from LLM.
        # For non-refactored items, they were shuffled above and 'correct' was deleted.
        # To avoid double-shuffling, we ONLY shuffle if it hasn't been done yet.
        for q in pc["questions"]:
            if "correct_answer" in q and not p.get("refactored"):
                # Already shuffled in the 'else' block
                continue
            shuffle_options(q, truth_key="correct_answer")

        new_item = TestItem(
            id=str(uuid.uuid4()),
            section=SectionType.READING,
            target_level=CEFRLevel[cefr_str],
            irt_difficulty=0.0,
            irt_discrimination=1.0,
            task_type=TaskType.READ_IN_DAILY_LIFE,
            prompt_content=json.dumps(pc),
            is_active=True,
            version=2,
            generated_by_model="gemini-1.5-pro-Refactor" if p.get("refactored") else "Legacy-Import-Fixed",
            generation_notes=f"Restored legacy item {source_id}. Refactored: {p.get('refactored', False)}.",
            source_file="read-in-daily-life-passages.json",
            source_id=source_id
        )
        db.add(new_item)
        total_restored += 1
        print(f"  ✓ {source_id} restored as v2.")

    db.commit()
    db.close()
    print(f"\nFinished! Restored {total_restored} items.")

if __name__ == "__main__":
    run()
