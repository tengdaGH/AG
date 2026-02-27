# Agent Handoff: TOEFL 2026 Audio Synthesis & Verification

## Current State of the Item Bank
We just completed a massive audit and recovery of orphaned audio files. Here is the current audio coverage status for the 520 listening/speaking items:

### Fully Covered (Audio exists and works)
- LISTEN_ACADEMIC_TALK: 12/12
- LISTEN_ANNOUNCEMENT: 21/21
- LISTEN_AND_REPEAT: 98/105

### Partially Covered (Needs Audio Generation)
- LISTEN_CHOOSE_RESPONSE: 150/262 (112 ETS items missing audio)
- LISTEN_CONVERSATION: 20/60 (40 ETS items missing audio)
- TAKE_AN_INTERVIEW: 14/60 (46 items missing audio)

## What Has Been Completed
1. **Audited the 205 missing items:** Found that `LISTEN_CHOOSE_RESPONSE` and `LISTEN_AND_REPEAT` data structures were mostly intact, but `TAKE_AN_INTERVIEW` and `LISTEN_CONVERSATION` had parsing issues.
2. **Fixed Parsing Issues:** 
   - Repaired 7 broken `TAKE_AN_INTERVIEW` items which contained raw ETS text instead of the structured `scenario` and `questions` arrays.
   - Updated the conversation parsing logic to properly handle single-speaker formats (`Professor:`, `Announcer:`) and accent-labeled speaker formats (`(M-Can)`, `(W-Br)`).
3. **Wrote the Synthesizer Script:**
   - Created `agents/scripts/generate_ets_audio.py` that fully implements the `toefl_voice_direction` skill for all 4 missing task types (voices, tones, multi-speaker assignment).
   - Tested it with `--limit 205` in dry-run mode, and it successfully parsed and assigned voices/tones to all 205 missing items.

## Immediate Next Steps (For the Next Agent)
The script `generate_ets_audio.py` was executed, but it currently fails when running with the `--apply` flag (it instantly outputs `✗` for every item).

Your task is to:
1. **Debug the Failure:** Find out why `generate_ets_audio.py --apply` is failing. (Recommendation: run `python agents/scripts/generate_ets_audio.py --apply --limit 1` without redirection to see the exact Python exception. The error is likely somewhere inside `tts_single`, `tts_multi`, or the `ffmpeg` conversion step).
2. **Fix the Script:** Resolve the bug preventing the API call or file save (Note: `log_audio.py` missing import warning is non-fatal; focus on the TTS generation error).
3. **Synthesize Audio:** Once fixed, run the script to successfully generate the audio for the remaining 205 items.
