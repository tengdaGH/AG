#!/usr/bin/env python3
# ============================================================
# Purpose:       Generate TTS audio for remaining ETS items via Inworld API.
#                Fallback script when Gemini TTS daily quotas are exhausted.
# Usage:
#                source backend/venv/bin/activate
#                python agents/scripts/generate_ets_audio_inworld.py              # dry-run
#                python agents/scripts/generate_ets_audio_inworld.py --apply      # generate audio
#                python agents/scripts/generate_ets_audio_inworld.py --apply --type lcr
#                python agents/scripts/generate_ets_audio_inworld.py --apply --delay 2 --limit 10
# Created:       2026-02-27
# Self-Destruct: No
# ============================================================
"""
Inworld TTS fallback for ETS audio synthesis.

Voice mapping (Inworld voices — AMERICAN ACCENT ONLY for TOEFL):
  - LCR stimulus:        Brian (M) / Jessica (F) alternating by item number
  - TAKE_AN_INTERVIEW:
      • Scenario narration:  Edward (M narrator, American)
      • Per-question:        Ashley (F interviewer, American)
  - General fallback:       Brian (M), Jessica (F)

  Note: Diego was removed — Inworld describes it as "Spanish-speaking male"
  voice (wrong language). Olivia removed — "Young, British female" (wrong accent).

API: POST https://api.inworld.ai/tts/v1/voice
Model: inworld-tts-1.5-max
Output: MP3 (native), saved to frontend/public/audio/
"""
import os
import sys
import json
import re
import time
import sqlite3
import argparse
import random
import base64
import subprocess
import tempfile
import uuid as uuid_mod
from datetime import datetime, timezone, timedelta

# ─── Path Setup ─────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, ".agent/skills/toefl_voice_direction"))

from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

try:
    from log_audio import append_voice_log, set_log_path
    VOICE_LOG_AVAILABLE = True
    set_log_path(os.path.join(PROJECT_ROOT, "audio", "audio_voice_log.jsonl"))
except ImportError:
    VOICE_LOG_AVAILABLE = False
    print("[WARN] log_audio.py not importable — voice log will be skipped.")

INWORLD_KEY = os.getenv("INWORLD_KEY")
INWORLD_SECRET = os.getenv("INWORLD_SECRET")

if not INWORLD_KEY or not INWORLD_SECRET:
    print("ERROR: INWORLD_KEY/INWORLD_SECRET not set in backend/.env")
    sys.exit(1)

# ─── Audio Directories ──────────────────────────────────────────────────────
PUB_LISTENING = os.path.join(PROJECT_ROOT, "frontend/public/audio/listening")
PUB_SPEAKING  = os.path.join(PROJECT_ROOT, "frontend/public/audio/speaking")
ROOT_AUDIO    = os.path.join(PROJECT_ROOT, "audio")

for d in [PUB_LISTENING, PUB_SPEAKING, ROOT_AUDIO]:
    os.makedirs(d, exist_ok=True)

DB_PATH = os.path.join(BACKEND_DIR, "item_bank.db")

# ─── Voice Catalog (Inworld) ───────────────────────────────────────────────
# American-accent voices only (per voice direction skill § 4 Accent Override)
# Diego removed: Inworld describes it as "Spanish-speaking male" (wrong language)
# Olivia removed: "Young, British female" (wrong accent for TOEFL)

INWORLD_MALE_VOICES   = ["Brian", "Ethan", "Nate", "Carter", "Jason"]
INWORLD_FEMALE_VOICES = ["Jessica", "Lauren", "Ashley", "Sarah", "Hana"]

