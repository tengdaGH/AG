# ============================================================
# Purpose:       Populate all 4 listening task types with text + MCQs (no TTS); tags items as PENDING_TTS for deferred audio generation.
# Usage:         python agents/scripts/populate_listening.py [--type lcr|conversation|announcement|talk|all]
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
Populate Listening section items (text + MCQs only, NO TTS).
Generates items for all 4 listening task types to reach 10-form capacity.

TTS audio generation is deferred — run recover_listening_audio.py when quota resets.
Items are tagged with 'PENDING_TTS' in generation_notes for easy tracking.

Usage:
    cd toefl-2026
    source backend/venv/bin/activate
    python agents/scripts/populate_listening.py
"""
import os, sys, json, uuid, re, time, argparse
from dotenv import load_dotenv
from google import genai
from google.genai import types

os.environ['PYTHONUNBUFFERED'] = '1'

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

manual_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../specs/toefl_2026_technical_manual.md'))
with open(manual_path, 'r', encoding='utf-8', errors='ignore') as f:
    manual_text = f.read()[:8000]

SYSTEM = f"""You are an ETS-certified Language Assessment Designer for TOEFL 2026.
Follow the RR-25-12 spec for Listening items. All output must be valid JSON only.
{manual_text}
"""

# ═══════════════════════════════════════════════════════════════════════════
#  LISTEN & CHOOSE RESPONSE — need ~60 more (have 90, need 150)
# ═══════════════════════════════════════════════════════════════════════════
LCR_TOPICS = [
    # A1 (15 items)
    {"topic": "Greetings", "level": "A1", "diff": -2.0, "count": 3},
    {"topic": "Asking for directions", "level": "A1", "diff": -1.8, "count": 3},
    {"topic": "At a store", "level": "A1", "diff": -1.6, "count": 3},
    {"topic": "Weather talk", "level": "A1", "diff": -1.8, "count": 3},
    {"topic": "Classroom basics", "level": "A1", "diff": -2.0, "count": 3},
    # A2 (20 items)
    {"topic": "Ordering at a restaurant", "level": "A2", "diff": -1.0, "count": 4},
    {"topic": "Making plans with friends", "level": "A2", "diff": -0.8, "count": 4},
    {"topic": "Doctor appointment", "level": "A2", "diff": -0.6, "count": 4},
    {"topic": "Library help desk", "level": "A2", "diff": -0.8, "count": 4},
    {"topic": "Campus events", "level": "A2", "diff": -0.6, "count": 4},
    # B1 (15 items)
    {"topic": "Job interview small talk", "level": "B1", "diff": 0.0, "count": 3},
    {"topic": "Resolving a misunderstanding", "level": "B1", "diff": 0.2, "count": 3},
    {"topic": "Travel arrangements", "level": "B1", "diff": 0.0, "count": 3},
    {"topic": "Discussing a movie", "level": "B1", "diff": 0.2, "count": 3},
    {"topic": "Returning a purchase", "level": "B1", "diff": 0.0, "count": 3},
    # B2 (10 items)
    {"topic": "Debating study methods", "level": "B2", "diff": 0.8, "count": 3},
    {"topic": "Workplace disagreement", "level": "B2", "diff": 1.0, "count": 4},
    {"topic": "Discussing current events", "level": "B2", "diff": 0.8, "count": 3},
]

LCR_PROMPT_TEMPLATE = """Generate exactly {count} TOEFL 2026 "Listen and Choose a Response" items as a JSON array.
Topic: "{topic}" | CEFR Level: {level}

Each item is a short 2-speaker exchange where the test taker hears a spoken question/statement
and selects the most appropriate response from 4 written options.

JSON schema per item:
{{{{
  "title": "Response: {topic} (unique-id)",
  "topic": "{topic}",
  "dialogue": ["Speaker 1 says something...", "Speaker 2 responds..."],
  "audio_url": "PENDING_TTS",
  "questions": [{{{{
    "question": "What would be the most appropriate response?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 0,
    "explanation": "Brief explanation..."
  }}}}]
}}}}

