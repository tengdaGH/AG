---
name: listening_audio_recovery
description: Recovering and generating missing TTS audio for TOEFL 2026 listening items using Gemini multi-speaker and single-speaker TTS.
---

# Listening Audio Recovery Skill

This skill provides instructions for finding and generating missing audio for listening items. Uses Gemini 2.5 Flash Preview TTS with multi-speaker support for conversations.

> [!NOTE]
> As of Feb 2026, all 204 listening items have working audio (0 PENDING_TTS, 0 stale URLs). This skill remains for any future items that may need audio generation.

## 🔍 Detecting Missing Audio

Items needing audio fall into two categories:
1. **PENDING_TTS**: Items with `audio_url = "PENDING_TTS"` in `prompt_content` — never had audio generated
2. **Stale URLs**: Items with an `audio_url` path that points to a nonexistent file — audio was lost or never created

The recovery script detects both automatically by checking file existence on disk.

## 🎙️ TTS Modes

### Single-Speaker (LCR, Announcement, Academic Talk)
- Uses `prebuilt_voice_config` with one voice
- Output: `.mp3` via ffmpeg PCM→MP3 conversion
- LCR items: only speak `dialogue[0]` (the stimulus utterance)

### Multi-Speaker (Conversation)
- Uses `multi_speaker_voice_config` with speaker-to-voice mapping
- Output: `.wav` saved directly from PCM data
- Speaker labels detected automatically from text: `F:`, `M:`, `(F)`, `(M)`, `**Speaker**:`
- Default mapping: F → Kore, M → Puck

## 🎤 Voice Palette

| Voice | Character | Best For |
|-------|-----------|----------|
| Puck | Bright, youthful | Students, young adults |
| Aoede | Warm, professional | Professors, librarians |
| Charon | Deep, authoritative | Administrators |
| Kore | Clear, friendly | Teaching assistants, peers |
| Fenrir | Energetic, robust | Narrators, guest speakers |

## 🛠 Script

### [recover_listening_audio.py](file:///Users/tengda/Antigravity/toefl-2026/agents/scripts/recover_listening_audio.py)

Unified recovery script that handles all listening types.

```bash
cd toefl-2026
source backend/venv/bin/activate

# Dry-run: list all items needing audio
python agents/scripts/recover_listening_audio.py

# Generate audio for all types
python agents/scripts/recover_listening_audio.py --apply

# Filter by type
python agents/scripts/recover_listening_audio.py --apply --type conversation
python agents/scripts/recover_listening_audio.py --apply --type lcr

# Adjust rate limiting
python agents/scripts/recover_listening_audio.py --apply --delay 12

# Limit items processed
python agents/scripts/recover_listening_audio.py --apply --limit 10
```

## 📁 Output Paths

Audio files are saved to **both** directories for compatibility:
- `frontend/public/audio/listening/` — served by Next.js
- `audio/listening/` — root-level backup

Items are updated with URL format: `audio/listening/{PREFIX}-{uuid}.{ext}`
- Prefixes: `LCR-` (choose response), `LC-` (conversation), `LA-` (announcement), `LT-` (academic talk)

## ⚡ Rate Limit Handling

- Default delay: 10 seconds between TTS calls (~6 RPM)
- On 429/RESOURCE_EXHAUSTED: exponential backoff (60s, 120s, 240s, 480s, 960s)
- On daily quota exhaustion: script exits with FATAL error
- On 500 (server error): same exponential backoff
- **Inworld API** (`INWORLD_KEY` in `.env`) is available as a fallback if Gemini hits sustained limits

## 🔄 Transcript Generation

For items missing transcript text (PENDING_TTS items with no `text` field), the script automatically generates a transcript using Gemini text generation before proceeding to TTS. Transcripts are constrained by the item's existing title, context, and questions.

## ✅ Safe to Re-Run
The script skips items that already have working audio files on disk.
