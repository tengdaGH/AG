# ============================================================
# Purpose:       Unified audio recovery: find all listening items missing TTS audio, generate transcripts if needed, and produce MP3/WAV files.
# Usage:         python agents/scripts/recover_listening_audio.py [--apply] [--type lcr|conversation|announcement|talk|all] [--delay N]
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
Unified Audio Recovery for Listening Items.

Finds ALL listening items missing audio (both PENDING_TTS and stale URLs),
generates transcripts for items that need them, then produces TTS audio
using the correct mode:
  - Single-speaker for LCR, Announcement, Academic Talk
  - Multi-speaker for Conversation

Usage:
    cd toefl-2026
    source backend/venv/bin/activate
    python agents/scripts/recover_listening_audio.py              # dry-run (default)
    python agents/scripts/recover_listening_audio.py --apply      # generate audio
    python agents/scripts/recover_listening_audio.py --apply --type conversation
    python agents/scripts/recover_listening_audio.py --apply --delay 8

Rate Limits:
    - Default 10s delay between TTS calls (max ~6 RPM)
    - Exponential backoff on 429: 60s, 120s, 240s, ...
    - Safe to re-run: skips items that already have working audio files
"""
import os, sys, json, uuid, re, time, wave, argparse
from dotenv import load_dotenv
from google import genai
from google.genai import types

os.environ['PYTHONUNBUFFERED'] = '1'

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

# Audio output directory (Next.js public)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
AUDIO_DIR = os.path.join(PROJECT_ROOT, 'frontend', 'public', 'audio', 'listening')
os.makedirs(AUDIO_DIR, exist_ok=True)

# Also ensure the root audio/listening symlink/copy works
ROOT_AUDIO_DIR = os.path.join(PROJECT_ROOT, 'audio', 'listening')
os.makedirs(ROOT_AUDIO_DIR, exist_ok=True)

# ─── Voice Configuration ────────────────────────────────────────────────────

SINGLE_VOICES = ["Aoede", "Puck", "Kore", "Charon", "Fenrir"]

# Multi-speaker voice mapping for conversations
SPEAKER_VOICES = {
    "F": "Kore",      # Female speaker → clear, friendly
    "M": "Puck",      # Male speaker → bright, youthful
    "F1": "Kore",
    "F2": "Aoede",
    "M1": "Puck",
    "M2": "Charon",
    "Speaker 1": "Kore",
    "Speaker 2": "Puck",
    "Student": "Puck",
    "Administrator": "Aoede",
    "Professor": "Charon",
}

TASK_TYPE_MAP = {
    'lcr': TaskType.LISTEN_CHOOSE_RESPONSE,
    'conversation': TaskType.LISTEN_CONVERSATION,
    'announcement': TaskType.LISTEN_ANNOUNCEMENT,
    'talk': TaskType.LISTEN_ACADEMIC_TALK,
}


# ─── Utility ────────────────────────────────────────────────────────────────

def save_wav(filename, pcm_data, channels=1, rate=24000, sample_width=2):
    """Save raw PCM audio as .wav file."""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


def audio_file_exists(audio_url):
    """Check if an audio file actually exists on disk."""
    if not audio_url or audio_url == 'PENDING_TTS':
        return False
    pub_path = os.path.join(PROJECT_ROOT, 'frontend', 'public', audio_url)
    root_path = os.path.join(PROJECT_ROOT, audio_url)
    return os.path.exists(pub_path) or os.path.exists(root_path)


# ─── Text Extraction ────────────────────────────────────────────────────────

def extract_tts_text(data, task_type):
    """Extract the transcript text for TTS generation."""
    if task_type == TaskType.LISTEN_CHOOSE_RESPONSE:
        # LCR: speak only the first dialogue line (the audio stimulus)
        dialogue = data.get("dialogue", [])
        if dialogue:
            return dialogue[0]
        return data.get("text", "")

    elif task_type == TaskType.LISTEN_CONVERSATION:
        # Conversation: full multi-turn dialogue
        return data.get("text", "") or data.get("transcript", "")

    elif task_type in (TaskType.LISTEN_ANNOUNCEMENT, TaskType.LISTEN_ACADEMIC_TALK):
        text = data.get("text", "")
        # Skip items where text == context (audio-only legacy items)
        context = data.get("context", "")
        if text.strip() == context.strip() or len(text.split()) < 10:
            return ""  # No transcript available
        return text

    return ""


def detect_speakers(text):
    """Detect speaker labels in conversation text and return mapping."""
    speakers = {}

    # Pattern: (F) or (M) or F: or M:
    for match in re.finditer(r'(?:^|\n)\s*(?:\(([FM]\d?)\)|([FM]\d?):|\*\*(\w+(?:\s+\w+)?)\*\*)', text):
        label = match.group(1) or match.group(2) or match.group(3)
        if label and label not in speakers:
            speakers[label] = SPEAKER_VOICES.get(label, SINGLE_VOICES[len(speakers) % len(SINGLE_VOICES)])

    return speakers if speakers else {"Narrator": "Aoede"}


def normalize_conversation_text(text):
    """Normalize conversation text to use 'SpeakerName: Dialogue' format for multi-speaker TTS."""
    lines = text.strip().split('\n')
    normalized = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Handle (F) ... or (M) ... format
        m = re.match(r'\(([FM]\d?)\)\s*(.*)', line)
        if m:
            normalized.append(f"{m.group(1)}: {m.group(2)}")
            continue

        # Handle F: ... or M: ... format
        m = re.match(r'([FM]\d?):\s*(.*)', line)
        if m:
            normalized.append(f"{m.group(1)}: {m.group(2)}")
            continue

        # Handle **SpeakerName:** ... format
        m = re.match(r'\*\*(\w+(?:\s+\w+)?)\*\*:?\s*(.*)', line)
        if m:
            normalized.append(f"{m.group(1)}: {m.group(2)}")
            continue

        # Plain line — append to last speaker or as narrator
        if normalized:
            normalized[-1] += " " + line
        else:
            normalized.append(f"Narrator: {line}")

    return "\n".join(normalized)


# ─── TTS Generation ─────────────────────────────────────────────────────────

def generate_single_speaker_tts(text, voice, filepath, max_retries=5):
    """Generate single-speaker TTS audio, save as MP3."""
    prompt = f"Generate audio from this precise transcript without adding or modifying anything:\n{text}"

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-preview-tts',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['AUDIO'],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                        )
                    )
                )
            )
            for part in response.candidates[0].content.parts:
                if getattr(part, 'inline_data', None) and getattr(part.inline_data, 'data', None):
                    pcm_path = filepath.replace('.mp3', '.pcm').replace('.wav', '.pcm')
                    with open(pcm_path, 'wb') as f:
                        f.write(part.inline_data.data)
                    os.system(f"ffmpeg -y -f s16le -ar 24000 -ac 1 -i '{pcm_path}' '{filepath}' > /dev/null 2>&1")
                    if os.path.exists(pcm_path):
                        os.remove(pcm_path)
                    return True
            return False
        except Exception as e:
            err = str(e)
            if "exceeded your current quota" in err:
                print(f"\n[FATAL] Daily quota exhausted: {err}", flush=True)
                sys.exit(1)
            elif "429" in err or "RESOURCE_EXHAUSTED" in err or "500" in err:
                wait = 60 * (2 ** attempt)
                print(f" [backoff {wait}s]", end="", flush=True)
                time.sleep(wait)
            else:
                print(f" [error: {err[:60]}]", end="", flush=True)
                return False
    return False


def generate_multi_speaker_tts(text, speaker_mapping, filepath, max_retries=5):
    """Generate multi-speaker TTS audio for conversations, save as .wav."""
    normalized = normalize_conversation_text(text)
    prompt = f"Generate audio from this precise transcript without adding or modifying anything:\n\n{normalized}"

    speaker_configs = []
    for speaker_name, voice_name in speaker_mapping.items():
        speaker_configs.append(
            types.SpeakerVoiceConfig(
                speaker=speaker_name,
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                )
            )
        )

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-preview-tts',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['AUDIO'],
                    speech_config=types.SpeechConfig(
                        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                            speaker_voice_configs=speaker_configs
                        )
                    )
                )
            )
            data = response.candidates[0].content.parts[0].inline_data.data
            save_wav(filepath, data)
            return True
        except Exception as e:
            err = str(e)
            if "exceeded your current quota" in err:
                print(f"\n[FATAL] Daily quota exhausted: {err}", flush=True)
                sys.exit(1)
            elif "429" in err or "RESOURCE_EXHAUSTED" in err or "500" in err:
                wait = 60 * (2 ** attempt)
                print(f" [backoff {wait}s]", end="", flush=True)
                time.sleep(wait)
            else:
                print(f" [error: {err[:60]}]", end="", flush=True)
                return False
    return False


# ─── Transcript Generation ──────────────────────────────────────────────────

def generate_transcript(data, task_type, max_retries=3):
    """Generate a missing transcript using Gemini text generation."""
    title = data.get('title', 'Untitled')
    context = data.get('context', '')

    if task_type == TaskType.LISTEN_ANNOUNCEMENT:
        prompt = f"""Generate a TOEFL 2026 "Listen to an Announcement" transcript.