Rules:
- Each item has ONE question with 4 options
- The dialogue is everyday life context
- Distribute correct_answer across positions 0-3
- Options must each be ≥5 characters
- Vocabulary level: {level_hint}

Output ONLY the raw JSON array. No markdown."""

# ═══════════════════════════════════════════════════════════════════════════
#  LISTEN TO A CONVERSATION — need ~20
# ═══════════════════════════════════════════════════════════════════════════
CONV_SCENARIOS = [
    {"topic": "Study group meeting", "setting": "Campus", "level": "A2", "diff": -0.5},
    {"topic": "Roommate conflict", "setting": "Dormitory", "level": "B1", "diff": 0.0},
    {"topic": "Planning a birthday party", "setting": "Social", "level": "A2", "diff": -0.5},
    {"topic": "Lost and found item", "setting": "Campus", "level": "A2", "diff": -0.8},
    {"topic": "Rescheduling a meeting", "setting": "Office", "level": "B1", "diff": 0.2},
    {"topic": "Choosing elective courses", "setting": "University", "level": "B1", "diff": 0.2},
    {"topic": "Apartment hunting", "setting": "Daily Life", "level": "B1", "diff": 0.0},
    {"topic": "Returning library books", "setting": "Campus", "level": "A2", "diff": -0.6},
    {"topic": "Travel planning for break", "setting": "Social", "level": "B1", "diff": 0.2},
    {"topic": "Car repair issues", "setting": "Daily Life", "level": "B1", "diff": 0.0},
    {"topic": "Discussing a professor's feedback", "setting": "University", "level": "B2", "diff": 0.8},
    {"topic": "Moving to a new city", "setting": "Daily Life", "level": "B2", "diff": 0.8},
    {"topic": "Buying concert tickets", "setting": "Entertainment", "level": "A2", "diff": -0.6},
    {"topic": "Cooking dinner together", "setting": "Home", "level": "A2", "diff": -0.8},
    {"topic": "Gym membership discussion", "setting": "Health", "level": "B1", "diff": 0.0},
    {"topic": "Preparing for a job fair", "setting": "Campus", "level": "B1", "diff": 0.2},
    {"topic": "Dealing with a noisy neighbor", "setting": "Home", "level": "B2", "diff": 0.8},
    {"topic": "Organizing a fundraiser", "setting": "Campus", "level": "B2", "diff": 1.0},
    {"topic": "Weekend hiking plan", "setting": "Social", "level": "A2", "diff": -0.5},
    {"topic": "Discussing internship options", "setting": "University", "level": "C1", "diff": 1.5},
]

CONV_PROMPT_TEMPLATE = """Generate ONE TOEFL 2026 "Listen to a Conversation" item as a JSON object.
Topic: "{topic}" | Setting: {setting} | CEFR Level: {level}

Format: A natural conversation between two speakers about an everyday topic.
The conversation should be 100-180 words. Include 4 MCQ questions.

JSON schema:
{{{{
  "title": "{topic}",
  "topic": "{setting}",
  "text": "Full conversation transcript with speaker labels (F:, M:) on alternating lines...",
  "audio_url": "PENDING_TTS",
  "questions": [
    {{{{
      "question": "Question about the conversation...",
      "options": ["A", "B", "C", "D"],
      "correct_answer": 0,
      "explanation": "Why this answer..."
    }}}}
  ]
}}}}

Question types should include: main idea, supporting detail, inference, prediction.
Distribute correct_answer keys across positions 0-3. Each option ≥5 chars.
Output ONLY the raw JSON object. No markdown."""

# ═══════════════════════════════════════════════════════════════════════════
#  LISTEN TO AN ANNOUNCEMENT — need ~5
# ═══════════════════════════════════════════════════════════════════════════
ANNOUNCE_SCENARIOS = [
    {"title": "Campus Shuttle Schedule Change", "context": "Transportation Office", "level": "A2", "diff": -0.5},
    {"title": "New Recycling Program", "context": "Campus Sustainability Office", "level": "B1", "diff": 0.2},
    {"title": "Scholarship Application Deadline", "context": "Financial Aid Office", "level": "B1", "diff": 0.0},
    {"title": "Emergency Weather Update", "context": "University Administration", "level": "A2", "diff": -0.6},
    {"title": "Student Art Exhibition Opening", "context": "Arts Department", "level": "B2", "diff": 0.8},
]

ANNOUNCE_PROMPT = """Generate ONE TOEFL 2026 "Listen to an Announcement" item as a JSON object.
Title: "{title}" | Context: {context} | CEFR Level: {level}

