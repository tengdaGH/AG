# ============================================================
# Purpose:       Regenerate only Read in Daily Life items to fix topic jargon and question redundancy issues.
# Usage:         python agents/scripts/regenerate_daily_life.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
Regenerate ONLY the "Read in Daily Life" items with version tracking.
Targeted fix to resolve topic jargon and question redundancy.
"""
import os
import sys
import json
import uuid
import re
import datetime
import random

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

BATCH = {
    "label": "Daily Life",
    "prompt": """Generate exactly 3 TOEFL 2026 "Read in Daily Life" items as a JSON array.

Rules:
- Formats: campus notice, personal email, social media post, community flyer. AVOID corporate workplace/business scenarios (e.g. "Q2 deliverables" or project management). Must be accessible daily life.
- Length: 50-150 words each (write the FULL text)
- 2-3 questions per item. Questions MUST test DIFFERENT parts of the text or different skills (e.g. main purpose vs specific detail inference). Do not ask redundant questions.
- Distractors and correct answers MUST be of similar length. Do not make the correct answer noticeably longer.
- Correct answers should paraphrase the text, NOT use exact word-matching.
- CEFR levels: A2, B1, B2 (one each)
- IRT difficulty: -1.5, -0.5, 0.3

JSON schema per item:
{"section":"READING","target_level":"A2","irt_difficulty":-1.5,"irt_discrimination":0.9,"prompt_content":{"type":"Read in Daily Life","title":"...","text":"FULL TEXT","questions":[{"question_num":1,"text":"...","options":["A","B","C","D"],"correct_answer":0}]},"is_active":true}

Note: The "correct_answer" should be the 0-indexed position of the correct option. Please RANDOMIZE which index is the correct one (do not always make it 0).

Output ONLY the raw JSON array. No markdown. No commentary."""
}


def shuffle_options(question):
    """
    Shuffles the options of a question and updates the correct_answer index accordingly.
    """
    options = question.get("options", [])
    if not options:
        return
    
    correct_idx = question.get("correct_answer", 0)
    # Be careful if index is out of bounds
    if correct_idx >= len(options):
        return
        
    correct_val = options[correct_idx]
    
    random.shuffle(options)
    
    question["options"] = options
    question["correct_answer"] = options.index(correct_val)



def run():
    client = genai.Client(api_key=GEMINI_API_KEY)

    manual_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../rr_25_12_extracted.txt'))
    with open(manual_path, 'r', encoding='utf-8', errors='ignore') as f:
        manual_text = f.read()

    system_prompt = f"""You are an ETS-certified Language Assessment Designer. Follow the TOEFL 2026 RR-25-12 spec strictly.

MANUAL EXCERPT:
{manual_text[:15000]}
"""

    db = SessionLocal()
    
    # ONLY delete the "Read in Daily Life" items to avoid wiping out the good ones
    items_to_delete = db.query(TestItem).all()
    deleted_count = 0
    for item in items_to_delete:
        try:
            pc = json.loads(item.prompt_content)
            if pc.get("type") == "Read in Daily Life":
                db.delete(item)
                deleted_count += 1
        except Exception as e:
            pass
    db.commit()
    print(f"Purged {deleted_count} old 'Read in Daily Life' items.\n")

    total_added = 0
    print(f"--- Generating: {BATCH['label']} ---")
    try:
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=[BATCH["prompt"]],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
            )
        )
        content = response.text

        match = re.search(r'\[.*\]', content, re.DOTALL)
        if not match:
            print(f"  ✗ No JSON found for {BATCH['label']}")
            return

        items = json.loads(match.group(0))
        for item_data in items:
            pc = item_data["prompt_content"]
            
            # Shuffle options to ensure randomness
            for q in pc.get("questions", []):
                shuffle_options(q)
                
            wc = len(pc["text"].split())
            new_item = TestItem(
                id=str(uuid.uuid4()),
                section=SectionType[item_data["section"]],
                target_level=CEFRLevel[item_data["target_level"]],
                irt_difficulty=item_data["irt_difficulty"],
                irt_discrimination=item_data["irt_discrimination"],
                task_type=TaskType.READ_IN_DAILY_LIFE,
                prompt_content=json.dumps(pc),
                is_active=item_data.get("is_active", True),
                version=2,
                generated_by_model="gemini-1.5-pro",
                generation_notes=f"Auto-generated Targeted Daily Life fix. {wc} words. Type: {pc['type']}."
            )
            db.add(new_item)
            total_added += 1
            print(f"  ✓ v2 | gemini-1.5-pro | {pc['type'][:25]:25s} | {wc:3d}w | {pc['title'][:40]}")
        db.commit()
    except Exception as e:
        print(f"  ✗ Error: {e}")
        db.rollback()

    db.close()
    print(f"\nDone! Injected {total_added} versioned targeted items.")

if __name__ == "__main__":
    run()
