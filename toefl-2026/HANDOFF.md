# Handoff: TOEFL 2026 Item Bank Integration

## Context
The TOEFL 2026 item bank has been duplicated from the legacy project (`Documents/Cursor Code`) to this repository (`Antigravity/toefl-2026`) to prepare for a full system merger.

## Status
- **Data**: All TOEFL-related JSON banks are located in the `data/` directory.
- **Audio**: Associated audio files (Interview, Listening, and Listen & Repeat) are in the `audio/` directory.
- **Exclusion**: IELTS content was explicitly ignored and remains in the legacy project.

## Project Structure
- `data/`: JSON files for all item types (Complete the Words, Academic Discussion, etc.).
- `audio/`: MP3/SRT files organized by item type.
- `backend/`: FastAPI application (FastAPI + SQLModel + SQLite).
- `frontend/`: Next.js application.

## Key Technical Requirements
1. **TOEFL 2026 Specifications**: Refer to the technical manual (`docs/TOEFL-2026-Technical-Manual.pdf` in the legacy project) for official formatting and scoring rules.
2. **C-Test Logic**: "Complete the Words" follows a strict rule: keep `floor(length/2)` characters of every second word starting from the second sentence.
3. **Adaptive Routing**: The technical manual defines difficulty at the module level (Easy vs. Hard routing).

## Recommended Next Steps
1. **Backend Integration**: Create API endpoints to serve the JSON data from the new `backend` or migrate the JSON data into the SQLite database (`toefl_2026.db`).
2. **Frontend Porting**: Re-implement the practice screens (currently vanilla HTML/JS in the legacy project) within the Next.js `frontend` app.
3. **Audio Management**: Ensure the Next.js app correctly serves and plays the files from the `audio/` directory.

## Reference Materials
- `Documents/Cursor Code/AGENTS.md`: Detailed developer notes and formatting patterns.
- `Documents/Cursor Code/docs/item-review-log.md`: Audit trail for all items.

## Merge Status (2026-02-22)

**Item bank merge complete.** All 12 JSON data files were imported into `toefl_2026.db`.

| Section | Task Type | Count |
|---|---|---|
| READING | READ_ACADEMIC_PASSAGE | 12 |
| READING | READ_IN_DAILY_LIFE | 31 |
| READING | COMPLETE_THE_WORDS | 112 |
| WRITING | BUILD_A_SENTENCE | 120 |
| WRITING | WRITE_ACADEMIC_DISCUSSION | 105 |
| WRITING | WRITE_AN_EMAIL | 35 |
| SPEAKING | TAKE_AN_INTERVIEW | 8 |
| READING | *(pre-existing, UNTYPED)* | 13 |
| **Total** | | **436** |

### Import Command
```bash
cd backend && source venv/bin/activate
python -m app.scripts.import_itembank          # live import
python -m app.scripts.import_itembank --dry-run # validate only
```

### Schema Changes
- Added `task_type` column (enum) to `test_items` for item-subtype classification
- Added `source_file` and `source_id` columns for import traceability
- Added `GET /api/items/audit` endpoint for diagnostics

## Progress Update (2026-02-23)

### Audio Padding & Connectivity
- **Backend Padding**: Implemented `ffmpeg`-based padding in `backend/app/services/inworld_service.py`. It adds 500ms of silence to the start and end of Inworld TTS audio to prevent clipping on Bluetooth devices.
- **Frontend Refactor**: Centralized API access via `API_BASE_URL` in `frontend/src/lib/api-config.ts`.
- **CORS & Tunneling**: Backend now allows all origins. Added `Bypass-Tunnel-Reminders: true` header to all frontend fetch calls to skip Localtunnel's landing page.

### Vercel Deployment
- **Frontend URL**: [https://frontend-ebon-zeta-67.vercel.app](https://frontend-ebon-zeta-67.vercel.app)
- **Status**: Production-ready. Connected to local backend via Localtunnel.
- **Architecture**:
  - Frontend: Vercel (Cloud)
  - Backend: Mac mini (Local) + `localtunnel` for public access.
  - Environment Var: `NEXT_PUBLIC_API_URL` set to current tunnel URL.

### Current Dev Links
- **Backend Tunnel**: `https://heavy-shirts-work.loca.lt` (Password: `154.17.8.50`)
- **Item Bank (Live)**: [https://frontend-ebon-zeta-67.vercel.app/dashboard/admin/items](https://frontend-ebon-zeta-67.vercel.app/dashboard/admin/items)

## Progress Update (2026-02-24)

### UI Components Refactoring
- **Build a Sentence (`BuildSentence.tsx`)**: Re-engineered drag-and-drop physics using `@dnd-kit/core`. Resolved vertical baseline jumping by injecting invisible `X` placeholders with identical font metrics into empty slots. Replaced the static layout with intelligent interactive drop-hints, providing bounding outlines and teal hover highlights during active dragging. Stripped legacy text borders.
- **Write an Email (`WriteEmail.tsx`)**: Completely redesigned the layout to perfectly replicate the utilitarian ETS specification UI shown in official reference materials (Figure 9). Implemented the exact header fields ("Your Response:", "To:", "Subject:"), stripped the extra 'Copy' button, added a functioning 'Hide Word Count' toggle, and integrated a stark plain gray border box design inline with the official technical manual. Integrated directly into the `/demo/writing` page.

## Agent Routing Protocol (Media & Reasoning)

**Primary Reasoning (Subscription Only):**
- Perform all reasoning, code analysis, content creation, and co-writing using the NATIVE model provider linked to my Google AI Ultra subscription. 
- DO NOT use the API key for text-based reasoning or logic tasks. 
- Use the models identified in the 'Model Quota' settings (Gemini 3.1 Pro, etc.) for these activities.

**Media Generation (API Key Only):**
- For any request involving Image Generation (Nano Banana Pro) or Voice/Audio Generation (Lyria 3/Gatling), you MUST use the provided Google Cloud API key (`AIzaSyBQ3QM89VQGKS-BW_TfZuzKabm28PphrTo`).
- Treat image and voice generation as "External Tools" that require the API endpoint.
- If the native model returns a 503 capacity error for images, do not retry with the subscription; immediately fail-over to the API-based generation script.

**Goal:**
- Maximize the use of the unlimited reasoning/writing capacity of the Ultra plan.
- Reserve the API key strictly for high-fidelity media assets to be covered by the monthly Google Cloud credits.
