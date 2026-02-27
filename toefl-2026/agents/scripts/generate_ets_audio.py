#!/usr/bin/env python3
# ============================================================
# Purpose:       Generate TTS audio for all 205 ETS items missing audio in the TOEFL 2026 item bank.
#                Covers LISTEN_CHOOSE_RESPONSE, LISTEN_CONVERSATION, TAKE_AN_INTERVIEW, LISTEN_AND_REPEAT.
#                Applies toefl_voice_direction skill for proper voice casting.
# Usage:         cd toefl-2026
#                source backend/venv/bin/activate
#                python agents/scripts/generate_ets_audio.py              # dry-run
#                python agents/scripts/generate_ets_audio.py --apply      # generate audio
#                python agents/scripts/generate_ets_audio.py --apply --type lcr
#                python agents/scripts/generate_ets_audio.py --apply --delay 12 --limit 20
# Created:       2026-02-26
# Self-Destruct: No
# ============================================================
"""
Comprehensive ETS audio synthesis for all missing-audio TOEFL 2026 items.

Voice casting follows the toefl_voice_direction skill:
  - LCR stimulus:          Single-speaker, alternating Fenrir(M)/Kore(F) by turn number
  - LISTEN_CONVERSATION:   Multi-speaker, Woman→Kore, Man→Puck
  - TAKE_AN_INTERVIEW:
      • Scenario narration: Fenrir (M narrator)
      • Per-question:       Callirrhoe (F interviewer, first default)
  - LISTEN_AND_REPEAT:     Fenrir (M) or Aoede (F) for clear pedagogy

Tone prefixes applied per toefl_voice_direction Section 6.
Rate limiting: 10s between calls. Exponential backoff on 429.

Audio output: frontend/public/audio/{listening,speaking,interview}/
DB update:    media_url set on test_items row.
Voice log:    audio/audio_voice_log.jsonl via log_audio.py
"""
import os
import sys
import json
import re
import time
import wave
import uuid
import shutil
import sqlite3
import argparse
import random
from datetime import datetime

# ─── Path Setup ─────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, ".agent/skills/toefl_voice_direction"))

from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

from google import genai
from google.genai import types

try:
    from log_audio import append_voice_log, set_log_path
    VOICE_LOG_AVAILABLE = True
    set_log_path(os.path.join(PROJECT_ROOT, "audio", "audio_voice_log.jsonl"))
except ImportError:
    VOICE_LOG_AVAILABLE = False
    print("[WARN] log_audio.py not importable — voice log will be skipped.")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY not set in backend/.env")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

# ─── Audio Directories ──────────────────────────────────────────────────────
PUB_LISTENING   = os.path.join(PROJECT_ROOT, "frontend/public/audio/listening")
PUB_SPEAKING    = os.path.join(PROJECT_ROOT, "frontend/public/audio/speaking")
PUB_INTERVIEW   = os.path.join(PROJECT_ROOT, "frontend/public/audio/interview")
ROOT_AUDIO      = os.path.join(PROJECT_ROOT, "audio")

for d in [PUB_LISTENING, PUB_SPEAKING, PUB_INTERVIEW, ROOT_AUDIO]:
    os.makedirs(d, exist_ok=True)

DB_PATH = os.path.join(BACKEND_DIR, "toefl_2026.db")

# ─── Voice Catalog (per toefl_voice_direction skill) ────────────────────────

