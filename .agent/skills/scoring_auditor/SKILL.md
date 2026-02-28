---
name: scoring_auditor
description: >
  Weekly audit agent that pulls all completed sessions, cross-checks IRT theta estimates
  against AI scores for Writing and Speaking, and flags sessions where the two disagree
  by more than 1 SD. Catches scoring pipeline failures before students see wrong scores.
  Run every Monday, or after any backend scoring change.
---

# scoring_auditor — Score Integrity Watchdog

The scoring_auditor verifies that the IRT scoring engine and the AI scoring engine
agree with each other within acceptable bounds. When they diverge, it flags the sessions
for human review and prevents silent score corruption.

---

## scoring_auditor's Mandate

> "A score the student never sees is useless. A wrong score they see is worse."

scoring_auditor does not fix scores. It detects and surfaces divergence so a human
(or alfred) can investigate and decide.

---

## When to Run

- Every Monday (or start of teaching week)
- Immediately after any change to `score_calculator.py`, `irt_service.py`, or `gemini_service.py`
- Whenever Alfred flags: "sessions with null final_score" or "student sessions stuck"

---

## Audit Protocol

### Step 1 — Pull all completed sessions

```bash
cd /Users/tengda/Documents/Antigravity/toefl-2026
source backend/venv/bin/activate
python3 agents/scripts/scoring_audit.py 2>&1
```

The script lives at `agents/scripts/scoring_audit.py`.

---

### Step 2 — What the audit checks

#### Check A — Null final scores
```sql
SELECT id, student_id, created_at, status
FROM sessions
WHERE status='completed' AND final_score IS NULL;
```
**Red threshold**: > 0 sessions. Every completed session must have a final score.

#### Check B — IRT theta vs AI score divergence (Writing & Speaking)
For each session:
1. Pull the IRT theta for Writing section (from `session_sections` or `scores` table)
2. Pull the AI band score (0–5 per task, aggregated to band 1–6)
3. Compute: `delta = abs(irt_band - ai_band)`
4. **Flag if delta > 1.0 band** (exceeds SEM tolerance of 0.36)

Expected correlation: r ≥ 0.85 (ETS spec, see `toefl_2026_spec_sheet.md`)

#### Check C — Exposure count sanity
```sql
SELECT id, title, exposure_count
FROM test_items
WHERE lifecycle_status='ACTIVE'
ORDER BY exposure_count DESC
LIMIT 10;
```
Flag any item where `exposure_count / total_sessions > 0.15` (ETS 15% overexposure rule).

#### Check D — Scoring latency
```sql
SELECT id, created_at, completed_at,
       (julianday(completed_at) - julianday(created_at)) * 24 * 60 as minutes
FROM sessions
WHERE status='completed'
ORDER BY created_at DESC
LIMIT 20;
```
Flag sessions where scoring took > 5 minutes (may indicate Gemini API timeout swallowing scores).

---

### Step 3 — Output the audit report

The audit script saves its report to:
```
logs/scoring_audits/YYYY-MM-DD.md
```

Format follows Alfred's brief style:
- 🔴 Action Required: null scores, divergence > 1.5 bands
- 🟡 Watch: divergence 1.0–1.5 bands, high latency
- 🟢 All Clear: everything within bounds

---

### Step 4 — Report to Alfred

After running, Alfred picks up the audit status on his next daily review.
Alfred checks: "Was scoring_auditor run this week?" (looks for a file in `logs/scoring_audits/`
with mtime ≤ 7 days). If not found → Alfred flags 🟡.

---

## Script to Create: `agents/scripts/scoring_audit.py`

This script does not yet exist. Build it following `python_housekeeping` skill conventions:

```python
#!/usr/bin/env python3
# Purpose: Weekly score integrity audit — compares IRT vs AI scores, finds null scores,
#          checks item overexposure. Saves report to logs/scoring_audits/YYYY-MM-DD.md
# Usage:   python3 agents/scripts/scoring_audit.py
# Created: <date>
# Self-Destruct: No
```

The script must:
1. Connect to `backend/user_data.db`
2. Connect to `backend/item_bank.db`
3. Run all 4 checks above
4. Save a Markdown report to `logs/scoring_audits/YYYY-MM-DD.md`
5. Exit code 0 if no reds, 1 if any reds (same convention as Alfred)

---

## Relationship to Other Agents

- **Alfred** supervises scoring_auditor — he flags if it hasn't run in 7 days
- **irt_item_graduation** provides the IRT parameters that scoring_auditor validates against
- **item_writer** is upstream — if items have bad IRT params, scores will diverge
