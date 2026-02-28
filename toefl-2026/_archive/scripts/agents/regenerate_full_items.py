# ============================================================
# Purpose:       Wipe and regenerate all reading and listening items from scratch in version-tracked batches using Gemini.
# Usage:         python agents/scripts/regenerate_full_items.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
Regenerate all items with version tracking.
Generates items in small batches to avoid JSON truncation.
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
from app.models.models import TestItem, SectionType, CEFRLevel

Base.metadata.create_all(bind=engine)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Please set GEMINI_API_KEY.")
    sys.exit(1)

BATCHES = [
    {
        "label": "Academic Passages",
        "prompt": """Generate exactly 3 TOEFL 2026 "Read an Academic Passage" items as a JSON array.

Rules:
- Each passage MUST be approximately 200 words (this is critical - write the FULL passage)
- Topics: one from history, one from life science, one from physical science
- 3 multiple-choice questions per passage
- CEFR levels: B2, C1, C2 (one each)
- IRT difficulty: 0.8, 1.5, 2.3

JSON schema per item:
{"section":"READING","target_level":"B2","irt_difficulty":0.8,"irt_discrimination":1.2,"prompt_content":{"type":"Read an Academic Passage","title":"...","text":"FULL 200-WORD TEXT","questions":[{"question_num":1,"text":"...","options":["A","B","C","D"],"correct_answer":0}]},"is_active":true}

Output ONLY the raw JSON array. No markdown. No commentary."""
    },
    {
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
    },
    {
        "label": "Complete the Words",
        "prompt": """Generate exactly 3 TOEFL 2026 "Complete the Words" (C-test) items as a JSON array.

Rules:
- The FIRST sentence MUST be completely intact with NO blanks.
- Then, starting from the second sentence, truncate the second half of approximately every second word using underscores.
- Each passage MUST have EXACTLY 10 truncated words (e.g., "temp_______" for "temperature").
- 60-80 words per passage.
- EXACTLY 10 fill-in questions per passage (one for each blank).
- This is a FILL-IN-THE-BLANK format. Test takers type the missing letters. There are NO multiple-choice options.
- CEFR levels: A2, B1, B2 (one each)
- IRT difficulty: -1.2, -0.3, 0.4

JSON schema per item:
{"section":"READING","target_level":"A2","irt_difficulty":-1.2,"irt_discrimination":0.8,"prompt_content":{"type":"Complete the Words","title":"...","text":"FULL TEXT WITH EVERY BLANK EXACTLY SHOWN WITH ___ (exactly 10 blanks)","questions":[{"question_num":1,"text":"temp___","correct_answer":"temperature"}]},"is_active":true}

Output ONLY the raw JSON array. No markdown. No commentary."""
    },
    {
        "label": "Listen and Choose a Response",
        "prompt": """Generate exactly 3 TOEFL 2026 "Listen and Choose a Response" items as a JSON array.

Rules:
- Format: Short two-speaker exchange. The test taker hears a statement/question (audio only) and must choose the best response.
- Transcript should contain what the speaker says, though text is not shown directly to user.
- Provide a placeholder "audioUrl" such as "audio/listen_choose_placeholder.mp3"
- Options: 4 options, only 1 correct.
- CEFR levels: A1, A2, B1 (one each)
- IRT difficulty: -2.0, -1.0, 0.0

JSON schema per item:
{"section":"LISTENING","target_level":"A1","irt_difficulty":-2.0,"irt_discrimination":1.0,"prompt_content":{"type":"Listen and Choose a Response","title":"Short Conversation","audioUrl":"audio/listen_choose_placeholder.mp3", "transcript":"Didn't I just see you in the library an hour ago?","questions":[{"question_num":1,"text":"Choose the best response:","options":["A","B","C","D"],"correct_answer":0}]},"is_active":true}

Note: RANDOMIZE the "correct_answer" 0-index position.

Output ONLY the raw JSON array. No markdown. No commentary."""
    },
    {
        "label": "Listen and Repeat",
        "prompt": """Generate exactly 3 TOEFL 2026 "Listen and Repeat" speaking items as a JSON array.

Rules:
- Format: Test taker hears a sentence and repeats it exactly.
- Need an array of sentences under "sentences", each having "text" and "audioUrl".
- Use placeholder "audioUrl" like "audio/listen_repeat_placeholder.mp3".
- CEFR levels: A1, A2, B1 (one each)
- IRT difficulty: -1.5, -0.5, 0.5

JSON schema per item:
{"section":"SPEAKING","target_level":"A1","irt_difficulty":-1.5,"irt_discrimination":0.9,"prompt_content":{"type":"Listen and Repeat","title":"Sentence Repetition","sentences":[{"text":"The train leaves at five o'clock.","audioUrl":"audio/listen_repeat_placeholder.mp3"}]},"is_active":true}

Output ONLY the raw JSON array. No markdown. No commentary."""
    }
]

def shuffle_options(question):
    """
    Shuffles the options of a question and updates the correct_answer index accordingly.
    """
    options = question.get("options", [])
    if not options:
        return
    
    correct_idx = question.get("correct_answer", 0)
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
    db.query(TestItem).delete()
    db.commit()
    print("Purged old items.\n")

    total_added = 0
    for batch in BATCHES:
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
            for item_data in items:
                pc = item_data["prompt_content"]
                
                # Shuffle options to ensure randomness (skip C-test: fill-in, no options)
                if pc.get("type") != "Complete the Words":
                    for q in pc.get("questions", []):
                        shuffle_options(q)
                    
                raw_txt = pc.get("text", "") or pc.get("transcript", "")
                if not raw_txt and pc.get("sentences"):
                    raw_txt = " ".join([s.get("text", "") for s in pc.get("sentences", [])])
                wc = len(raw_txt.split())
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
                    generation_notes=f"Auto-generated from RR-25-12 spec. {wc} words. Type: {pc.get('type')}."
                )
                db.add(new_item)
                total_added += 1
                print(f"  ✓ v1 | gemini-1.5-pro | {pc['type'][:25]:25s} | {wc:3d}w | {pc['title'][:40]}")
            db.commit()
        except Exception as e:
            print(f"  ✗ Error: {e}")
            db.rollback()

    db.close()
    print(f"\nDone! Injected {total_added} versioned items with full audit trail.")

if __name__ == "__main__":
    run()