# LCR: alternate voice by item number parity
def lcr_voice(item_number: int) -> tuple[str, str]:
    """Return (voice, gender) for an LCR stimulus based on item number."""
    # Odd numbers → Male (Puck), even → Female (Kore)
    # For variety, rotate through a small pool
    male_voices   = ["Puck", "Achird", "Fenrir"]
    female_voices = ["Kore", "Leda",   "Sulafat"]
    if item_number % 2 == 1:
        voice = male_voices[(item_number // 2) % len(male_voices)]
        return voice, "M"
    else:
        voice = female_voices[(item_number // 2) % len(female_voices)]
        return voice, "F"

# Conversation speaker mapping (Woman/Man labels from ETS transcripts)
CONV_SPEAKER_MAP = {
    "Woman": ("Kore",    "F"),
    "Man":   ("Puck",    "M"),
    "F":     ("Kore",    "F"),
    "M":     ("Puck",    "M"),
    "F1":    ("Kore",    "F"),
    "F2":    ("Aoede",   "F"),
    "M1":    ("Puck",    "M"),
    "M2":    ("Achird",  "M"),
}

# TAKE_AN_INTERVIEW voices
TAI_SCENARIO_VOICE     = ("Fenrir",      "M")   # neutral narrator
TAI_INTERVIEWER_VOICE  = ("Callirrhoe",  "F")   # warm, professional interviewer

# LISTEN_AND_REPEAT voices
LAR_VOICES = [("Fenrir", "M"), ("Aoede", "F")]

# ─── Tone Direction Strings (Section 6) ─────────────────────────────────────
TONE = {
    "LISTEN_CHOOSE_RESPONSE": "Neutral, natural conversational stimulus. Short, clear, single utterance. Sound like an ordinary person in a casual exchange.",
    "LISTEN_CONVERSATION":    "Natural, conversational tone. Each speaker should sound like a real person talking, not reading. Match the emotion implied by the dialogue.",
    "TAKE_AN_INTERVIEW_NAR":  "Neutral, clear narration. This is a scene-setting voice. Professional, unhurried.",
    "TAKE_AN_INTERVIEW_INT":  "Professional, warm, and genuinely curious. Conversational but polished, like a TV journalist.",
    "LISTEN_AND_REPEAT":      "Clear, pedagogical delivery. Speak each word cleanly and at a slightly measured pace — this audio is used for language learning repetition practice.",
}

# ─── Utility ─────────────────────────────────────────────────────────────────

def save_wav(path, pcm_data):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm_data)


def pcm_to_mp3(pcm_data, out_mp3):
    pcm_tmp = out_mp3.replace(".mp3", "_tmp.pcm")
    with open(pcm_tmp, "wb") as f:
        f.write(pcm_data)
    ret = os.system(f"ffmpeg -y -f s16le -ar 24000 -ac 1 -i '{pcm_tmp}' '{out_mp3}' > /dev/null 2>&1")
    if os.path.exists(pcm_tmp):
        os.remove(pcm_tmp)
    return ret == 0 and os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 0


# ─── TTS Model Rotation ────────────────────────────────────────────────────────
# Alternate flash / pro to spread load across two independent daily quotas.
# When one quota is exhausted, fall back to the other permanently.

TTS_MODELS = [
    "gemini-2.5-flash-preview-tts",
    "gemini-2.5-pro-preview-tts",
]
_model_exhausted = set()   # tracks which models have hit their daily quota
_model_index = 0           # round-robin cursor

def _next_model() -> str:
    """Return the next available TTS model, rotating between flash and pro."""
    global _model_index
    available = [m for m in TTS_MODELS if m not in _model_exhausted]
    if not available:
        print("\n[FATAL] All TTS model quotas exhausted for today.", flush=True)
        sys.exit(1)
    model = available[_model_index % len(available)]
    _model_index += 1
    return model

def _mark_exhausted(model: str):
    """Mark a model's daily quota as exhausted and log the fallback."""
    _model_exhausted.add(model)
    available = [m for m in TTS_MODELS if m not in _model_exhausted]
    if available:
        print(f"\n[QUOTA] {model} daily quota exhausted → switching to {available[0]}", flush=True)
    else:
        print(f"\n[FATAL] All TTS model quotas exhausted for today.", flush=True)
        sys.exit(1)


# ─── TTS Core ────────────────────────────────────────────────────────────────

def tts_single(text: str, voice: str, tone: str, out_path: str, max_retries=5) -> tuple[bool, str]:
    """Single-speaker TTS. Rotates between flash and pro models. Returns (success, engine)."""
    prompt = f"{tone}\n\nGenerate audio from this precise transcript without adding or modifying anything:\n{text}"
    use_mp3 = out_path.endswith(".mp3")

    last_engine = ""
    for attempt in range(max_retries):
        model = _next_model()
        last_engine = model
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                        )
                    )
                )
            )
            for part in resp.candidates[0].content.parts:
                if getattr(part, "inline_data", None) and getattr(part.inline_data, "data", None):
                    pcm = part.inline_data.data
                    if use_mp3:
                        return pcm_to_mp3(pcm, out_path), model
                    else:
                        save_wav(out_path, pcm)
                        return True, model
            return False, model
        except Exception as e:
            err = str(e)
            if "exceeded your current quota" in err or ("429" in err and "daily" in err.lower()):
                _mark_exhausted(model)
                # retry immediately with the other model
                continue
            elif "429" in err or "RESOURCE_EXHAUSTED" in err:
                wait = 30 * (2 ** attempt)
                print(f" [429 backoff {wait}s]", end="", flush=True)
                time.sleep(wait)
            elif "500" in err:
                time.sleep(30)
            else:
                print(f" [err: {err[:80]}]", end="", flush=True)
                return False, model

    return False, last_engine


