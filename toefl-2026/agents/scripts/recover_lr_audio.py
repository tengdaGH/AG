# ============================================================
# Purpose:       Recovery script for Listen and Repeat Scenario 10 (Office Hours): Phase 1 generates text, Phase 2 generates TTS audio.
# Usage:         python agents/scripts/recover_lr_audio.py [--text-only | --tts-only]
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
Recovery script for Listen and Repeat: Scenario 10 (Office Hours with Professor).
Phase 1: Generate text items and save to DB (no audio, placeholder URLs).
Phase 2: Retry TTS for any items with placeholder audio URLs (run separately when quota resets).

Usage:
    python agents/scripts/recover_lr_audio.py --text-only   # Phase 1: Generate text
    python agents/scripts/recover_lr_audio.py --tts-only    # Phase 2: Generate TTS audio
    python agents/scripts/recover_lr_audio.py               # Both phases
"""
import os
import sys
import json
import uuid
import re
import time
import argparse
from dotenv import load_dotenv
from google import genai
from google.genai import types

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.append(backend_dir)

from app.database.connection import SessionLocal, engine, Base
from app.models.models import TestItem, SectionType, CEFRLevel, TaskType

Base.metadata.create_all(bind=engine)
load_dotenv(os.path.join(backend_dir, '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Please set GEMINI_API_KEY in backend/.env.")
    sys.exit(1)

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

FRONTEND_AUDIO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend/public/audio'))
os.makedirs(FRONTEND_AUDIO_DIR, exist_ok=True)

TTS_DELAY = 10  # Mandatory 10s delay between TTS calls

SCENARIO_10 = {
    "name": "Office Hours with Professor",
    "setting": "Academic",
    "description": "A professor is explaining their office hours policies and how students can get help with coursework.",
    "voice": "Fenrir",
}


def generate_voice_line(voice_name, text, filename, max_retries=3):
    """Generates TTS audio with mandatory 10s delay and PCM→MP3 conversion."""
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        print(f"      [skip] {os.path.basename(filename)} already exists.")
        return True

    prompt = f"Generate audio from this precise transcript without adding or modifying anything:\n{text}"

    for attempt in range(max_retries):
        try:
            print(f"      [tts] Attempt {attempt+1}/{max_retries}...")
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash-preview-tts',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['AUDIO'],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                        )
                    )
                )
            )
            for part in response.candidates[0].content.parts:
                if getattr(part, 'inline_data', None) and getattr(part.inline_data, 'data', None):
                    pcm_filename = filename.replace(".mp3", ".pcm")
                    with open(pcm_filename, 'wb') as f:
                        f.write(part.inline_data.data)
                    os.system(f"ffmpeg -y -f s16le -ar 24000 -ac 1 -i '{pcm_filename}' '{filename}' > /dev/null 2>&1")
                    if os.path.exists(pcm_filename):
                        os.remove(pcm_filename)
                    break
            # Mandatory 10s delay
            print(f"      [ok] Audio generated. Sleeping {TTS_DELAY}s...")
            time.sleep(TTS_DELAY)
            return True
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 60 * (attempt + 1)
                print(f"      [rate-limit] Sleeping {wait}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                print(f"      [error] TTS failed: {e}")
                return False
    return False


def phase_1_text_only():
    """Generate text items for Scenario 10 and save to DB with placeholder audio."""
    print("\n" + "=" * 60)
    print("  PHASE 1: Generate text for Scenario 10 (Office Hours)")
    print("=" * 60)

    db = SessionLocal()

    # Check if Scenario 10 items already exist
    existing = db.query(TestItem).filter(
        TestItem.task_type == TaskType.LISTEN_AND_REPEAT,
        TestItem.generation_notes.like('%Office Hours%')
    ).all()

    if existing:
        print(f"  ⚠ Found {len(existing)} existing 'Office Hours' items. Skipping text generation.")
        db.close()
        return

    prompt = f"""Generate exactly 9 TOEFL 2026 "Listen and Repeat" sentences for a single scenario as a JSON array.

SCENARIO: "{SCENARIO_10['name']}" — {SCENARIO_10['description']}
Setting: {SCENARIO_10['setting']}

Rules:
- Each item in the array represents ONE sentence the test taker will hear and repeat.
- Sentences MUST get progressively longer and more complex.
- Start with very short, simple sentences (4-6 words) and end with long, complex ones (22-30 words).
- All sentences must be thematically connected to the scenario.
- Sentences should sound natural.

CEFR difficulty ramp:
  - Sentences 1-2: CEFR A1 (4-6 words, IRT difficulty around -2.0 to -1.5)
  - Sentences 3-4: CEFR A2 (6-10 words, IRT difficulty around -1.0 to -0.5)
  - Sentences 5-6: CEFR B1 (10-15 words, IRT difficulty around -0.2 to 0.5)
  - Sentences 7-8: CEFR B2 (15-22 words, IRT difficulty around 0.8 to 1.5)
  - Sentence 9: CEFR C1 (22-30 words, IRT difficulty around 2.0)

JSON schema per item:
{{"section":"SPEAKING","target_level":"A1","irt_difficulty":-1.8,"irt_discrimination":0.9,"prompt_content":{{"type":"Listen and Repeat","title":"Office Hours with Professor","sentences":[{{"text":"Please visit my office.","audioUrl":"PLACEHOLDER"}}]}},"is_active":true}}

