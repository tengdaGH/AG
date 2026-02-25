# IELTS Item Bank — Agent Briefing
**Date Written**: 2026-02-25T16:20 CST
**Author**: Antigravity (prior conversation agent)
**Status**: Ready to execute — no user input required at any step
**Priority**: HIGH

---

## Mission

Set up a new IELTS item bank inside the **existing TOEFL 2026 PostgreSQL/SQLite database**
at `/Users/tengda/Antigravity/toefl-2026/backend/` and migrate all
**129 parsed IELTS Reading JSON files** from `/Users/tengda/Antigravity/IELTS/parsed/`
into it. One broken file (`ielts-r-121.json`) in `/IELTS/broken/` should be skipped.

Do this **fully automatically** — **no user interruption whatsoever**.

---

## Context Rot Prevention Strategy

This job has ~130 files. To prevent failure from context exhaustion:

1. **Write a self-contained migration script** that runs entirely in the shell —
   the agent does NOT need to hold any file content in memory.
2. **Script tracks its own progress** via a `migration_state.json` sidecar file.
   On each run it loads state, processes files not yet marked `done`, and updates state.
3. **Idempotent**: Running the script twice is safe — it checks DB for existing `source_id`
   before inserting. Duplicate inserts are skipped, not errored.
4. **Batch size** in the script is 10 files per "wave". If you re-run, it picks up where
   it left off automatically via the state file.
5. After writing the script, execute it once end-to-end. Verify row counts.

---

## Environment

| Thing | Value |
|---|---|
| Python venv | `source /Users/tengda/Antigravity/toefl-2026/backend/venv/bin/activate` |
| DB connection | `sqlite:///…/toefl-2026/backend/toefl_2026.db` (default) OR `$DATABASE_URL` if set |
| Gemini API key | `AIzaSyBQ3QM89VQGKS-BW_TfZuzKabm28PphrTo` (from `toefl-2026/backend/.env`) |
| SQLAlchemy Base | `from app.database.connection import Base, engine` |
| Existing models file | `/Users/tengda/Antigravity/toefl-2026/backend/app/models/models.py` |
| JSON source dir | `/Users/tengda/Antigravity/IELTS/parsed/` (129 files, `ielts-r-001.json` → `ielts-r-130.json`) |
| Broken file (skip) | `/Users/tengda/Antigravity/IELTS/broken/ielts-r-121.json` |
| Script output dir | `/Users/tengda/Antigravity/IELTS/scripts/` |
| State file | `/Users/tengda/Antigravity/IELTS/scripts/migration_state.json` |

> **Working directory for all commands**: `/Users/tengda/Antigravity/toefl-2026/backend/`
> Always source the venv before running anything.

---

## Step 1 — Add IELTS Models to `models.py`

**File to modify**: `/Users/tengda/Antigravity/toefl-2026/backend/app/models/models.py`

Append the following **four new SQLAlchemy model classes** at the bottom of the file.
Do NOT touch existing models (User, TestItem, TestSession, etc.). Import `JSON` from
`sqlalchemy` (already available in the venv).

### IeltsPassage

```python
from sqlalchemy import JSON

class IeltsDifficulty(str, enum.Enum):
    HIGH   = 'high'
    MEDIUM = 'medium'
    LOW    = 'low'

class IeltsPosition(str, enum.Enum):
    P1 = 'P1'
    P2 = 'P2'
    P3 = 'P3'

class IeltsPassage(Base):
    """
    One row per IELTS Reading passage (one test set = 3 passages).
    Corresponds directly to one parsed JSON file.
    """
    __tablename__ = "ielts_passages"

    id                 = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id          = Column(String(20), unique=True, nullable=False)   # e.g. "ielts-r-001"
    source_file        = Column(String(255), nullable=True)                # original PDF filename
    position           = Column(Enum(IeltsPosition), nullable=False)       # P1 / P2 / P3
    difficulty         = Column(Enum(IeltsDifficulty), nullable=True)
    title              = Column(String(500), nullable=False)
    title_cn           = Column(String(500), nullable=True)
    time_allocation    = Column(String(50), nullable=True)
    has_paragraph_labels = Column(Boolean, default=False)
    paragraphs         = Column(JSON, nullable=False)   # list of {label, text}
    question_range_start = Column(Integer, nullable=True)
    question_range_end   = Column(Integer, nullable=True)
    needs_review       = Column(Boolean, default=True)
    parsed_at          = Column(DateTime(timezone=True), nullable=True)
    created_at         = Column(DateTime(timezone=True), server_default=func.now())
    updated_at         = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    question_groups    = relationship("IeltsQuestionGroup", back_populates="passage",
                                      cascade="all, delete-orphan")
```

