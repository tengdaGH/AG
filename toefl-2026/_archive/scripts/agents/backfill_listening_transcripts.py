# ============================================================
# Purpose:       Backfill missing transcript text for legacy listening items that have audio but only contain a context stub in the text field.
# Usage:         python agents/scripts/backfill_listening_transcripts.py [--apply] [--delay N]
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
Backfill missing transcript text for legacy listening items.

These items have audio files and questions but their `text` field only contains
the context string (e.g., "History class") instead of the actual transcript.
This script generates proper transcripts using Gemini and updates the DB.

Usage:
    cd toefl-2026
    source backend/venv/bin/activate
    python agents/scripts/backfill_listening_transcripts.py          # dry-run
    python agents/scripts/backfill_listening_transcripts.py --apply  # commit
"""
import os, sys, json, re, time, argparse
from dotenv import load_dotenv
from google import genai
from google.genai import types

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.append(backend_dir)

from app.database.connection import SessionLocal
from app.models.models import TestItem, SectionType, TaskType

load_dotenv(os.path.join(backend_dir, '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Set GEMINI_API_KEY in backend/.env")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)


def find_incomplete_items(db):
    """Find listening items with text == context stub (no real transcript)."""
    items = db.query(TestItem).filter(TestItem.section == SectionType.LISTENING).all()
    incomplete = []
    for item in items:
        c = json.loads(item.prompt_content)
        text = c.get('text', '')
        wc = len(text.split()) if text else 0

        # Only Announcement and Academic Talk items can have context stubs
        if item.task_type in (TaskType.LISTEN_ANNOUNCEMENT, TaskType.LISTEN_ACADEMIC_TALK):
            if wc <= 10:
                incomplete.append(item)

    return incomplete


def generate_transcript(title, context, task_type, questions, max_retries=3):
    """Generate a transcript that matches existing questions."""
    q_text = "\n".join(f"  Q{i+1}: {q.get('question',q.get('text',''))}" for i, q in enumerate(questions))

    if task_type == TaskType.LISTEN_ANNOUNCEMENT:
        prompt = f"""Generate a TOEFL 2026 "Listen to an Announcement" transcript.

Title: "{title}"
Context: {context}
The announcement must contain the information needed to answer these questions:
{q_text}

Write a short campus announcement (80-150 words), monologic format.
The speaker should be addressing students in an academic/campus setting.
Output ONLY the transcript text, no JSON, no markdown fencing, no commentary."""
    else:  # Academic Talk
        prompt = f"""Generate a TOEFL 2026 "Listen to an Academic Talk" transcript.

Title: "{title}"
Context: {context}
The talk must contain the information needed to answer these questions:
{q_text}

Write a short academic talk by a professor or educator (175-250 words), monologic format.
The talk should be educational and engaging, as if spoken to students in a classroom.
Output ONLY the transcript text, no JSON, no markdown fencing, no commentary."""

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt],
                config=types.GenerateContentConfig(temperature=0.7)
            )
            text = response.text.strip()
            text = re.sub(r'^```\w*\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
            return text.strip()
        except Exception as e:
            print(f"  [error] Transcript generation failed: {e}", flush=True)
            time.sleep(5)
    return None


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Commit transcript updates')
    parser.add_argument('--delay', type=int, default=6, help='Seconds between API calls')
    args = parser.parse_args()

    db = SessionLocal()
    items = find_incomplete_items(db)

    print(f"\n{'='*60}")
    print(f"  TRANSCRIPT BACKFILL")
    print(f"{'='*60}")
    print(f"  Items needing transcripts: {len(items)}")
    print(f"  Mode: {'APPLY' if args.apply else 'DRY RUN'}")
    print()

    if not args.apply:
        for i, item in enumerate(items):
            c = json.loads(item.prompt_content)
            q = c.get('questions', [])
            print(f"  {i+1:2}. [{item.target_level.name}] {item.task_type.value[:22]:22s} | text=\"{c.get('text','')[:30]}\" | q={len(q)} | \"{c.get('title','?')[:40]}\"")
        print(f"\n  [DRY RUN] Pass --apply to generate transcripts.")
        db.close()
        return

    success = 0
    for idx, item in enumerate(items):
        c = json.loads(item.prompt_content)
        title = c.get('title', '?')
        context = c.get('context', '')
        questions = c.get('questions', [])

        print(f"  [{idx+1}/{len(items)}] \"{title}\"...", end="", flush=True)

        transcript = generate_transcript(title, context, item.task_type, questions)
        if transcript:
            wc = len(transcript.split())
            c['text'] = transcript
            item.prompt_content = json.dumps(c)
            old_notes = item.generation_notes or ''
            item.generation_notes = f"Transcript backfilled ({wc}w). {old_notes}"
            db.commit()
            success += 1
            print(f" ✓ ({wc}w)", flush=True)
        else:
            print(f" ✗", flush=True)

        time.sleep(args.delay)

    db.close()
    print(f"\n{'='*60}")
    print(f"  DONE! Backfilled {success}/{len(items)} transcripts.")
    print(f"{'='*60}")


if __name__ == '__main__':
    run()
