# Backlog & Daily Standup
**Persistence**: This file tracks loose ends and unfinished tasks to be addressed at the start of each morning.

## 🔴 Immediate Loose Ends (TOEFL 2026)
- [ ] **Final Audio Synthesis**: Generate the remaining 44 `TAKE_AN_INTERVIEW` items.
    - **Context**: Blocked by Gemini TTS daily quota. Reset expected at ~08:00 Local/00:00 Pacific.
    - **Command**: `backend/venv/bin/python agents/scripts/generate_ets_audio.py --apply --delay 10`
- [ ] **Data Integrity Check**: Run a final audit of `media_url` and `prompt_content` in `toefl_2026.db` once the final 44 items are done.
- [ ] **Audio Manifest Update**: Regenerate the final `audio_voice_log.jsonl` manifest to include the last batch.

## 🟡 Pending Improvements
- [ ] **Refactor `generate_ets_audio.py`**: Merge the model rotation and jitter logic into a more modular `TTSClient` class if this becomes a recurring need.
- [ ] **IELTS Dashboard Integration**: Verify if any reading items imported in previous sessions require further data cleaning or UI alignment.

## 🟢 Habits & Principles
- **Morning Routine**: Start every session by reviewing this file and clearing 🔴 items first.
- **Tidying**: Ensure all temporary scripts (e.g., `backfill_audio_log.py`) are cleaned up or moved to `/tmp/` once their permanent logic is absorbed.