def tts_multi(script_lines: list[tuple[str,str]], speaker_voices: dict[str,str],
              tone: str, out_path: str, max_retries=5) -> tuple[bool, str]:
    """Multi-speaker TTS (max 2 speakers). Rotates between flash and pro models. Returns (success, engine)."""
    formatted = "\n".join(f"{spk}: {txt}" for spk, txt in script_lines)
    prompt = f"{tone}\n\nGenerate audio from this precise transcript without adding or modifying anything:\n\n{formatted}"

    configs = [
        types.SpeakerVoiceConfig(
            speaker=name,
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=v)
            )
        )
        for name, v in speaker_voices.items()
    ]

    last_engine = ""
    for attempt in range(max_retries):
        model = _next_model()
        last_engine = model
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                            speaker_voice_configs=configs
                        )
                    )
                )
            )
            pcm = resp.candidates[0].content.parts[0].inline_data.data
            save_wav(out_path, pcm)
            return True, model
        except Exception as e:
            err = str(e)
            if "exceeded your current quota" in err or ("429" in err and "daily" in err.lower()):
                _mark_exhausted(model)
                continue
            elif "429" in err or "RESOURCE_EXHAUSTED" in err:
                wait = 30 * (2 ** attempt)
                print(f" [429 backoff {wait}s]", end="", flush=True)
                time.sleep(wait)
            elif "500" in err:
                time.sleep(30)
            else:
                print(f" [err: {err[:80]}]", end="", flush=True)
                return False, model

    return False, last_engine


# ─── Text Extraction ─────────────────────────────────────────────────────────

def parse_conversation_lines(transcript: str) -> list[tuple[str,str]]:
    """Parse ETS transcript into (speaker, text) tuples."""
    lines = transcript.strip().split("\n")
    result = []
    current_spk = None
    current_txt = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip header "Listen to a ..." lines
        if re.match(r'^Listen to (a|an|the)\b', line, re.IGNORECASE):
            continue

        # Format: (M-Can) or (W-Br) etc — extract gender prefix
        m = re.match(r'^\(([MW])[^)]*\)\s*(.*)', line)
        if m:
            gender_code = "Man" if m.group(1) == "M" else "Woman"
            txt = m.group(2).strip()
            if current_spk and current_txt:
                result.append((current_spk, " ".join(current_txt)))
            current_spk = gender_code
            current_txt = [txt] if txt else []
            continue

        # Format: "Woman:", "Man:", "Professor:", "Announcer:", "Podcast Host:", etc.
        m = re.match(r'^([A-Z][A-Za-z\s]+?):\s*(.*)', line)
        if m:
            spk_raw = m.group(1).strip()
            txt = m.group(2).strip()
            # Normalize to canonical speakers
            if spk_raw in ("Woman", "F"):
                spk = "Woman"
            elif spk_raw in ("Man", "M"):
                spk = "Man"
            else:
                spk = spk_raw
            if current_spk and current_txt:
                result.append((current_spk, " ".join(current_txt)))
            current_spk = spk
            current_txt = [txt] if txt else []
            continue

        # Continuation line
        if current_spk:
            current_txt.append(line)

    if current_spk and current_txt:
        result.append((current_spk, " ".join(current_txt)))

    return result