Format: A short academic-related announcement (monologic speech, 80-150 words).
Include 2-3 MCQ questions about the announcement.

JSON schema:
{{{{
  "title": "{title}",
  "context": "{context}",
  "text": "Full transcript of the announcement...",
  "audio_url": "PENDING_TTS",
  "questions": [
    {{{{
      "question": "What is the main purpose...?",
      "options": ["A", "B", "C", "D"],
      "correct_answer": 0,
      "explanation": "Why..."
    }}}}
  ]
}}}}

Output ONLY the raw JSON. No markdown."""

# ═══════════════════════════════════════════════════════════════════════════
#  LISTEN TO AN ACADEMIC TALK — need ~2
# ═══════════════════════════════════════════════════════════════════════════
TALK_SCENARIOS = [
    {"title": "The Science of Sleep", "subject": "Life Science", "level": "B2", "diff": 0.8},
    {"title": "Urban Heat Islands", "subject": "Physical Science", "level": "C1", "diff": 1.5},
]

TALK_PROMPT = """Generate ONE TOEFL 2026 "Listen to an Academic Talk" item as a JSON object.
Title: "{title}" | Subject: {subject} | CEFR Level: {level}

Format: A short academic talk by an educator (175-250 words). Monologic.
Include 4 MCQ questions (main idea, supporting detail, inference, vocabulary).

JSON schema:
{{{{
  "title": "{title}",
  "context": "{subject}",
  "text": "Full transcript of the talk (~200 words)...",
  "audio_url": "PENDING_TTS",
  "questions": [
    {{{{
      "question": "Question about the talk...",
      "options": ["A", "B", "C", "D"],
      "correct_answer": 0,
      "explanation": "Why..."
    }}}}
  ]
}}}}

