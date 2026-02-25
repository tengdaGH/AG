# ============================================================
# Purpose:    Utility to append a structured voice log entry to audio_voice_log.jsonl
#             after successful Gemini TTS audio generation for TOEFL/IELTS items.
# Usage:      python log_audio.py --item_id "abc123" --task_type "LISTEN_ACADEMIC_TALK" ...
#             Or import append_voice_log() directly in generation scripts.
# Created:    2026-02-25
# Self-Destruct: No
# ============================================================

import argparse
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Canonical log path — relative to the toefl-2026 project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # .agent/skills/toefl_voice_direction → up 4 levels
_LOG_PATH = _PROJECT_ROOT / "audio" / "audio_voice_log.jsonl"


def append_voice_log(
    item_id: str,
    task_type: str,
    audio_file: str,
    engine: str = "gemini-2.5-flash-preview-tts",
    mode: str = "single",  # "single" or "multi"
    speakers: list[dict] | None = None,
    tts_prompt_preview: str = "",
    duration_seconds: float | None = None,
    verified: bool = False,
    notes: str = "",
) -> Path:
    """
    Append one entry to the voice log JSONL file.

    Parameters
    ----------
    item_id             DB item ID or descriptive slug.
    task_type           TOEFL task type enum value (e.g. "LISTEN_ACADEMIC_TALK").
    audio_file          Relative path from project root (e.g. "audio/listening/LT-abc.wav").
    engine              TTS engine identifier string.
    mode                "single" or "multi".
    speakers            List of speaker dicts (see schema in SKILL.md Section 8a).
    tts_prompt_preview  First ~200 chars of the TTS prompt sent to the API.
    duration_seconds    Audio duration if known, else None.
    verified            Set True after a human has listened and approved the audio.
    notes               Any anomalies or special handling notes.

    Returns
    -------
    Path to the log file.
    """
    # Build timestamp in the project's local timezone (Asia/Shanghai, UTC+8)
    tz_local = timezone(timedelta(hours=8))
    timestamp = datetime.now(tz=tz_local).isoformat(timespec="seconds")

    entry = {
        "timestamp": timestamp,
        "item_id": item_id,
        "task_type": task_type,
        "audio_file": audio_file,
        "engine": engine,
        "mode": mode,
        "speakers": speakers or [],
        "tts_prompt_preview": tts_prompt_preview[:300],  # cap at 300 chars
        "duration_seconds": duration_seconds,
        "verified": verified,
        "notes": notes,
    }

    # Ensure the log directory exists
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with _LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"[voice_log] Appended entry for {item_id} → {_LOG_PATH.relative_to(_PROJECT_ROOT)}")
    return _LOG_PATH


def read_log(as_dicts: bool = True) -> list:
    """Read and parse the voice log file."""
    if not _LOG_PATH.exists():
        return []
    lines = _LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    if as_dicts:
        return [json.loads(line) for line in lines if line.strip()]
    return lines


def mark_verified(item_id: str) -> int:
    """Mark all log entries for a given item_id as verified=True. Returns count updated."""
    if not _LOG_PATH.exists():
        return 0
    entries = read_log()
    updated = 0
    for entry in entries:
        if entry.get("item_id") == item_id:
            entry["verified"] = True
            updated += 1
    if updated:
        with _LOG_PATH.open("w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return updated


# ─── CLI interface ────────────────────────────────────────────────────────────

def _cli():
    parser = argparse.ArgumentParser(
        description="Append a voice log entry to audio_voice_log.jsonl"
    )
    parser.add_argument("--item_id", required=True)
    parser.add_argument("--task_type", required=True)
    parser.add_argument("--audio_file", required=True)
    parser.add_argument("--engine", default="gemini-2.5-flash-preview-tts")
    parser.add_argument("--mode", default="single", choices=["single", "multi"])
    parser.add_argument("--voice", help="Voice name (for single-speaker)")
    parser.add_argument("--gender", default="")
    parser.add_argument("--age_range", default="")
    parser.add_argument("--accent", default="american")
    parser.add_argument("--role", default="")
    parser.add_argument("--character_name", default="")
    parser.add_argument("--tone", default="")
    parser.add_argument("--prompt_preview", default="")
    parser.add_argument("--duration", type=float, default=None)
    parser.add_argument("--verified", action="store_true")
    parser.add_argument("--notes", default="")

    # Special: --verify-item to mark an existing item verified
    parser.add_argument("--verify-item", metavar="ITEM_ID",
                        help="Mark all log entries for this item_id as verified")

    args = parser.parse_args()

    if args.verify_item:
        count = mark_verified(args.verify_item)
        print(f"[voice_log] Marked {count} entries as verified for item '{args.verify_item}'")
        return

    speakers = []
    if args.voice:
        speakers.append({
            "role": args.role,
            "name": args.character_name,
            "gender": args.gender,
            "age_range": args.age_range,
            "accent": args.accent,
            "voice": args.voice,
            "tone_instruction": args.tone,
        })

    append_voice_log(
        item_id=args.item_id,
        task_type=args.task_type,
        audio_file=args.audio_file,
        engine=args.engine,
        mode=args.mode,
        speakers=speakers,
        tts_prompt_preview=args.prompt_preview,
        duration_seconds=args.duration,
        verified=args.verified,
        notes=args.notes,
    )


if __name__ == "__main__":
    _cli()