### IeltsQuestionGroup

```python
class IeltsQuestionGroup(Base):
    """
    One row per question group within a passage (e.g., TFNG block, MCQ block).
    A passage usually has 2–3 groups.
    """
    __tablename__ = "ielts_question_groups"

    id            = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    passage_id    = Column(String, ForeignKey("ielts_passages.id"), nullable=False)
    group_type    = Column(String(50), nullable=False)   # TFNG, MCQ, HEADING_MATCHING, etc.
    instructions  = Column(Text, nullable=True)
    range_start   = Column(Integer, nullable=True)
    range_end     = Column(Integer, nullable=True)
    sort_order    = Column(Integer, default=0)           # position within passage

    passage       = relationship("IeltsPassage", back_populates="question_groups")
    questions     = relationship("IeltsQuestion", back_populates="group",
                                 cascade="all, delete-orphan")
```

### IeltsQuestion

```python
class IeltsQuestion(Base):
    """
    One row per individual question. Options stored as JSON for flexible
    support across all 14 IELTS question sub-types.
    """
    __tablename__ = "ielts_questions"

    id             = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id       = Column(String, ForeignKey("ielts_question_groups.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text  = Column(Text, nullable=True)
    options        = Column(JSON, nullable=True)      # list of {letter, text} or None
    answer         = Column(String(500), nullable=True)
    answer_source  = Column(String(50), nullable=True)  # "llm_generated" or "human"
    needs_review   = Column(Boolean, default=True)

    group          = relationship("IeltsQuestionGroup", back_populates="questions")
```

### IeltsMigrationLog (for idempotency tracking)

```python
class IeltsMigrationLog(Base):
    """
    Tracks which source JSON files have been migrated. Allows safe re-runs.
    """
    __tablename__ = "ielts_migration_log"

    source_id   = Column(String(20), primary_key=True)   # e.g. "ielts-r-001"
    status      = Column(String(20), default="done")     # "done" or "error"
    error_msg   = Column(Text, nullable=True)
    migrated_at = Column(DateTime(timezone=True), server_default=func.now())
```

---

## Step 2 — Create the DB Tables

After appending the models, run this one-liner from the venv to create the four new tables
without touching existing tables:

```bash
cd /Users/tengda/Antigravity/toefl-2026/backend
source venv/bin/activate
python -c "
import sys; sys.path.insert(0, '.')
from app.database.connection import engine, Base
from app.models.models import IeltsPassage, IeltsQuestionGroup, IeltsQuestion, IeltsMigrationLog
Base.metadata.create_all(bind=engine, checkfirst=True)
print('Tables created (or already existed).')
"
```

Verify success by checking the output line. If any `OperationalError` appears, fix it
before proceeding.

---

## Step 3 — Write the Migration Script

Create a new file at:
`/Users/tengda/Antigravity/IELTS/scripts/migrate_reading_to_db.py`

The script must:

1. Load all `.json` files from `/Users/tengda/Antigravity/IELTS/parsed/`
   using `os.listdir()` (never hardcode paths — smart quotes in filenames caused bugs before).
2. For each file, check `IeltsMigrationLog` — if `source_id` already exists with status `done`,
   skip silently.
3. Open a DB session, insert `IeltsPassage` → `IeltsQuestionGroup`(s) → `IeltsQuestion`(s)
   in one transaction.
4. On success, write a `IeltsMigrationLog` row with `status="done"`.
5. On exception, write `IeltsMigrationLog` row with `status="error"` and `error_msg=str(e)`,
   then continue to next file (do not abort the whole run).
6. Print a summary at the end: `N inserted, M skipped, K errors`.

### JSON → Model Field Mapping

| JSON field | Model field |
|---|---|
| `id` | `IeltsPassage.source_id` |
| `source_file` | `IeltsPassage.source_file` |
| `position` | `IeltsPassage.position` |
| `difficulty` | `IeltsPassage.difficulty` (default `None` if missing) |
| `title` | `IeltsPassage.title` |
| `title_cn` | `IeltsPassage.title_cn` |
| `time_allocation` | `IeltsPassage.time_allocation` |
| `passage.has_paragraph_labels` | `IeltsPassage.has_paragraph_labels` |
| `passage.paragraphs` | `IeltsPassage.paragraphs` (store as-is JSON) |
| `question_range[0]` | `IeltsPassage.question_range_start` |
| `question_range[1]` | `IeltsPassage.question_range_end` |
| `metadata.needs_review` | `IeltsPassage.needs_review` |
| `metadata.parsed_at` | `IeltsPassage.parsed_at` (parse ISO string → datetime) |
| `question_groups[i].type` | `IeltsQuestionGroup.group_type` |
| `question_groups[i].instructions` | `IeltsQuestionGroup.instructions` |
| `question_groups[i].range[0]` | `IeltsQuestionGroup.range_start` |
| `question_groups[i].range[1]` | `IeltsQuestionGroup.range_end` |
| `question_groups[i]` index | `IeltsQuestionGroup.sort_order` |
| `questions[j].number` | `IeltsQuestion.question_number` |
| `questions[j].text` | `IeltsQuestion.question_text` |
| `questions[j].options` | `IeltsQuestion.options` |
| `questions[j].answer` | `IeltsQuestion.answer` |
| `questions[j].answer_source` | `IeltsQuestion.answer_source` |