Title: "{title}" | Context: {context}

Write a short academic-related announcement (80-150 words), monologic format.
The announcement should be about {title.lower()} in an academic/campus setting.
Output ONLY the transcript text, no JSON, no markdown."""
    elif task_type == TaskType.LISTEN_ACADEMIC_TALK:
        prompt = f"""Generate a TOEFL 2026 "Listen to an Academic Talk" transcript.
Title: "{title}" | Context: {context}

Write a short academic talk by an educator (175-250 words), monologic format.
The talk should be about {title.lower()}.
Output ONLY the transcript text, no JSON, no markdown."""
    else:
        return None

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt],
                config=types.GenerateContentConfig(temperature=0.7)
            )
            text = response.text.strip()
            # Remove any markdown wrapping
            text = re.sub(r'^```\w*\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
            return text.strip()
        except Exception as e:
            print(f" [transcript error: {e}]", end="", flush=True)
            time.sleep(5)
    return None


# ─── Main ────────────────────────────────────────────────────────────────────

def find_items_needing_audio(db, task_type_filter=None):
    """Find all listening items that need audio generation."""
    query = db.query(TestItem).filter(TestItem.section == SectionType.LISTENING)
    if task_type_filter:
        query = query.filter(TestItem.task_type == task_type_filter)

    items = query.all()
    needs_audio = []

    for item in items:
        data = json.loads(item.prompt_content)
        audio_url = data.get('audio_url', '') or ''

        if audio_url == 'PENDING_TTS' or not audio_file_exists(audio_url):
            needs_audio.append(item)

    return needs_audio


def run():
    parser = argparse.ArgumentParser(description='Recover missing audio for listening items')
    parser.add_argument('--apply', action='store_true', help='Actually generate audio (default is dry-run)')
    parser.add_argument('--type', choices=['lcr', 'conversation', 'announcement', 'talk', 'all'], default='all')
    parser.add_argument('--delay', type=int, default=10, help='Seconds between TTS calls')
    parser.add_argument('--limit', type=int, default=0, help='Max items to process (0 = all)')
    args = parser.parse_args()

    db = SessionLocal()
    task_filter = TASK_TYPE_MAP.get(args.type) if args.type != 'all' else None
    items = find_items_needing_audio(db, task_filter)

    print(f"\n{'='*60}")
    print(f"  LISTENING AUDIO RECOVERY")
    print(f"{'='*60}")
    print(f"  Items needing audio: {len(items)}")
    print(f"  Mode: {'APPLY' if args.apply else 'DRY RUN'}")
    print(f"  Delay: {args.delay}s between calls")
    if args.limit:
        print(f"  Limit: {args.limit} items")
        items = items[:args.limit]
    print()

    # Group by type for reporting
    from collections import Counter
    type_counts = Counter(item.task_type.value for item in items)
    for typ, count in type_counts.most_common():
        print(f"  {typ}: {count}")
    print()

    if not args.apply:
        # Dry run — just list items
        for i, item in enumerate(items):
            data = json.loads(item.prompt_content)
            text = extract_tts_text(data, item.task_type)
            title = data.get('title', '?')[:35]
            url = data.get('audio_url', '')[:35]
            has_text = bool(text and len(text.split()) > 3)
            print(f"  {i+1:3}. [{item.target_level.name:3}] {item.task_type.value[:22]:22s} | text={'✓' if has_text else '✗':1s} | \"{title}\" | url={url}")
        print(f"\n  [DRY RUN] Pass --apply to generate audio.")
        db.close()
        return

    # ─── Apply mode ──────────────────────────────────────────────────────
    success = 0
    failed = 0
    transcript_generated = 0

    for idx, item in enumerate(items):
        data = json.loads(item.prompt_content)
        text = extract_tts_text(data, item.task_type)
        title = data.get('title', '?')[:35]

        # Step 1: Generate transcript if missing
        if not text or len(text.split()) < 5:
            print(f"  [{idx+1}/{len(items)}] Generating transcript for \"{title}\"...", end="", flush=True)
            text = generate_transcript(data, item.task_type)
            if text:
                data['text'] = text
                transcript_generated += 1
                print(f" ✓ ({len(text.split())}w)", flush=True)
                time.sleep(args.delay)
            else:
                print(f" ✗ (no transcript)", flush=True)
                failed += 1
                continue

        # Step 2: Generate TTS
        if item.task_type == TaskType.LISTEN_CONVERSATION:
            # Multi-speaker conversation
            speakers = detect_speakers(text)
            ext = '.wav'
            filename = f"LC-{uuid.uuid4().hex[:10]}{ext}"
            filepath = os.path.join(AUDIO_DIR, filename)

            print(f"  [{idx+1}/{len(items)}] 🎙️ Multi-speaker | {len(speakers)} voices | \"{title}\"...", end="", flush=True)
            ok = generate_multi_speaker_tts(text, speakers, filepath)
        else:
            # Single-speaker
            voice = SINGLE_VOICES[idx % len(SINGLE_VOICES)]
            prefix = {
                TaskType.LISTEN_CHOOSE_RESPONSE: 'LCR',
                TaskType.LISTEN_ANNOUNCEMENT: 'LA',
                TaskType.LISTEN_ACADEMIC_TALK: 'LT',
            }.get(item.task_type, 'L')
            ext = '.mp3'
            filename = f"{prefix}-{uuid.uuid4().hex[:10]}{ext}"
            filepath = os.path.join(AUDIO_DIR, filename)

            print(f"  [{idx+1}/{len(items)}] 🔊 {voice:7s} | \"{title}\"...", end="", flush=True)
            ok = generate_single_speaker_tts(text, voice, filepath)

        if ok and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            # Copy to root audio dir too
            import shutil
            root_dest = os.path.join(ROOT_AUDIO_DIR, filename)
            shutil.copy2(filepath, root_dest)

            # Update item in DB
            audio_url = f"audio/listening/{filename}"
            data['audio_url'] = audio_url
            item.prompt_content = json.dumps(data)
            if item.generation_notes:
                item.generation_notes = item.generation_notes.replace("PENDING_TTS", "TTS_DONE")
            db.commit()
            success += 1
            print(f" ✓", flush=True)
        else:
            failed += 1
            print(f" ✗", flush=True)

        time.sleep(args.delay)

    db.close()

    print(f"\n{'='*60}")
    print(f"  DONE!")
    print(f"    Audio generated: {success}")
    print(f"    Transcripts generated: {transcript_generated}")
    print(f"    Failed: {failed}")
    print(f"    Total: {success + failed}")
    print(f"{'='*60}")


if __name__ == '__main__':
    run()
