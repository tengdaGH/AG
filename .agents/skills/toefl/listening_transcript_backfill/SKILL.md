---
name: listening_transcript_backfill
description: Generating and backfilling missing transcript text for legacy listening items that have audio but no stored transcript.
---

# Listening Transcript Backfill Skill

This skill handles legacy listening items that have working audio files and MCQ questions but lack a stored transcript in their `text` field. These items typically show only a context stub (e.g., "History class") in the dashboard preview.

> [!NOTE]
> As of Feb 2026, all 204 listening items have been backfilled with proper transcripts. This skill remains for any future items that may need similar treatment.

## 🔍 Identifying Incomplete Items

Legacy items are identified by:
- `task_type` is `LISTEN_ANNOUNCEMENT` or `LISTEN_ACADEMIC_TALK`
- `text` field has ≤10 words (just the context string, not a real transcript)
- Audio file exists and is playable
- Questions exist and are well-formed

> [!NOTE]
> LCR items (`LISTEN_CHOOSE_RESPONSE`) do NOT need a `text` field — they use `dialogue` arrays by design. Conversation items always have full transcripts.

## 🧠 Transcript Generation Strategy

Transcripts are generated using **question-constrained prompting**:
1. The existing MCQ questions are provided as constraints
2. Gemini generates a transcript that contains the information needed to answer those questions
3. This ensures the generated text aligns with the existing audio content and correct answers

### Word Count Targets (per spec)
| Type | Target |
|------|--------|
| Announcement | 80–150 words |
| Academic Talk | 175–250 words |

## 🛠 Script

### [backfill_listening_transcripts.py](file:///Users/tengda/Antigravity/toefl-2026/agents/scripts/backfill_listening_transcripts.py)

```bash
cd toefl-2026
source backend/venv/bin/activate

# Dry-run: list items needing transcripts
python agents/scripts/backfill_listening_transcripts.py

# Generate and save transcripts
python agents/scripts/backfill_listening_transcripts.py --apply

# Adjust rate limiting
python agents/scripts/backfill_listening_transcripts.py --apply --delay 8
```

## ⚠️ Important Notes

- This is a **text-only** operation — no TTS audio is generated (audio already exists)
- The script adds a `generation_notes` entry: `"Transcript backfilled ({N}w)"`
- Uses `gemini-2.5-flash` for text generation (not the TTS model)
- Has 3-retry logic with 5s waits on API errors
- Safe to re-run: only targets items with ≤10 word text fields
