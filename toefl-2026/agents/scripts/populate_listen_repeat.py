# ============================================================
# Purpose:       Populate the Listen and Repeat item pool: generates ~90 items across 10 scenarios with progressive CEFR difficulty using Gemini TTS.
# Usage:         python agents/scripts/populate_listen_repeat.py [--resume]
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
Populate Listen and Repeat item pool for 10 test forms.
Generates ~90 items across 10 scenarios with progressive CEFR difficulty.
Uses Gemini 1.5 Pro for text and Gemini 2.5 Flash TTS for audio.
"""
import os
import sys
import json
import uuid
import re
import time
import random
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

VOICES = ["Puck", "Aoede", "Charon", "Kore", "Fenrir"]

# ─── 10 Scenarios ───────────────────────────────────────────────────────────
SCENARIOS = [
    {
        "name": "Campus Tour",
        "setting": "Daily Life",
        "description": "A student guide is leading new students on a campus tour, pointing out buildings and facilities.",
        "voice": "Puck",
    },
    {
        "name": "Library Orientation",
        "setting": "Academic",
        "description": "A librarian is explaining how to use the university library, including borrowing policies and study rooms.",
        "voice": "Aoede",
    },
    {
        "name": "Cafeteria Ordering",
        "setting": "Daily Life",
        "description": "A cafeteria worker is explaining the menu options and ordering process to a new student.",
        "voice": "Kore",
    },
    {
        "name": "Lab Safety Briefing",
        "setting": "Academic",
        "description": "A teaching assistant is giving a safety briefing before students begin their first chemistry lab session.",
        "voice": "Charon",
    },
    {
        "name": "Dormitory Check-in",
        "setting": "Daily Life",
        "description": "A residence advisor is welcoming a new student to the dormitory, explaining rules and amenities.",
        "voice": "Fenrir",
    },
    {
        "name": "Museum Visit",
        "setting": "Daily Life",
        "description": "A museum guide is leading a group of students through a natural history exhibit.",
        "voice": "Aoede",
    },
    {
        "name": "Biology Lecture Introduction",
        "setting": "Academic",
        "description": "A professor is introducing the first biology lecture of the semester, outlining the course structure.",
        "voice": "Charon",
    },
    {
        "name": "Student Club Fair",
        "setting": "Daily Life",
        "description": "A student club president is recruiting new members at the university activities fair.",
        "voice": "Puck",
    },
    {
        "name": "Bookstore and Supplies",
        "setting": "Daily Life",
        "description": "A bookstore employee is helping a student find textbooks and supplies for their courses.",
        "voice": "Kore",
    },
    {
        "name": "Office Hours with Professor",
        "setting": "Academic",
        "description": "A professor is explaining their office hours policies and how students can get help with coursework.",
        "voice": "Fenrir",
    },
]


def build_scenario_prompt(scenario):
    """Build the LLM prompt for a single scenario."""
    return f"""Generate exactly 9 TOEFL 2026 "Listen and Repeat" sentences for a single scenario as a JSON array.

SCENARIO: "{scenario['name']}" — {scenario['description']}
Setting: {scenario['setting']}

Rules:
- Each item in the array represents ONE sentence the test taker will hear and repeat.
- Sentences MUST get progressively longer and more complex (this is critical for the TOEFL spec).
- Start with very short, simple sentences (4-6 words) and end with long, complex ones (22-30 words).
- All sentences must be thematically connected to the scenario above.
- Sentences should sound natural — like something a real person would say in this setting.
- DO NOT use overly formal or stilted language for lower-level sentences.

CEFR difficulty ramp (follow this distribution exactly):
  - Sentences 1-2: CEFR A1 (4-6 words, very simple grammar, IRT difficulty around -2.0 to -1.5)
  - Sentences 3-4: CEFR A2 (6-10 words, simple but slightly longer, IRT difficulty around -1.0 to -0.5)
  - Sentences 5-6: CEFR B1 (10-15 words, moderate complexity, IRT difficulty around -0.2 to 0.5)
  - Sentences 7-8: CEFR B2 (15-22 words, complex grammar and vocabulary, IRT difficulty around 0.8 to 1.5)
  - Sentence 9: CEFR C1 (22-30 words, advanced complexity with subordinate clauses, IRT difficulty around 2.0)

JSON schema per item:
{{"section":"SPEAKING","target_level":"A1","irt_difficulty":-1.8,"irt_discrimination":0.9,"prompt_content":{{"type":"Listen and Repeat","title":"{scenario['name']}","sentences":[{{"text":"Welcome to campus.","audioUrl":"placeholder"}}]}},"is_active":true}}