Output ONLY the raw JSON array. No markdown. No commentary."""

    try:
        print("  [1/2] Generating text via Gemini 2.5 Flash...")
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(temperature=0.7)
        )
        content = response.text

        match = re.search(r'\[.*\]', content, re.DOTALL)
        if not match:
            print("  ✗ No JSON found. Aborting.")
            db.close()
            return

        items = json.loads(match.group(0))
        print(f"  ↪ Got {len(items)} sentences.")

        total_added = 0
        for i, item_data in enumerate(items):
            pc = item_data.get("prompt_content", {})
            sentences = pc.get("sentences", [])
            if not sentences:
                continue

            text = sentences[0].get("text", "")
            word_count = len(text.split())

            # Set placeholder audio URL — will be filled by Phase 2
            audio_filename = f"lr_{uuid.uuid4().hex[:12]}.mp3"
            sentences[0]["audioUrl"] = f"audio/{audio_filename}"
            sentences[0]["_pending_tts"] = True  # marker for Phase 2
            sentences[0]["_audio_filepath"] = os.path.join(FRONTEND_AUDIO_DIR, audio_filename)

            new_item = TestItem(
                id=str(uuid.uuid4()),
                section=SectionType.SPEAKING,
                task_type=TaskType.LISTEN_AND_REPEAT,
                target_level=CEFRLevel[item_data["target_level"]],
                irt_difficulty=item_data.get("irt_difficulty", 0.0),
                irt_discrimination=item_data.get("irt_discrimination", 1.0),
                prompt_content=json.dumps(pc),
                is_active=True,
                version=1,
                generated_by_model="gemini-2.5-flash + Gemini 2.5 Flash TTS",
                generation_notes=f"L&R pool. Scenario: Office Hours with Professor. {word_count}w. PENDING_TTS."
            )
            db.add(new_item)
            total_added += 1
            print(f"    [{i+1}] {item_data.get('target_level','??'):3s} | {word_count:2d}w | \"{text[:60]}\"")

        db.commit()
        print(f"\n  ✓ Committed {total_added} text-only items (audio pending).")

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def phase_2_tts_only():
    """Find all items with PENDING_TTS in generation_notes and generate their audio."""
    print("\n" + "=" * 60)
    print("  PHASE 2: Generate TTS audio for pending items")
    print("=" * 60)

    db = SessionLocal()
    pending = db.query(TestItem).filter(
        TestItem.task_type == TaskType.LISTEN_AND_REPEAT,
        TestItem.generation_notes.like('%PENDING_TTS%')
    ).all()

    if not pending:
        print("  ✓ No pending TTS items found. All audio is up to date.")
        db.close()
        return

    print(f"  Found {len(pending)} items needing TTS audio.")
    voice = SCENARIO_10["voice"]
    success_count = 0

    for i, item in enumerate(pending):
        pc = json.loads(item.prompt_content)
        sentences = pc.get("sentences", [])
        if not sentences:
            continue

        text = sentences[0].get("text", "")
        audio_url = sentences[0].get("audioUrl", "")
        audio_filename = audio_url.replace("audio/", "") if audio_url.startswith("audio/") else f"lr_{uuid.uuid4().hex[:12]}.mp3"
        audio_filepath = os.path.join(FRONTEND_AUDIO_DIR, audio_filename)

        print(f"\n    [{i+1}/{len(pending)}] ({voice}) \"{text[:60]}\"")

        success = generate_voice_line(voice, text, audio_filepath)

        if success:
            # Update DB: remove PENDING_TTS marker, clean up internal fields
            sentences[0]["audioUrl"] = f"audio/{audio_filename}"
            sentences[0].pop("_pending_tts", None)
            sentences[0].pop("_audio_filepath", None)
            item.prompt_content = json.dumps(pc)
            item.generation_notes = item.generation_notes.replace(" PENDING_TTS.", ".")
            db.commit()
            success_count += 1
            print(f"    ✓ Audio saved and DB updated.")
        else:
            print(f"    ✗ TTS failed. Will retry next run.")

    db.close()
    print(f"\n  ✓ Generated audio for {success_count}/{len(pending)} items.")


def main():
    parser = argparse.ArgumentParser(description="Recovery script for missing L&R audio")
    parser.add_argument("--text-only", action="store_true", help="Phase 1: Generate text items only")
    parser.add_argument("--tts-only", action="store_true", help="Phase 2: Generate TTS for pending items")
    args = parser.parse_args()

    if args.text_only:
        phase_1_text_only()
    elif args.tts_only:
        phase_2_tts_only()
    else:
        phase_1_text_only()
        phase_2_tts_only()

    # Final summary
    db = SessionLocal()
    total = db.query(TestItem).filter(
        TestItem.task_type == TaskType.LISTEN_AND_REPEAT
    ).count()
    pending = db.query(TestItem).filter(
        TestItem.task_type == TaskType.LISTEN_AND_REPEAT,
        TestItem.generation_notes.like('%PENDING_TTS%')
    ).count()
    db.close()

    print(f"\n{'='*60}")
    print(f"  SUMMARY: {total} total L&R items | {pending} still pending TTS")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