def is_single_speaker_conv(script_lines: list[tuple[str,str]]) -> tuple[bool, str]:
    """Returns (True, speaker_name) if all lines belong to a single speaker."""
    speakers = set(spk for spk, _ in script_lines)
    if len(speakers) == 1:
        return True, list(speakers)[0]
    return False, ""


def get_conv_voice_map(speaker: str) -> tuple[str, str]:
    """Get voice + gender for a named speaker."""
    if speaker in CONV_SPEAKER_MAP:
        return CONV_SPEAKER_MAP[speaker]
    # Professor-type: use Charon (M)
    if any(k in speaker for k in ("Professor", "Teacher", "Instructor")):
        return "Charon", "M"
    # Announcer/Host-type: use Aoede (F)
    if any(k in speaker for k in ("Announcer", "Host", "Narrator", "Trainer")):
        return "Aoede", "F"
    # Default: alternate by hash
    return ("Fenrir", "M") if hash(speaker) % 2 == 0 else ("Kore", "F")



def extract_lcr_stimulus(pc: dict) -> str:
    """Extract just the spoken stimulus for LCR (strip item number prefix)."""
    text_data = pc.get("text", {})
    if isinstance(text_data, dict):
        raw = text_data.get("text", "")
    else:
        raw = str(text_data)
    # Strip leading "N. " item number
    raw = re.sub(r"^\d+\.\s*", "", raw)
    # Strip leading speaker label e.g. "Woman: " or "Man: "
    # Keep label for context — TTS handles it naturally
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


# ─── Per-Type Processing ──────────────────────────────────────────────────────

def process_lcr(conn, row, delay, apply_mode):
    item_id = row["id"]
    pc = json.loads(row["prompt_content"])

    stimulus = extract_lcr_stimulus(pc)
    if not stimulus or len(stimulus) < 5:
        print(f"  [SKIP] {item_id}: empty stimulus")
        return False

    # Parse item number from text for voice alternation
    raw_text = pc.get("text", {})
    raw_full = raw_text.get("text", "") if isinstance(raw_text, dict) else str(raw_text)
    m = re.match(r"^(\d+)\.", raw_full.strip())
    item_num = int(m.group(1)) if m else 1

    voice, gender = lcr_voice(item_num)
    tone = TONE["LISTEN_CHOOSE_RESPONSE"]

    ext_id = pc.get("id", item_id)
    filename = f"LCR-{ext_id.replace('/', '-')}.wav"
    out_path = os.path.join(PUB_LISTENING, filename)
    audio_url = f"audio/listening/{filename}"

    print(f"  LCR {ext_id:25s} | {voice:12s}({gender}) | {stimulus[:55]}...", end="", flush=True)

    if not apply_mode:
        print()
        return True

    ok, engine = tts_single(stimulus, voice, tone, out_path)
    if ok:
        update_media_url(conn, item_id, audio_url)
        # Also write audio_url into prompt_content
        pc["audio_url"] = audio_url
        conn.cursor().execute("UPDATE test_items SET prompt_content=? WHERE id=?",
                              (json.dumps(pc, ensure_ascii=False), item_id))
        conn.commit()
        if VOICE_LOG_AVAILABLE:
            append_voice_log(
                item_id=item_id, task_type="LISTEN_CHOOSE_RESPONSE",
                audio_file=audio_url, engine=engine,
                mode="single",
                speakers=[{"role": "Speaker", "gender": gender, "voice": voice,
                           "tone_instruction": tone}],
                tts_prompt_preview=f"{tone[:80]}\n{stimulus[:200]}"
            )
        print(" ✓")
    else:
        print(" ✗")
    return ok