### `difficulty` value normalisation

The JSON has `"high"`, `"medium"`, some have `"次"` (medium in Chinese) or are missing.
Normalise:
- `"high"` or `"高"` → `IeltsDifficulty.HIGH`
- `"medium"` or `"次"` or `"中"` → `IeltsDifficulty.MEDIUM`
- `"low"` or `"低"` → `IeltsDifficulty.LOW`
- anything else or missing → `None` (nullable)

---

## Step 4 — Run the Migration Script

```bash
cd /Users/tengda/Antigravity/toefl-2026/backend
source venv/bin/activate
python /Users/tengda/Antigravity/IELTS/scripts/migrate_reading_to_db.py
```

Expected output should end with something like:
```
Migration complete: 129 inserted, 0 skipped, 0 errors.
```

If there are errors, inspect the `IeltsMigrationLog` table for `status='error'` rows:

```bash
python -c "
import sys; sys.path.insert(0, '.')
from app.database.connection import SessionLocal
from app.models.models import IeltsMigrationLog
db = SessionLocal()
errors = db.query(IeltsMigrationLog).filter_by(status='error').all()
for e in errors: print(e.source_id, e.error_msg)
db.close()
"
```

Fix the root cause and re-run — already-successful passages will be automatically skipped.

---

## Step 5 — Verify Row Counts

Run these verification checks after migration completes:

```bash
python -c "
import sys; sys.path.insert(0, '.')
from app.database.connection import SessionLocal
from app.models.models import IeltsPassage, IeltsQuestionGroup, IeltsQuestion
db = SessionLocal()
print('Passages:        ', db.query(IeltsPassage).count())
print('Question groups: ', db.query(IeltsQuestionGroup).count())
print('Questions:       ', db.query(IeltsQuestion).count())
db.close()
"
```

Expected ranges:
- **Passages**: 129
- **Question groups**: ~280–320 (typically 2–3 groups per passage)
- **Questions**: ~1,677 (129 passages × 13 questions average)

If any count is wildly off, check the error log (Step 4 command) and re-run.

---

## Step 6 — Housekeeping

Per the `python_housekeeping` skill (`/Users/tengda/Antigravity/.agent/skills/python_housekeeping/SKILL.md`):
- The migration script lives in `/IELTS/scripts/` — **do not delete it** (it is a permanent
  migration artefact, not a one-off temp script).
- The `migration_state.json` sidecar (if used) should remain next to the script.
- Do NOT delete the source JSON files in `/IELTS/parsed/` — they are the authoritative
  backup/archive.

---

## Known Pitfalls / Gotchas

| Issue | Fix |
|---|---|
| Smart apostrophe in filenames | Always use `os.listdir()`, never construct filenames manually |
| `question_range` is a list `[1, 13]` not two separate fields | Index it: `data["question_range"][0]` |
| `difficulty` field is sometimes missing from JSON | Use `data.get("difficulty")` and normalise |
| `parsed_at` is an ISO string | Parse with `datetime.fromisoformat()` — may need `.replace("+0800", "+08:00")` for some |
| SQLite JSON column | SQLAlchemy's `JSON` type works fine with SQLite — no special handling needed |
| `IeltsPosition` enum: JSON has `"P1"` as a string | Direct match — no normalisation needed |
| `check_same_thread=False` is set in connection.py | This is fine for SQLite single-thread migrations |

---

## What Comes After (Future Work — Do Not Act On)

Once Reading is migrated and confirmed, future agents can migrate:
- **Listening**: Same `IeltsQuestionGroup`/`IeltsQuestion` tables — add a new `IeltsListeningAudio`
  table linked to `IeltsPassage` via FK.
- **Writing**: A separate `IeltsWritingTask` table (prompt + stimulus image path + task type).
- **Speaking**: A separate `IeltsSpenkingPrompt` table (part 1/2/3 prompts + cue card content).

All under the same single database — no cross-database queries needed.

---

*End of briefing. The agent receiving this should execute Steps 1–6 in order
without asking the user for anything.*
