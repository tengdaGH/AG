# Item Bank Filling — Handoff Document

> **Date**: 2026-02-24 | **Status**: In Progress | **Target**: 10 test forms with no item overlap

---

## Current Inventory (Updated 2026-02-24 03:45)

| Task Type | Section | Usable | 10-Form Need | Status |
|---|---|---|---|---|
| Complete the Words | Reading | 115 | 20 passages | ✅ Done |
| Read in Daily Life | Reading | 41 | ~40 texts | ✅ Done |
| Read Academic Passage | Reading | 20 | 20 passages | ✅ Done |
| Listen & Choose Response | Listening | 150 | ~150 items | ✅ Done |
| Listen to Conversation | Listening | 20 | ~20 convos | ✅ Done |
| Listen to Announcement | Listening | 10 | ~10 | ✅ Done |
| Listen Academic Talk | Listening | 10 | ~10 | ✅ Done |
| Build a Sentence | Writing | 120 | 100 | ✅ Done |
| Write an Email | Writing | 35 | 10 | ✅ Done |
| Write Academic Discussion | Writing | 86 | 10 | ✅ Done |
| Listen and Repeat | Speaking | 98 | 70 | ✅ Done |
| Take an Interview | Speaking | 53 | 40 | ✅ Done |

**Total: 778 items | 752 FIELD_TEST | ALL 12 types at 10-form capacity ✅**

## Remaining Work

### TTS Audio Recovery (when rate limit resets)
5 listening items need TTS audio. Run:
```bash
python agents/scripts/recover_listening_audio.py --dry-run  # preview
python agents/scripts/recover_listening_audio.py             # generate
```

### Minor QA Cleanup
4 items in REVIEW (3 Read in Daily Life, 1 Read Academic Passage) with editorial/fairness flags.

## Key Files
- `backend/scripts/gauntlet_qa.py` — QA pipeline (4 agents: Content → Fairness → MCQ → Editorial)
- `agents/scripts/populate_interviews.py` — Interview generation (32 scenarios)
- `agents/scripts/populate_academic_passages.py` — Academic passage generation
- `agents/scripts/populate_listen_repeat.py` — Listen & Repeat generation + TTS
- `.agents/skills/toefl_item_generation/SKILL.md` — generation instructions
- `.agents/skills/toefl_audio_generation/SKILL.md` — TTS audio generation

## Environment
- `GEMINI_API_KEY` in `backend/.env`
- Backend: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm run dev`