def process_conversation(conn, row, delay, apply_mode):
    item_id = row["id"]
    pc = json.loads(row["prompt_content"])

    transcript = pc.get("transcript", "") or pc.get("text", "")
    if not transcript or len(transcript) < 30:
        print(f"  [SKIP] {item_id}: empty transcript")
        return False

    script_lines = parse_conversation_lines(transcript)
    if not script_lines:
        print(f"  [SKIP] {item_id}: no parseable lines")
        return False

    ext_id = pc.get("id", item_id)
    tone = TONE["LISTEN_CONVERSATION"]

    # Check if single-speaker (talk/announcement) or multi-speaker (conversation)
    mono, mono_speaker = is_single_speaker_conv(script_lines)

    if mono:
        # Use single-speaker TTS
        v, g = get_conv_voice_map(mono_speaker)
        # Single-speaker: determine appropriate tone
        if "Professor" in mono_speaker or "Instructor" in mono_speaker or "Teacher" in mono_speaker:
            tone_used = "Deliver in a measured, authoritative academic lecture tone. Speak clearly with natural academic pacing."
        elif "Announcer" in mono_speaker or "Host" in mono_speaker:
            tone_used = "Friendly, clear campus broadcast voice. Upbeat but professional. Moderate pace, warm energy."
        else:
            tone_used = tone
        full_text = "\n".join(f"{spk}: {txt}" for spk, txt in script_lines)
        filename = f"LC-{ext_id.replace('/', '-')}.wav"
        out_path = os.path.join(PUB_LISTENING, filename)
        audio_url = f"audio/listening/{filename}"
        preview = transcript[:50].replace("\n", " ")
        print(f"  CONV {ext_id:25s} | {v}({g}) MONO | {preview}...", end="", flush=True)

        if not apply_mode:
            print()
            return True
        ok, engine = tts_single(full_text, v, tone_used, out_path)
    else:
        # Multi-speaker
        # Build speaker→voice map (max 2)
        unique_spks = list(dict.fromkeys(spk for spk, _ in script_lines))
        speaker_voices = {}
        for spk in unique_spks[:2]:
            v, _ = get_conv_voice_map(spk)
            speaker_voices[spk] = v
        filename = f"LC-{ext_id.replace('/', '-')}.wav"
        out_path = os.path.join(PUB_LISTENING, filename)
        audio_url = f"audio/listening/{filename}"
        spk_labels = "/".join(f"{s}→{v}" for s, v in speaker_voices.items())
        preview = transcript[:50].replace("\n", " ")
        print(f"  CONV {ext_id:25s} | {spk_labels} | {preview}...", end="", flush=True)

        if not apply_mode:
            print()
            return True
        ok, engine = tts_multi(script_lines, speaker_voices, tone, out_path)

    if ok:
        update_media_url(conn, item_id, audio_url)
        pc["audio_url"] = audio_url
        conn.cursor().execute("UPDATE test_items SET prompt_content=? WHERE id=?",
                              (json.dumps(pc, ensure_ascii=False), item_id))
        conn.commit()
        if VOICE_LOG_AVAILABLE:
            speakers_log = ([{"role": spk, "voice": v, "tone_instruction": tone}
                              for spk, v in speaker_voices.items()]
                             if not mono else
                             [{"role": mono_speaker, "voice": v, "gender": g, "tone_instruction": tone_used}])
            append_voice_log(
                item_id=item_id, task_type="LISTEN_CONVERSATION",
                audio_file=audio_url, engine=engine,
                mode="single" if mono else "multi",
                speakers=speakers_log,
                tts_prompt_preview=f"{tone[:80]}\n{preview}"
            )
        print(" ✓")
        shutil.copy2(out_path, os.path.join(ROOT_AUDIO, filename))
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
        fn = f"{item_id}_scenario.wav"
        out = os.path.join(PUB_SPEAKING, fn)
        url = f"audio/speaking/{fn}"
        v, g = TAI_SCENARIO_VOICE
        tone = TONE["TAKE_AN_INTERVIEW_NAR"]
        print(f"    → Scenario [{v}]...", end="", flush=True)
        ok, engine = tts_single(scenario, v, tone, out)
        if ok:
            pc["scenario_audio_url"] = url
            changed = True
            print(" ✓")
            if VOICE_LOG_AVAILABLE:
                append_voice_log(item_id=f"{item_id}_scenario", task_type="TAKE_AN_INTERVIEW",
                                 audio_file=url, engine=engine,
                                 mode="single",
                                 speakers=[{"role": "Narrator", "gender": g, "voice": v,
                                            "tone_instruction": tone}],
                                 tts_prompt_preview=f"{tone[:80]}\n{scenario[:200]}")
            time.sleep(delay + random.uniform(-1, 1))
        else:
            print(" ✗")

    # 2. Per-question audio
    v_int, g_int = TAI_INTERVIEWER_VOICE
    tone_int = TONE["TAKE_AN_INTERVIEW_INT"]

    for i, q in enumerate(questions):
        q_text = q.get("text", "").strip()
        if not q_text:
            continue
        fn = f"{item_id}_q{i}.wav"
        out = os.path.join(PUB_SPEAKING, fn)
        url = f"audio/speaking/{fn}"
        print(f"    → Q{i+1} [{v_int}]...", end="", flush=True)
        ok, engine = tts_single(q_text, v_int, tone_int, out)
        if ok:
            questions[i]["audio_url"] = url
            changed = True
            print(" ✓")
            if VOICE_LOG_AVAILABLE:
                append_voice_log(item_id=f"{item_id}_q{i}", task_type="TAKE_AN_INTERVIEW",
                                 audio_file=url, engine=engine,
                                 mode="single",
                                 speakers=[{"role": "Interviewer", "gender": g_int, "voice": v_int,
                                            "tone_instruction": tone_int}],
                                 tts_prompt_preview=f"{tone_int[:80]}\n{q_text[:200]}")
            if i < len(questions) - 1:
                time.sleep(delay + random.uniform(-1, 1))
        else:
            print(" ✗")

    if changed:
        # Set top-level media_url to first question's audio_url (for admin preview)
        first_q_url = questions[0].get("audio_url", "") if questions else ""
        pc["questions"] = questions
        cur = conn.cursor()
        cur.execute("UPDATE test_items SET prompt_content=?, media_url=?, updated_at=? WHERE id=?",
                    (json.dumps(pc, ensure_ascii=False), first_q_url, datetime.now().isoformat(), item_id))
        conn.commit()
        return True
    return False


