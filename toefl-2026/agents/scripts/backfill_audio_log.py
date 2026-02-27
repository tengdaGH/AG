import sqlite3
import json
import os
import sys
from pathlib import Path

# Fix path to import log_audio
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, ".agent/skills/toefl_voice_direction"))

try:
    from log_audio import append_voice_log, set_log_path, read_log
except ImportError:
    print("Error: Could not import log_audio.py")
    sys.exit(1)

DB_PATH = os.path.join(PROJECT_ROOT, "backend/toefl_2026.db")
LOG_PATH = os.path.join(PROJECT_ROOT, "audio/audio_voice_log.jsonl")

set_log_path(LOG_PATH)

def backfill():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Get all items with wav audio
    cur.execute("SELECT id, task_type, media_url, prompt_content FROM test_items WHERE media_url LIKE '%.wav'")
    rows = cur.fetchall()

    # Load existing logs to avoid duplicates
    existing_entries = read_log()
    existing_ids = set(entry["item_id"] for entry in existing_entries)

    added = 0
    for row in rows:
        item_id = row["id"]
        task_type = row["task_type"]
        media_url = row["media_url"]
        pc = json.loads(row["prompt_content"] or "{}")

        # Handle Take An Interview separately as it has multiple files
        if task_type == "TAKE_AN_INTERVIEW":
            # Scenario
            scenario_url = pc.get("scenario_audio_url")
            if scenario_url and f"{item_id}_scenario" not in existing_ids:
                append_voice_log(
                    item_id=f"{item_id}_scenario",
                    task_type=task_type,
                    audio_file=scenario_url,
                    engine="gemini-2.5-flash-preview-tts", # Assumed for backfill
                    mode="single",
                    notes="Backfilled"
                )
                added += 1
            
            # Questions
            for i, q in enumerate(pc.get("questions", [])):
                q_url = q.get("audio_url")
                if q_url and f"{item_id}_q{i}" not in existing_ids:
                    append_voice_log(
                        item_id=f"{item_id}_q{i}",
                        task_type=task_type,
                        audio_file=q_url,
                        engine="gemini-2.5-flash-preview-tts",
                        mode="single",
                        notes="Backfilled"
                    )
                    added += 1
            continue

        # Other types
        if item_id in existing_ids:
            continue

        append_voice_log(
            item_id=item_id,
            task_type=task_type,
            audio_file=media_url,
            engine="gemini-2.5-flash-preview-tts",
            mode="single" if "multi" not in str(pc).lower() else "multi",
            notes="Backfilled"
        )
        added += 1

    print(f"Backfilled {added} entries.")
    conn.close()

if __name__ == "__main__":
    backfill()
