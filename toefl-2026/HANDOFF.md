Next Agent: You are taking over the building of the TOEFL 2026 platform backend. The psychometric anchors and both Phase 1 (Deterministic/Selected Response) and Phase 2 (LLM/Constructed Response) Scoring Engine algorithms are completely built and functioning locally. 

However, the new scoring algorithms currently run in a vacuum. If a test is completed, the student's essay, answers, and the AI feedback JSON are not saved anywhere permanently.

Your immediate, top-priority task is "Data Persistence." Do not touch the React frontend until you have achieved the following:

1. Modify `backend/app/models/models.py`. We urgently need a `TestResponse` SQL table to act as our ledger. It must tie to `TestSession` and `TestItemQuestion`. It MUST contain columns for `student_raw_response` (the essay string or audio S3 URL), `is_correct` (boolean), `rubric_score` (int), and `ai_feedback` (JSON). Create an imperative migration script and inject this table into the SQLite database.
2. Build the API Bridge. Create a FastAPI route (e.g. `POST /api/sessions/{session_id}/submit`) that accepts a giant dictionary of student answers, runs it through the `ScoringEngine` (which triggers Gemini AI grading for essays), and then `db.add()` the returned dictionary mappings directly into the new `TestResponse` SQL tables.
3. Test it. Write a Python scraper/script that mimics a POST network request to verify the scoring and the database logging works end-to-end. 

Only after the PostgreSQL/SQLite database successfully holds the written data and feedback should you begin building the React Zustand State Management and UI to catch user input.