def clean_ocr_text(text: str) -> str:
    """Fix PDF OCR artifacts: mid-word line breaks, stray newlines, duplicate spaces."""
    # Fix mid-word line breaks: `t\nhe` → `the`, only when prev char is lowercase and next is lowercase
    text = re.sub(r'([a-z])\n([a-z])', r'\1\2', text)
    # Collapse stray `\n` within a sentence (not speaker-label lines)
    # Remove trailing "Speaking Section" or "Listening Section" footers
    text = re.sub(r'\n?Speaking Section\s*$', '', text.strip())
    text = re.sub(r'\n?Listening Section\s*$', '', text.strip())
    # Normalize multiple spaces
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def extract_lar_trainer_text(pc: dict) -> str:
    """
    LAR items contain the full ETS instruction page as `text`.
    Extract only the `Trainer:` lines which are the actual spoken content to synthesize.
    """
    raw = pc.get("text", "")
    if not raw:
        return ""
    raw = clean_ocr_text(raw)

    # Extract all Trainer: lines
    trainer_lines = re.findall(r'Trainer:\s*(.+?)(?=\nTrainer:|$)', raw, re.DOTALL)
    if trainer_lines:
        # Clean each line and join with a natural pause spacing
        cleaned = []
        for line in trainer_lines:
            line = re.sub(r'\s+', ' ', line.strip())
            if line:
                cleaned.append(line)
        return "\n".join(cleaned)  # One trainer line per line for natural pacing

    # Fallback: check for sentence/phrase fields
    return pc.get("sentence", "") or pc.get("phrase", "") or ""