Output ONLY the raw JSON array. No markdown. No commentary."""


def generate_voice_line(voice_name, text, filename, max_retries=5):
    """Generates a single line of dialog with PCM→MP3 conversion.
    Uses exponential backoff (60s base) on 429 rate-limit errors.
    """
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        print(f"      [skip] {os.path.basename(filename)} already exists.")
        return True

    prompt = f"Generate audio from this precise transcript without adding or modifying anything:\n{text}"

    for attempt in range(max_retries):
        try:
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
            # Breathing room between successful calls to stay under RPM limit
            time.sleep(8)
            return True
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 60 * (2 ** attempt)  # 60s, 120s, 240s, 480s, 960s
                print(f"      [rate-limit] Sleeping {wait}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                print(f"      [error] TTS failed for '{text[:40]}': {e}")
                return False
    return False


def scenario_exists_in_db(db, scenario_name):
    """Check if a scenario's items already exist in the DB."""
    items = db.query(TestItem).filter(
        TestItem.task_type == TaskType.LISTEN_AND_REPEAT,
        TestItem.generation_notes.like(f"%Scenario: {scenario_name}.%")
    ).all()
    return len(items) >= 9  # Each scenario produces 9 items


def run():
    parser = argparse.ArgumentParser(description='Populate Listen and Repeat items')
    parser.add_argument('--resume', action='store_true',
                        help='Skip scenarios that already have 9+ items in the DB')
    args = parser.parse_args()

    manual_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../specs/toefl_2026_technical_manual.md'))
    with open(manual_path, 'r', encoding='utf-8', errors='ignore') as f:
        manual_text = f.read()

    system_prompt = f"""You are an ETS-certified Language Assessment Designer. Follow the TOEFL 2026 RR-25-12 spec strictly.
The Listen and Repeat task requires sentences that get progressively longer and more complex within a scenario.
Each scenario should feel like a natural, coherent situation.

MANUAL EXCERPT:
{manual_text[:15000]}
"""

    db = SessionLocal()
    total_added = 0
    total_scenarios = len(SCENARIOS)

    for idx, scenario in enumerate(SCENARIOS):
        print(f"\n{'='*60}")
        print(f"  Scenario {idx+1}/{total_scenarios}: {scenario['name']} ({scenario['setting']})")
        print(f"{'='*60}")

        if args.resume and scenario_exists_in_db(db, scenario['name']):
            print(f"  [resume] Skipping '{scenario['name']}' — already in DB.")
            continue

        prompt = build_scenario_prompt(scenario)

        try:
            # Step 1: Generate text via Gemini 1.5 Pro
            print(f"  [1/2] Generating sentences via Gemini 1.5 Pro...")
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                )
            )
            content = response.text

            match = re.search(r'\[.*\]', content, re.DOTALL)
            if not match:
                print(f"  ✗ No JSON found for scenario '{scenario['name']}'. Skipping.")
                continue

            items = json.loads(match.group(0))
            print(f"  ↪ Got {len(items)} sentences. Generating TTS audio...")

            # Step 2: Generate audio for each sentence
            voice = scenario["voice"]
            scenario_success_count = 0

            for i, item_data in enumerate(items):
                pc = item_data.get("prompt_content", {})
                sentences = pc.get("sentences", [])
                if not sentences:
                    print(f"    [{i+1}] ✗ No sentences found, skipping.")
                    continue

                sentence = sentences[0]
                text = sentence.get("text", "")
                if not text:
                    continue

                word_count = len(text.split())
                audio_filename = f"lr_{uuid.uuid4().hex[:12]}.mp3"
                audio_filepath = os.path.join(FRONTEND_AUDIO_DIR, audio_filename)

                print(f"    [{i+1}] ({voice}) {word_count:2d}w | {item_data.get('target_level','??'):3s} | \"{text[:50]}{'...' if len(text)>50 else ''}\"")
                success = generate_voice_line(voice, text, audio_filepath)

                if not success:
                    print(f"    [{i+1}] ✗ Audio generation failed. Skipping this item.")
                    continue

                sentence["audioUrl"] = f"audio/{audio_filename}"

                # Save to DB
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
                    generated_by_model="gemini-2.0-flash + Gemini 2.5 Flash TTS",
                    generation_notes=f"L&R pool. Scenario: {scenario['name']}. {word_count}w."
                )
                db.add(new_item)
                total_added += 1
                scenario_success_count += 1

            db.commit()
            print(f"  ✓ Committed {scenario_success_count} items for '{scenario['name']}'")

        except Exception as e:
            print(f"  ✗ Error processing scenario '{scenario['name']}': {e}")
            import traceback
            traceback.print_exc()
            db.rollback()

    db.close()
    print(f"\n{'='*60}")
    print(f"  DONE! Injected {total_added} Listen and Repeat items across {total_scenarios} scenarios.")
    print(f"{'='*60}")


if __name__ == "__main__":
    run()
