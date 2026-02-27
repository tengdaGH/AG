#!/usr/bin/env python3
"""
migrate_staging_v2.py
=====================
Migrates the 617 staged parsed_v2 IELTS Reading items into the existing
IELTS item bank tables (IeltsPassage, IeltsQuestionGroup, IeltsQuestion).

Source schema (parsed_v2 / staging):
  {
    "id": "ielts-r-0001",
    "slug": "...",
    "title": "...",
    "page_range": [21, 25],
    "raw_answer_key": {"1": "viii", ...},
    "content": {
      "title": "...",
      "has_paragraph_labels": true,
      "paragraphs": [{"label": "A", "content": "..."}, ...]
    },
    "questions": {
      "question_groups": [
        {
          "type": "MATCHING_HEADINGS",
          "instruction": "...",
          "questions": [
            {"number": 1, "text": "...", "answer": "viii", "options": [...]}
          ]
        }
      ],
      "parsed_total_questions": 13
    },
    "processed_at": "2026-02-26T00:39:06.945341"
  }

Run from:  /Users/tengda/Antigravity/toefl-2026/backend
Command:   source venv/bin/activate && python /Users/tengda/Antigravity/IELTS/scripts/migrate_staging_v2.py
"""

import sys, os, json, uuid
from datetime import datetime

# --- Bootstrap backend path ---
BACKEND_DIR = "/Users/tengda/Antigravity/toefl-2026/backend"
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from app.database.connection import engine, Base, SessionLocal
from app.models.models import (
    IeltsPassage, IeltsQuestionGroup, IeltsQuestion, IeltsMigrationLog,
    IeltsPosition,
)

# ── Config ───────────────────────────────────────────────────────────────────
STAGING_DIR = "/Users/tengda/Antigravity/IELTS/staging"

# ── Ensure tables exist ──────────────────────────────────────────────────────
print("=" * 60)
print("Ensuring IELTS tables exist...")
Base.metadata.create_all(bind=engine, checkfirst=True)
print("  ✓ Tables ready.\n")

