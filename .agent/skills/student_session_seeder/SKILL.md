---
name: student_session_seeder
description: >
  Generates realistic synthetic student sessions and responses for load testing,
  score pipeline validation, and UI development. Inserts directly into user_data.db.
  Use when real student data is absent and you need to test scoring, teacher dashboard,
  or Alfred's student data checks.
---

# student_session_seeder — Synthetic Data Generator

The student_session_seeder creates realistic, ETS-spec-compliant synthetic student data
so you can develop and test the platform without waiting for real users.

---

## student_session_seeder's Mandate

> "Development without real data is flying blind. Synthetic data is the next best thing."

The seeder creates sessions that mirror real student behavior:
- Realistic response time distributions
- CEFR-level-appropriate answer accuracy rates
- Realistic abandonment/completion patterns

---

## When to Run

- When Alfred reports: "0 sessions in user_data.db" (you are flying blind)
- Before testing the Teacher Dashboard (needs session roster data)
- Before running `scoring_auditor` (needs sessions to audit)
- After any schema change to `user_data.db` (verify the pipeline end-to-end)

---

## Seeder Protocol

### Step 1 — Define student profiles

The seeder creates synthetic students across CEFR levels:

| Profile | CEFR | Reading Accuracy | Listening Accuracy | Writing Band | Speaking Band |
|---------|------|-----------------|-------------------|--------------|---------------|
| `weak_student` | A2 | 40% | 35% | 1–2 | 1–2 |
| `average_student` | B1 | 60% | 55% | 3 | 3 |
| `good_student` | B2 | 75% | 70% | 4 | 4 |
| `strong_student` | C1 | 88% | 85% | 5 | 5 |
| `native_like` | C2 | 95% | 93% | 5–6 | 5–6 |

---

### Step 2 — Run the seeder

```bash
cd /Users/tengda/Documents/Antigravity/toefl-2026
source backend/venv/bin/activate
python3 agents/scripts/seed_student_sessions.py --count 10 --profile mixed 2>&1
```

Arguments:
- `--count N` — number of complete sessions to generate (default: 10)
- `--profile {weak|average|good|strong|mixed}` — student ability level (default: mixed)
- `--username-prefix TEST` — prefix for synthetic usernames (default: `SYN`)

---

### Step 3 — What the seeder creates

For each synthetic session:

1. **Student account** in `user_data.db` (if not already exists):
   ```sql
   INSERT OR IGNORE INTO students (username, password_hash, created_at)
   VALUES (?, ?, ?);
   ```

2. **Session record**:
   ```sql
   INSERT INTO sessions (student_id, status, created_at, completed_at)
   VALUES (?, 'completed', ?, ?);
   ```

3. **Responses** for all 93 scored questions:
   - Reading (35 Qs): correct/incorrect based on CEFR accuracy rate ± gaussian noise
   - Listening (35 Qs): correct/incorrect based on CEFR accuracy rate ± gaussian noise
   - Writing (12 Qs): Build-a-Sentence correct/incorrect + simulated AI scores for email/discussion
   - Speaking (11 Qs): simulated transcripts + AI scores for listen-and-repeat and interview

4. **Final score** computed by running the actual IRT scoring engine (not hardcoded):
   ```python
   from app.services.score_calculator import calculate_final_score
   score = calculate_final_score(session_id)
   ```

---

### Step 4 — Verify

After seeding, confirm data looks correct:

```bash
python3 - <<'EOF'
import sqlite3
conn = sqlite3.connect("backend/user_data.db")
sessions = conn.execute("SELECT COUNT(*) FROM sessions WHERE status='completed'").fetchone()[0]
responses = conn.execute("SELECT COUNT(*) FROM responses").fetchone()[0]
print(f"Sessions: {sessions}")
print(f"Responses: {responses}")
conn.close()
EOF
```

Then run Alfred — he should report sessions in the Student Data pillar.

---

## Script to Create: `agents/scripts/seed_student_sessions.py`

This script does not yet exist. Build it following `python_housekeeping` skill conventions.

Key design rules:
- Usernames must start with `SYN_` to distinguish from real students
- Sessions must have `notes = 'SYNTHETIC'` in a metadata field (or a dedicated column if schema allows)
- The seeder must be **idempotent**: running it twice doesn't double-insert
- Use the real IRT scoring engine — synthetic data that uses a fake scorer teaches you nothing

---

## Alfred Supervision

Alfred does NOT audit synthetic sessions the same way as real ones.
Alfred checks: "Are there SYN_ sessions mixed with real data?" — if yes, flags 🟡.

Before deploying to production, run:
```bash
python3 agents/scripts/seed_student_sessions.py --purge-synthetic
```
This deletes all `SYN_*` users and their sessions, leaving only real student data.

---

## Relationship to Other Agents

- **Alfred** uses seeder output to test his own student data checks
- **scoring_auditor** needs sessions to audit — seeder provides them
- **Teacher Dashboard** needs session roster — seeder populates it for dev/testing
