# ============================================================
# Purpose:       Populate the reading item bank with high-compliance items using Gemini, with version tracking and audit trails.
# Usage:         python agents/scripts/populate_reading_items.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
Populate the reading item bank with more high-compliance items.
Appends items to the database with version tracking and audit trails.
"""
import os
import sys
import json
import uuid
import re
import datetime

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.append(backend_dir)

from google import genai
from google.genai import types
from app.database.connection import SessionLocal, engine, Base, SQLALCHEMY_DATABASE_URL
print(f"DEBUG: Using database at: {SQLALCHEMY_DATABASE_URL}")
from app.models.models import TestItem, SectionType, CEFRLevel

Base.metadata.create_all(bind=engine)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Please set GEMINI_API_KEY.")
    sys.exit(1)

BATCH_CONFIGS = [
    {
        "label": "Academic Passages (Set 2)",
        "prompt": """Generate exactly 2 TOEFL 2026 "Read an Academic Passage" items as a JSON array.

Rules:
- Each passage MUST be approximately 200 words.
- Topics: one from Business/Economics, one from Art/Music.
- 5 multiple-choice questions per passage.
- CEFR levels: B2, C1 (one each).
- IRT difficulty: 0.5, 1.2.
- IRT discrimination: 1.1, 1.3.

JSON schema per item:
{"section":"READING","target_level":"B2","irt_difficulty":0.5,"irt_discrimination":1.1,"prompt_content":{"type":"Read an Academic Passage","title":"...","text":"FULL 200-WORD TEXT","questions":[{"question_num":1,"text":"...","options":["A","B","C","D"],"correct_answer":0}]},"is_active":true}

Output ONLY the raw JSON array. No markdown. No commentary."""
    },
    {
        "label": "Daily Life (Set 2)",
        "prompt": """Generate exactly 2 TOEFL 2026 "Read in Daily Life" items as a JSON array.

Rules:
- Formats: Menu, Schedule.
- Length: 50-150 words each.
- 3 questions per item.
- CEFR levels: A2, B1 (one each).
- IRT difficulty: -1.0, -0.2.
- IRT discrimination: 0.8, 1.0.

JSON schema per item:
{"section":"READING","target_level":"A2","irt_difficulty":-1.0,"irt_discrimination":0.8,"prompt_content":{"type":"Read in Daily Life","title":"...","text":"FULL TEXT","questions":[{"question_num":1,"text":"...","options":["A","B","C","D"],"correct_answer":0}]},"is_active":true}

Output ONLY the raw JSON array. No markdown. No commentary."""
    },
    {
        "label": "Complete the Words (Initial Set)",
        "prompt": """Generate exactly 3 TOEFL 2026 "Complete the Words" (C-test) items as a JSON array.

Rules:
- Intact first sentence, then second half of every second word deleted using underscores.
- Each passage has EXACTLY 10 truncated words (e.g., "stu____" for "students").
- 60-80 words per passage.
- 10 fill-in-the-blank questions per item (matching the 10 truncated words).
- This is a FILL-IN-THE-BLANK format. Test takers type the missing letters. There are NO multiple-choice options.
- CEFR levels: B1, B2, C1 (one each).
- IRT difficulty: -0.1, 0.4, 0.9.
- IRT discrimination: 0.9, 1.1, 1.2.

JSON schema per item:
{"section":"READING","target_level":"B1","irt_difficulty":-0.1,"irt_discrimination":0.9,"prompt_content":{"type":"Complete the Words","title":"...","text":"FULL TEXT WITH ___","questions":[{"question_num":1,"text":"trunc___","correct_answer":"truncated"}]},"is_active":true}

Output ONLY the raw JSON array. No markdown. No commentary."""
    }
]

def run():
    client = genai.Client(api_key=GEMINI_API_KEY)

    manual_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../rr_25_12_extracted.txt'))
    with open(manual_path, 'r', encoding='utf-8', errors='ignore') as f:
        manual_text = f.read()

    system_prompt = f"""You are an ETS-certified Language Assessment Designer. Follow the TOEFL 2026 RR-25-12 spec strictly.
    When generating C-tests, ensure the truncation follow the 'second half of every second word' rule exactly.
    Provide 4 options for each question in C-test, where the correct answer is the full word.

    MANUAL EXCERPT:
    {manual_text[:15000]}
    """

    db = SessionLocal()
    total_added = 0
    
    for batch in BATCH_CONFIGS:
        print(f"--- Generating: {batch['label']} ---")
        try:
            response = client.models.generate_content(
                model="gemini-1.5-pro",
                contents=[batch["prompt"]],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                )
            )
            content = response.text

            match = re.search(r'\[.*\]', content, re.DOTALL)
            if not match:
                print(f"  ✗ No JSON found for {batch['label']}")
                continue

            items = json.loads(match.group(0))
            print(f"  ↪ Found {len(items)} items in JSON.")
            for item_data in items:
                pc = item_data["prompt_content"]
                wc = len(pc["text"].split())
                new_item = TestItem(
                    id=str(uuid.uuid4()),
                    section=SectionType[item_data["section"]],
                    target_level=CEFRLevel[item_data["target_level"]],
                    irt_difficulty=item_data["irt_difficulty"],
                    irt_discrimination=item_data["irt_discrimination"],
                    prompt_content=json.dumps(pc),
                    is_active=item_data.get("is_active", True),
                    version=1,
                    generated_by_model="gemini-1.5-pro",
                    generation_notes=f"Population run. {wc} words. Type: {pc['type']}."
                )
                db.add(new_item)
                total_added += 1
                print(f"  ✓ v1 | gemini-1.5-pro | {pc['type'][:25]:25s} | {wc:3d}w | {pc['title'][:40]}")
            db.commit()
            print(f"  ✓ Committed batch: {batch['label']}")
            
            # Final sanity check with raw SQL
            with engine.connect() as conn:
                from sqlalchemy import text
                count = conn.execute(text("SELECT COUNT(*) FROM test_items WHERE generation_notes LIKE 'Population run%'")).scalar()
                print(f"  ↪ Current count in DB for this run: {count}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            db.rollback()

    db.close()
    print(f"\nDone! Injected {total_added} versioned items.")

if __name__ == "__main__":
    run()