# ── Helpers ──────────────────────────────────────────────────────────────────
def parse_iso(s):
    """Parse ISO datetime string gracefully."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def infer_position(page_range):
    """
    Infer IELTS position (P1/P2/P3) from page range.
    The source PDF has ~3 passages per test set, so we use a rough heuristic:
    every group of 3 consecutive passages cycles P1→P2→P3.
    However, page_range gives us the actual PDF page numbers so we cannot
    infer test-set position reliably without more metadata.
    Default all new items to P1 with needs_review=True so human can correct.
    """
    return IeltsPosition.P1


# ── Migration ────────────────────────────────────────────────────────────────
print("=" * 60)
print(f"Migrating from staging: {STAGING_DIR}\n")

files = sorted(f for f in os.listdir(STAGING_DIR) if f.endswith(".json"))
print(f"  Found {len(files)} files to process.\n")

inserted = 0
skipped  = 0
errors   = 0

for fname in files:
    source_id = fname.replace(".json", "")
    fpath = os.path.join(STAGING_DIR, fname)

    db = SessionLocal()
    try:
        # Idempotency: skip if already migrated
        existing_log = db.query(IeltsMigrationLog).filter_by(
            source_id=source_id, status="done"
        ).first()
        if existing_log:
            skipped += 1
            db.close()
            continue

        # Extra safety: skip if source_id already in ielts_passages
        existing_passage = db.query(IeltsPassage).filter_by(
            source_id=source_id
        ).first()
        if existing_passage:
            db.add(IeltsMigrationLog(source_id=source_id, status="done",
                                     error_msg="skipped: already in ielts_passages"))
            db.commit()
            skipped += 1
            db.close()
            continue

        # Load JSON
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        content   = data.get("content", {})
        questions = data.get("questions", {})
        groups    = questions.get("question_groups", [])

        # -- IeltsPassage --
        page_range = data.get("page_range", [None, None])
        passage = IeltsPassage(
            id=str(uuid.uuid4()),
            source_id=data["id"],
            source_file=None,           # not tracked in parsed_v2 schema
            position=infer_position(page_range),
            difficulty=None,            # not tracked in parsed_v2 schema
            title=data.get("title", "Untitled"),
            title_cn=None,
            time_allocation=None,
            has_paragraph_labels=content.get("has_paragraph_labels", False),
            paragraphs=content.get("paragraphs", []),
            question_range_start=None,
            question_range_end=None,
            needs_review=True,
            parsed_at=parse_iso(data.get("processed_at")),
        )
        db.add(passage)

        # -- IeltsQuestionGroup + IeltsQuestion --
        q_range_start = None
        q_range_end   = None

        for idx, grp in enumerate(groups):
            qs = grp.get("questions", [])
            numbers = [q.get("number") for q in qs if q.get("number") is not None]
            grp_start = min(numbers) if numbers else None
            grp_end   = max(numbers) if numbers else None

            # Track overall question range for passage
            if grp_start is not None:
                q_range_start = min(grp_start, q_range_start or grp_start)
            if grp_end is not None:
                q_range_end = max(grp_end, q_range_end or grp_end)

            group = IeltsQuestionGroup(
                id=str(uuid.uuid4()),
                passage_id=passage.id,
                group_type=grp.get("type", "UNKNOWN"),
                instructions=grp.get("instruction"),   # Note: parsed_v2 uses 'instruction' (singular)
                range_start=grp_start,
                range_end=grp_end,
                sort_order=idx,
            )
            db.add(group)

            for q in qs:
                question = IeltsQuestion(
                    id=str(uuid.uuid4()),
                    group_id=group.id,
                    question_number=q.get("number", 0),
                    question_text=q.get("text"),
                    options=q.get("options"),
                    answer=q.get("answer"),
                    answer_source="llm_generated",
                    needs_review=True,
                )
                db.add(question)

        # Update passage with overall question range
        passage.question_range_start = q_range_start
        passage.question_range_end   = q_range_end

        # Log success
        db.add(IeltsMigrationLog(source_id=source_id, status="done"))
        db.commit()
        inserted += 1
        if inserted % 50 == 0:
            print(f"    ... {inserted} inserted so far")

    except Exception as e:
        db.rollback()
        try:
            db.add(IeltsMigrationLog(
                source_id=source_id, status="error", error_msg=str(e)[:500]
            ))
            db.commit()
        except Exception:
            pass
        errors += 1
        print(f"  ✗ ERROR on {fname}: {e}")
    finally:
        db.close()

print(f"\n  Migration complete: {inserted} inserted, {skipped} skipped, {errors} errors.\n")

# ── Verification ─────────────────────────────────────────────────────────────
print("=" * 60)
print("Verification\n")
db = SessionLocal()
p_count = db.query(IeltsPassage).count()
g_count = db.query(IeltsQuestionGroup).count()
q_count = db.query(IeltsQuestion).count()
# Count just the v2 batch (4-digit IDs)
v2_count = db.query(IeltsPassage).filter(
    IeltsPassage.source_id.like("ielts-r-0%")
).count()
err_rows = db.query(IeltsMigrationLog).filter_by(status="error").all()
db.close()

expected_total = 129 + inserted  # old 3-digit + new 4-digit
print(f"  Total passages in DB   : {p_count}  (expected ~{expected_total})")
print(f"  v2 passages (4-digit)  : {v2_count}  (expected {inserted})")
print(f"  Total question groups  : {g_count}")
print(f"  Total questions        : {q_count}")

if err_rows:
    print(f"\n  ⚠  {len(err_rows)} error(s) in migration log:")
    for r in err_rows[:10]:
        print(f"    - {r.source_id}: {r.error_msg}")
else:
    print(f"\n  ✓ No errors in migration log.")

print("\n" + "=" * 60)
if errors == 0:
    print(f"✅ ALL DONE — {inserted} new IELTS Reading passages imported.")
else:
    print(f"⚠  Completed with {errors} error(s). Check log above.")
print("=" * 60)