CRITICAL: The talk MUST be 175-250 words. Do NOT truncate.
Output ONLY the raw JSON object. No markdown."""


def generate_json(prompt, expect_array=False, max_retries=3):
    """Call Gemini and parse JSON from response."""
    for attempt in range(max_retries):
        try:
            resp = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM, temperature=0.8,
                )
            )
            text = resp.text
            if expect_array:
                match = re.search(r'\[.*\]', text, re.DOTALL)
            else:
                match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            print(f"    [attempt {attempt+1}] No JSON found in response", flush=True)
        except Exception as e:
            print(f"    [attempt {attempt+1}] Error: {e}", flush=True)
            time.sleep(5)
    return None


def save_item(db, task_type, level, diff, data, notes_extra=""):
    """Save a single item to DB."""
    item = TestItem(
        id=str(uuid.uuid4()),
        section=SectionType.LISTENING,
        task_type=task_type,
        target_level=CEFRLevel[level],
        irt_difficulty=diff,
        irt_discrimination=1.0,
        prompt_content=json.dumps(data),
        is_active=True,
        lifecycle_status=ItemStatus.DRAFT,
        version=1,
        generated_by_model="gemini-2.5-flash",
        generation_notes=f"PENDING_TTS. {notes_extra}",
    )
    db.add(item)
    return item


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', choices=['lcr', 'conversation', 'announcement', 'talk', 'all'], default='all')
    args = parser.parse_args()

    db = SessionLocal()
    stats = {"lcr": 0, "conversation": 0, "announcement": 0, "talk": 0}

    # ─── Listen & Choose Response ────────────────────────────────────────
    if args.type in ('lcr', 'all'):
        print("\n" + "="*60, flush=True)
        print("  LISTEN & CHOOSE RESPONSE", flush=True)
        print("="*60, flush=True)

        for batch in LCR_TOPICS:
            level_hints = {'A1':'Very simple vocabulary and short sentences.','A2':'Simple vocabulary, short to medium sentences.','B1':'Moderately complex language.','B2':'Sophisticated vocabulary and nuanced register.'}
            prompt = LCR_PROMPT_TEMPLATE.format(level_hint=level_hints.get(batch['level'],'Moderate vocabulary.'), **batch)
            print(f"\n  [{batch['level']}] {batch['topic']} (×{batch['count']})...", end="", flush=True)

            items = generate_json(prompt, expect_array=True)
            if not items:
                print(" ✗ Failed", flush=True)
                continue

            for item_data in items[:batch["count"]]:
                save_item(db, TaskType.LISTEN_CHOOSE_RESPONSE, batch["level"], batch["diff"],
                          item_data, f"LCR: {batch['topic']} ({batch['level']})")
                stats["lcr"] += 1

            db.commit()
            print(f" ✓ {len(items[:batch['count']])} items", flush=True)
            time.sleep(2)

    # ─── Listen to a Conversation ────────────────────────────────────────
    if args.type in ('conversation', 'all'):
        print("\n" + "="*60, flush=True)
        print("  LISTEN TO A CONVERSATION", flush=True)
        print("="*60, flush=True)

        for sc in CONV_SCENARIOS:
            prompt = CONV_PROMPT_TEMPLATE.format(**sc)
            print(f"\n  [{sc['level']}] {sc['topic']}...", end="", flush=True)

            data = generate_json(prompt, expect_array=False)
            if not data:
                print(" ✗ Failed", flush=True)
                continue

            save_item(db, TaskType.LISTEN_CONVERSATION, sc["level"], sc["diff"],
                      data, f"Conversation: {sc['topic']} ({sc['level']})")
            db.commit()
            stats["conversation"] += 1
            print(f" ✓", flush=True)
            time.sleep(2)

    # ─── Listen to an Announcement ───────────────────────────────────────
    if args.type in ('announcement', 'all'):
        print("\n" + "="*60, flush=True)
        print("  LISTEN TO AN ANNOUNCEMENT", flush=True)
        print("="*60, flush=True)

        for sc in ANNOUNCE_SCENARIOS:
            prompt = ANNOUNCE_PROMPT.format(**sc)
            print(f"\n  [{sc['level']}] {sc['title']}...", end="", flush=True)

            data = generate_json(prompt, expect_array=False)
            if not data:
                print(" ✗ Failed", flush=True)
                continue

            save_item(db, TaskType.LISTEN_ANNOUNCEMENT, sc["level"], sc["diff"],
                      data, f"Announcement: {sc['title']} ({sc['level']})")
            db.commit()
            stats["announcement"] += 1
            print(f" ✓", flush=True)
            time.sleep(2)

    # ─── Listen to an Academic Talk ──────────────────────────────────────
    if args.type in ('talk', 'all'):
        print("\n" + "="*60, flush=True)
        print("  LISTEN TO AN ACADEMIC TALK", flush=True)
        print("="*60, flush=True)

        for sc in TALK_SCENARIOS:
            prompt = TALK_PROMPT.format(**sc)
            print(f"\n  [{sc['level']}] {sc['title']}...", end="", flush=True)

            data = generate_json(prompt, expect_array=False)
            if not data:
                print(" ✗ Failed", flush=True)
                continue

            wc = len(data.get("text", "").split())
            save_item(db, TaskType.LISTEN_ACADEMIC_TALK, sc["level"], sc["diff"],
                      data, f"Academic Talk: {sc['title']} ({wc}w, {sc['level']})")
            db.commit()
            stats["talk"] += 1
            print(f" ✓ ({wc}w)", flush=True)
            time.sleep(2)

    db.close()

    print("\n" + "="*60, flush=True)
    print(f"  DONE! Generated:", flush=True)
    for k, v in stats.items():
        if v > 0:
            print(f"    {k}: {v} items", flush=True)
    print(f"  Total: {sum(stats.values())} new items (all PENDING_TTS)", flush=True)
    print(f"\n  To generate TTS audio later, run:", flush=True)
    print(f"    python agents/scripts/recover_listening_audio.py", flush=True)
    print("="*60, flush=True)


if __name__ == "__main__":
    run()