def lcr_voice(item_number: int) -> tuple[str, str]:
    """Return (voice, gender) for an LCR stimulus based on item number."""
    if item_number % 2 == 1:
        voice = INWORLD_MALE_VOICES[(item_number // 2) % len(INWORLD_MALE_VOICES)]
        return voice, "M"
    else:
        voice = INWORLD_FEMALE_VOICES[(item_number // 2) % len(INWORLD_FEMALE_VOICES)]
        return voice, "F"

# TAKE_AN_INTERVIEW voices
TAI_SCENARIO_VOICE    = ("Edward",  "M")   # neutral narrator
TAI_INTERVIEWER_VOICE = ("Ashley",  "F")   # warm, professional interviewer


# ─── Inworld TTS Core ──────────────────────────────────────────────────────

ENGINE_NAME = "inworld-tts-1.5-max"

def tts_inworld(text: str, voice: str, out_path: str, max_retries=3) -> bool:
    """
    Call Inworld TTS API via curl (robust against VPN proxy drops).
    Returns True on success, False on failure.
    Output is MP3.
    """
    payload = json.dumps({
        "text": text,
        "voiceId": voice,
        "modelId": ENGINE_NAME,
        "applyTextNormalization": "ON",
        "textType": "TEXT"
    })

    for attempt in range(max_retries):
        try:
            # Use curl for robust timeout handling (per minimax_vpn_workaround skill)
            auth_str = f"{INWORLD_KEY}:{INWORLD_SECRET}"
            result = subprocess.run(
                [
                    "curl", "-s", "-S", "-m", "60",
                    "-X", "POST",
                    "https://api.inworld.ai/tts/v1/voice",
                    "-H", "Content-Type: application/json",
                    "-u", auth_str,
                    "-d", payload,
                ],
                capture_output=True,
                text=True,
                timeout=90,
            )

            if result.returncode != 0:
                print(f" [curl err rc={result.returncode}]", end="", flush=True)
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                continue

            data = json.loads(result.stdout)

            if "audioContent" not in data:
                err_msg = data.get("error", {}).get("message", result.stdout[:100])
                print(f" [api err: {err_msg[:60]}]", end="", flush=True)
                if "429" in str(data) or "quota" in str(data).lower():
                    time.sleep(30 * (attempt + 1))
                    continue
                return False

            audio_bytes = base64.b64decode(data["audioContent"])

            # Save raw MP3
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(audio_bytes)

            return os.path.getsize(out_path) > 0

        except subprocess.TimeoutExpired:
            print(f" [timeout]", end="", flush=True)
            if attempt < max_retries - 1:
                time.sleep(10)
        except json.JSONDecodeError:
            print(f" [json err]", end="", flush=True)
            return False
        except Exception as e:
            print(f" [err: {str(e)[:60]}]", end="", flush=True)
            return False

    return False


# ─── Text Extraction (reused from generate_ets_audio.py) ────────────────

def extract_lcr_stimulus(pc: dict) -> str:
    """Extract just the spoken stimulus for LCR (strip item number prefix)."""
    text_data = pc.get("text")
    if text_data:
        if isinstance(text_data, dict):
            raw = text_data.get("text", "")
        else:
            raw = str(text_data)
    else:
        dialogue = pc.get("dialogue", [])
        raw = dialogue[0] if dialogue else ""
    raw = re.sub(r"^\d+\.\s*", "", raw)
    return raw.strip()


# ─── DB helpers ──────────────────────────────────────────────────────────────

def get_missing_items(conn, task_types):
    cur = conn.cursor()
    placeholders = ",".join(["?"] * len(task_types))
    cur.execute(
        f"SELECT id, task_type, prompt_content FROM test_items "
        f"WHERE (media_url IS NULL OR media_url='') AND task_type IN ({placeholders}) "
        f"ORDER BY task_type, id",
        task_types
    )
    return cur.fetchall()


def update_media_url(conn, item_id, media_url):
    cur = conn.cursor()
    cur.execute(
        "UPDATE test_items SET media_url=?, updated_at=? WHERE id=?",
        (media_url, datetime.now().isoformat(), item_id)
    )
    conn.commit()


# ─── Per-Type Processing ──────────────────────────────────────────────────

def process_lcr(conn, row, delay, apply_mode):
    item_id = row["id"]
    pc = json.loads(row["prompt_content"])

    stimulus = extract_lcr_stimulus(pc)
    if not stimulus or len(stimulus) < 5:
        print(f"  [SKIP] {item_id}: empty stimulus")
        return False

    raw_text = pc.get("text", {})
    raw_full = raw_text.get("text", "") if isinstance(raw_text, dict) else str(raw_text)
    m = re.match(r"^(\d+)\.", raw_full.strip())
    item_num = int(m.group(1)) if m else 1

    voice, gender = lcr_voice(item_num)

    ext_id = pc.get("id", item_id)
    filename = f"LCR-{ext_id.replace('/', '-')}.mp3"
    out_path = os.path.join(PUB_LISTENING, filename)
    audio_url = f"audio/listening/{filename}"

    print(f"  LCR {ext_id:25s} | {voice:10s}({gender}) | {stimulus[:55]}...", end="", flush=True)

    if not apply_mode:
        print()
        return True

    ok = tts_inworld(stimulus, voice, out_path)
    if ok:
        update_media_url(conn, item_id, audio_url)
        pc["audio_url"] = audio_url
        conn.cursor().execute("UPDATE test_items SET prompt_content=? WHERE id=?",
                              (json.dumps(pc, ensure_ascii=False), item_id))
        conn.commit()
        if VOICE_LOG_AVAILABLE:
            append_voice_log(
                item_id=item_id, task_type="LISTEN_CHOOSE_RESPONSE",
                audio_file=audio_url, engine=ENGINE_NAME,
                mode="single",
                speakers=[{"role": "Speaker", "gender": gender, "voice": voice}],
                tts_prompt_preview=stimulus[:200]
            )
        print(" ✓")
    else:
        print(" ✗")
    return ok


def process_interview(conn, row, delay, apply_mode):
    item_id = row["id"]
    pc = json.loads(row["prompt_content"])

    topic = pc.get("topic", "Interview")
    scenario = pc.get("scenario", "")
    questions = pc.get("questions", [])

    if not questions:
        print(f"  [SKIP] {item_id}: no questions")
        return False

    ext_id = pc.get("id", item_id)
    print(f"  TAI  {ext_id:25s} | {topic[:30]} ({len(questions)}q)", flush=True)

    if not apply_mode:
        return True

    changed = False

    # 1. Scenario narration
    if scenario:
        fn = f"{item_id}_scenario.mp3"
        out = os.path.join(PUB_SPEAKING, fn)
        url = f"audio/speaking/{fn}"
        v, g = TAI_SCENARIO_VOICE
        print(f"    → Scenario [{v}]...", end="", flush=True)
        ok = tts_inworld(scenario, v, out)
        if ok:
            pc["scenario_audio_url"] = url
            changed = True
            print(" ✓")
            if VOICE_LOG_AVAILABLE:
                append_voice_log(item_id=f"{item_id}_scenario", task_type="TAKE_AN_INTERVIEW",
                                 audio_file=url, engine=ENGINE_NAME,
                                 mode="single",
                                 speakers=[{"role": "Narrator", "gender": g, "voice": v}],
                                 tts_prompt_preview=scenario[:200])
            time.sleep(delay + random.uniform(-0.5, 0.5))
        else:
            print(" ✗")

    # 2. Per-question audio
    v_int, g_int = TAI_INTERVIEWER_VOICE

    for i, q in enumerate(questions):
        q_text = q.get("text", "").strip()
        if not q_text:
            continue
        fn = f"{item_id}_q{i}.mp3"
        out = os.path.join(PUB_SPEAKING, fn)
        url = f"audio/speaking/{fn}"
        print(f"    → Q{i+1} [{v_int}]...", end="", flush=True)
        ok = tts_inworld(q_text, v_int, out)
        if ok:
            questions[i]["audio_url"] = url
            changed = True
            print(" ✓")
            if VOICE_LOG_AVAILABLE:
                append_voice_log(item_id=f"{item_id}_q{i}", task_type="TAKE_AN_INTERVIEW",
                                 audio_file=url, engine=ENGINE_NAME,
                                 mode="single",
                                 speakers=[{"role": "Interviewer", "gender": g_int, "voice": v_int}],
                                 tts_prompt_preview=q_text[:200])
            if i < len(questions) - 1:
                time.sleep(delay + random.uniform(-0.5, 0.5))
        else:
            print(" ✗")

    if changed:
        first_q_url = questions[0].get("audio_url", "") if questions else ""
        pc["questions"] = questions
        cur = conn.cursor()
        cur.execute("UPDATE test_items SET prompt_content=?, media_url=?, updated_at=? WHERE id=?",
                    (json.dumps(pc, ensure_ascii=False), first_q_url, datetime.now().isoformat(), item_id))
        conn.commit()
        return True
    return False


# ─── Main ──────────────────────────────────────────────────────────────────

TYPE_CHOICES = {
    "lcr":       "LISTEN_CHOOSE_RESPONSE",
    "interview": "TAKE_AN_INTERVIEW",
    "all":       None,
}

def main():
    parser = argparse.ArgumentParser(description="Generate TTS audio via Inworld API for remaining ETS items.")
    parser.add_argument("--apply", action="store_true", help="Apply (default: dry-run)")
    parser.add_argument("--type", choices=list(TYPE_CHOICES.keys()), default="all")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between TTS calls (default: 2)")
    parser.add_argument("--limit", type=int, default=0, help="Max items to process (0 = all)")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if args.type == "all":
        task_types = ["LISTEN_CHOOSE_RESPONSE", "TAKE_AN_INTERVIEW"]
    else:
        task_types = [TYPE_CHOICES[args.type]]

    rows = get_missing_items(conn, task_types)
    if args.limit:
        rows = rows[:args.limit]

    print(f"\n{'='*65}")
    print(f"  ETS AUDIO SYNTHESIS (INWORLD) — {'APPLY' if args.apply else 'DRY RUN'}")
    print(f"{'='*65}")
    print(f"  Engine:  {ENGINE_NAME}")
    print(f"  Items:   {len(rows)}")
    print(f"  Delay:   {args.delay}s between calls")
    print()

    from collections import Counter
    counts = Counter(r["task_type"] for r in rows)
    for tt, n in counts.most_common():
        print(f"  {tt}: {n}")
    print()

    success = failed = 0

    for idx, row in enumerate(rows):
        tt = row["task_type"]
        try:
            if tt == "LISTEN_CHOOSE_RESPONSE":
                ok = process_lcr(conn, row, args.delay, args.apply)
            elif tt == "TAKE_AN_INTERVIEW":
                ok = process_interview(conn, row, args.delay, args.apply)
            else:
                print(f"  [SKIP] Unknown task_type: {tt}")
                ok = False
        except KeyboardInterrupt:
            print("\n[Interrupted by user]")
            break
        except Exception as e:
            print(f"\n  [ERROR] {row['id']}: {e}")
            ok = False

        if ok:
            success += 1
        else:
            failed += 1

        if args.apply and idx < len(rows) - 1:
            actual_delay = args.delay + random.uniform(-0.5, 1)
            time.sleep(max(0.5, actual_delay))

    conn.close()

    print(f"\n{'='*65}")
    print(f"  Done!")
    print(f"  Success: {success}  |  Failed/Skipped: {failed}  |  Total: {len(rows)}")
    if not args.apply:
        print(f"\n  [DRY RUN] Pass --apply to generate audio.")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()
