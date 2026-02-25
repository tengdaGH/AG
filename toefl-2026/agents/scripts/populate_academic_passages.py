# ============================================================
# Purpose:       Generate 3 new Read Academic Passage items (B2/C1/C2) to reach the 10-form target using Gemini.
# Usage:         python agents/scripts/populate_academic_passages.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
Generate 3 new Read Academic Passage items to reach the 10-form target of 20.
Levels: 1×B2 (History), 1×C1 (Life Science), 1×C2 (Physical Science).
"""
import os, sys, json, uuid, re
from dotenv import load_dotenv
from google import genai
from google.genai import types

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.append(backend_dir)

from app.database.connection import SessionLocal, engine, Base
from app.models.models import TestItem, SectionType, CEFRLevel, TaskType, ItemStatus

Base.metadata.create_all(bind=engine)
load_dotenv(os.path.join(backend_dir, '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Please set GEMINI_API_KEY in backend/.env.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

PASSAGES_TO_GENERATE = [
    {
        "level": "B2",
        "subject": "History / Art",
        "topic_hint": "The development of public museums and their role in democratizing access to art and culture",
        "irt_difficulty": 0.8,
    },
    {
        "level": "C1",
        "subject": "Life Science",
        "topic_hint": "How microbiomes in the human gut influence brain function through the gut-brain axis",
        "irt_difficulty": 1.5,
    },
    {
        "level": "C2",
        "subject": "Physical Science",
        "topic_hint": "The physics of superconductivity and its potential applications in energy transmission",
        "irt_difficulty": 2.2,
    },
]

# Load manual excerpt for system prompt
manual_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../rr_25_12_extracted.txt'))
with open(manual_path, 'r', encoding='utf-8', errors='ignore') as f:
    manual_text = f.read()[:15000]

SYSTEM_PROMPT = f"""You are an ETS-certified Language Assessment Designer.
Follow the TOEFL 2026 RR-25-12 spec strictly for Read an Academic Passage items.

MANUAL EXCERPT:
{manual_text}
"""


def build_prompt(spec):
    return f"""Generate ONE "Read an Academic Passage" item as a JSON object.

REQUIREMENTS:
- CEFR Level: {spec['level']}
- Subject Area: {spec['subject']}
- Topic seed: {spec['topic_hint']}
- Passage length: ~200 words (CRITICAL — do NOT truncate)
- Questions: EXACTLY 5 multiple-choice questions
- Each question has exactly 4 options and a correct_answer (0-indexed integer)
- Question types should cover: factual detail, vocabulary-in-context, inference, main idea, and author purpose
- Distribute correct answer keys across positions 0-3 (do NOT cluster them)
- Every option must be ≥5 characters
- Every question stem must be ≥10 characters

JSON schema:
{{
  "type": "Read an Academic Passage",
  "title": "Descriptive Title",
  "text": "Full passage text (~200 words)...",
  "questions": [
    {{
      "question_num": 1,
      "text": "Question stem...",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 0
    }}
  ]
}}

Output ONLY the raw JSON object. No markdown. No commentary."""


def generate_passage(spec):
    prompt = build_prompt(spec)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
        )
    )
    text = response.text
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        return None
    data = json.loads(match.group(0))
    return data


def validate_passage(data):
    """Quick structural validation."""
    text = data.get("text", "")
    questions = data.get("questions", [])
    word_count = len(text.split())

    errors = []
    if word_count < 100:
        errors.append(f"Passage too short: {word_count} words")
    if len(questions) != 5:
        errors.append(f"Expected 5 questions, got {len(questions)}")
    for q in questions:
        if len(q.get("options", [])) != 4:
            errors.append(f"Q{q.get('question_num')}: need 4 options")
        if not isinstance(q.get("correct_answer"), int):
            errors.append(f"Q{q.get('question_num')}: correct_answer must be int")
    return errors


def run():
    db = SessionLocal()
    generated = 0

    for spec in PASSAGES_TO_GENERATE:
        print(f"\n{'='*60}")
        print(f"  Generating {spec['level']} passage: {spec['subject']}")
        print(f"  Topic: {spec['topic_hint']}")
        print(f"{'='*60}")

        for attempt in range(3):
            try:
                data = generate_passage(spec)
                if not data:
                    print(f"  [attempt {attempt+1}] No JSON found, retrying...")
                    continue

                errors = validate_passage(data)
                if errors:
                    print(f"  [attempt {attempt+1}] Validation errors: {errors}")
                    continue

                word_count = len(data["text"].split())
                print(f"  ✓ Generated: \"{data.get('title', 'Untitled')}\" ({word_count} words, 5 Qs)")

                item = TestItem(
                    id=str(uuid.uuid4()),
                    section=SectionType.READING,
                    task_type=TaskType.READ_ACADEMIC_PASSAGE,
                    target_level=CEFRLevel[spec["level"]],
                    irt_difficulty=spec["irt_difficulty"],
                    irt_discrimination=1.0,
                    prompt_content=json.dumps(data),
                    is_active=True,
                    lifecycle_status=ItemStatus.DRAFT,
                    version=1,
                    generated_by_model="gemini-2.5-flash",
                    generation_notes=f"Academic Passage ({spec['subject']}). {word_count}w, 5Qs.",
                )
                db.add(item)
                db.commit()
                generated += 1
                print(f"  ✓ Saved to DB as DRAFT (will QA next).")
                break

            except Exception as e:
                print(f"  [attempt {attempt+1}] Error: {e}")
                import traceback
                traceback.print_exc()

    db.close()
    print(f"\n{'='*60}")
    print(f"  DONE! Generated {generated}/3 Academic Passages.")
    print(f"{'='*60}")


if __name__ == "__main__":
    run()