def process_listen_repeat(conn, row, idx, delay, apply_mode):
    item_id = row["id"]
    pc = json.loads(row["prompt_content"])

    text = extract_lar_trainer_text(pc)
    if not text or len(text.strip()) < 5:
        print(f"  [SKIP] {item_id}: empty/no Trainer lines found")
        return False

    voice, gender = LAR_VOICES[idx % len(LAR_VOICES)]
    tone = TONE["LISTEN_AND_REPEAT"]

    ext_id = pc.get("id", item_id)
    filename = f"LAR-{ext_id.replace('/', '-')}.wav"
    out_path = os.path.join(PUB_LISTENING, filename)
    audio_url = f"audio/listening/{filename}"

    print(f"  LAR  {ext_id:25s} | {voice:10s} | {text[:55]}...", end="", flush=True)

    if not apply_mode:
        print()
        return True

    ok, engine = tts_single(text, voice, tone, out_path)
    if ok:
        update_media_url(conn, item_id, audio_url)
        if VOICE_LOG_AVAILABLE:
            append_voice_log(item_id=item_id, task_type="LISTEN_AND_REPEAT",
                             audio_file=audio_url, engine=engine,
                             mode="single",
                             speakers=[{"role": "Speaker", "gender": gender, "voice": voice,
                                        "tone_instruction": tone}],
                             tts_prompt_preview=f"{tone[:80]}\n{text[:200]}")
        print(" ✓")
    else:
        print(" ✗")
    return ok


# ─── Main ──────────────────────────────────────────────────────────────────

TYPE_CHOICES = {
    "lcr":          "LISTEN_CHOOSE_RESPONSE",
    "conversation": "LISTEN_CONVERSATION",
    "interview":    "TAKE_AN_INTERVIEW",
    "lar":          "LISTEN_AND_REPEAT",
    "all":          None,
}


def main():
    parser = argparse.ArgumentParser(description="Generate TTS audio for ETS items missing audio.")
    parser.add_argument("--apply", action="store_true", help="Apply (default: dry-run)")
    parser.add_argument("--type", choices=list(TYPE_CHOICES.keys()), default="all")
    parser.add_argument("--delay", type=int, default=10, help="Seconds between TTS calls")
    parser.add_argument("--limit", type=int, default=0, help="Max items to process (0 = all)")
    parser.add_argument("--item_id", type=str, help="Process specific item by ID")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    all_types = ["LISTEN_CHOOSE_RESPONSE", "LISTEN_CONVERSATION", "TAKE_AN_INTERVIEW", "LISTEN_AND_REPEAT"]
    if args.type == "all":
        task_types = all_types
    else:
        task_types = [TYPE_CHOICES[args.type]]

    rows = get_missing_items(conn, task_types)
    if args.limit:
        rows = rows[: args.limit]

    print(f"\n{'='*65}")
    print(f"  ETS AUDIO SYNTHESIS — {'APPLY' if args.apply else 'DRY RUN'}")
    print(f"{'='*65}")
    print(f"  Items to process: {len(rows)}")
    print(f"  Delay: {args.delay}s between calls")
    print()

    from collections import Counter
    counts = Counter(r["task_type"] for r in rows)
    for tt, n in counts.most_common():
        print(f"  {tt}: {n}")
    print()

    success = failed = 0
    lar_idx = 0

    for idx, row in enumerate(rows):
        tt = row["task_type"]
        try:
            if tt == "LISTEN_CHOOSE_RESPONSE":
                ok = process_lcr(conn, row, args.delay, args.apply)
            elif tt == "LISTEN_CONVERSATION":
                ok = process_conversation(conn, row, args.delay, args.apply)
            elif tt == "TAKE_AN_INTERVIEW":
                ok = process_interview(conn, row, args.delay, args.apply)
            elif tt == "LISTEN_AND_REPEAT":
                ok = process_listen_repeat(conn, row, lar_idx, args.delay, args.apply)
                lar_idx += 1
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
            # Add small random jitter to the delay to prevent burst triggers
            actual_delay = args.delay + random.uniform(-1, 2)
            time.sleep(max(1, actual_delay))

    conn.close()

    print(f"\n{'='*65}")
    print(f"  Done!")
    print(f"  Success: {success}  |  Failed/Skipped: {failed}  |  Total: {len(rows)}")
    if not args.apply:
        print(f"\n  [DRY RUN] Pass --apply to generate audio.")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()
