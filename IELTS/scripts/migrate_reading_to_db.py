#!/usr/bin/env python3
"""
IELTS Reading → DB Migration (Steps 2-5 all-in-one)
====================================================
Creates tables, migrates 129 parsed JSON files, and verifies row counts.
Idempotent: safe to re-run — skips already-migrated passages.

Run from:  /Users/tengda/Antigravity/toefl-2026/backend
Command:   source venv/bin/activate && python /Users/tengda/Antigravity/IELTS/scripts/migrate_reading_to_db.py
"""

import sys, os, json, uuid
from datetime import datetime

# --- Bootstrap path so app.* imports work ---
BACKEND_DIR = "/Users/tengda/Antigravity/toefl-2026/backend"
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from app.database.connection import engine, Base, SessionLocal
from app.models.models import (
    IeltsPassage, IeltsQuestionGroup, IeltsQuestion, IeltsMigrationLog,
    IeltsDifficulty, IeltsPosition,
)

# ── Config ──────────────────────────────────────────────────────────────────
PARSED_DIR = "/Users/tengda/Antigravity/IELTS/parsed"

# ── Step 2: Create tables ───────────────────────────────────────────────────
print("=" * 60)
print("STEP 2 — Creating IELTS tables (if not exist)...")
Base.metadata.create_all(bind=engine, checkfirst=True)
print("  ✓ Tables ready.\n")

# ── Helpers ─────────────────────────────────────────────────────────────────
DIFFICULTY_MAP = {
    "high": IeltsDifficulty.HIGH,
    "高":   IeltsDifficulty.HIGH,
    "medium": IeltsDifficulty.MEDIUM,
    "次":   IeltsDifficulty.MEDIUM,
    "中":   IeltsDifficulty.MEDIUM,
    "low":  IeltsDifficulty.LOW,
    "低":   IeltsDifficulty.LOW,
}

POSITION_MAP = {
    "P1": IeltsPosition.P1,
    "P2": IeltsPosition.P2,
    "P3": IeltsPosition.P3,
}

def parse_iso(s):
    """Parse ISO datetime string, handling +0800 → +08:00."""
    if s is None:
        return None
    # Fix timezone offset without colon (e.g. +0800 → +08:00)
    if len(s) >= 5 and s[-5] == '+' and ':' not in s[-5:]:
        s = s[:-2] + ':' + s[-2:]
    elif len(s) >= 5 and s[-5] == '-' and ':' not in s[-5:]:
        s = s[:-2] + ':' + s[-2:]
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


# ── Step 3+4: Migrate ──────────────────────────────────────────────────────
print("=" * 60)
print("STEP 3+4 — Migrating JSON files...\n")

files = sorted([f for f in os.listdir(PARSED_DIR) if f.endswith(".json")])
print(f"  Found {len(files)} JSON files in {PARSED_DIR}\n")

inserted = 0
skipped = 0
errors = 0

for fname in files:
    source_id = fname.replace(".json", "")
    fpath = os.path.join(PARSED_DIR, fname)

    db = SessionLocal()
    try:
        # Check idempotency
        existing = db.query(IeltsMigrationLog).filter_by(source_id=source_id, status="done").first()
        if existing:
            skipped += 1
            db.close()
            continue

        # Load JSON
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Build IeltsPassage
        diff_raw = data.get("difficulty")
        difficulty_enum = DIFFICULTY_MAP.get(diff_raw.lower() if diff_raw else "", None) if diff_raw else None

        position_enum = POSITION_MAP.get(data.get("position", "P1"), IeltsPosition.P1)

        qr = data.get("question_range", [None, None])
        passage_data = data.get("passage", {})
        metadata = data.get("metadata", {})

        passage = IeltsPassage(
            id=str(uuid.uuid4()),
            source_id=data["id"],
            source_file=data.get("source_file"),
            position=position_enum,
            difficulty=difficulty_enum,
            title=data.get("title", "Untitled"),
            title_cn=data.get("title_cn"),
            time_allocation=data.get("time_allocation"),
            has_paragraph_labels=passage_data.get("has_paragraph_labels", False),
            paragraphs=passage_data.get("paragraphs", []),
            question_range_start=qr[0] if qr else None,
            question_range_end=qr[1] if len(qr) > 1 else None,
            needs_review=metadata.get("needs_review", True),
            parsed_at=parse_iso(metadata.get("parsed_at")),
        )
        db.add(passage)

        # Build question groups and questions
        for idx, grp_data in enumerate(data.get("question_groups", [])):
            grp_range = grp_data.get("range", [None, None])
            group = IeltsQuestionGroup(
                id=str(uuid.uuid4()),
                passage_id=passage.id,
                group_type=grp_data.get("type", "UNKNOWN"),
                instructions=grp_data.get("instructions"),
                range_start=grp_range[0] if grp_range else None,
                range_end=grp_range[1] if len(grp_range) > 1 else None,
                sort_order=idx,
            )
            db.add(group)

            for q_data in grp_data.get("questions", []):
                question = IeltsQuestion(
                    id=str(uuid.uuid4()),
                    group_id=group.id,
                    question_number=q_data.get("number", 0),
                    question_text=q_data.get("text"),
                    options=q_data.get("options"),
                    answer=q_data.get("answer"),
                    answer_source=q_data.get("answer_source"),
                    needs_review=True,
                )
                db.add(question)

        # Log success
        db.add(IeltsMigrationLog(source_id=source_id, status="done"))
        db.commit()
        inserted += 1
        if inserted % 20 == 0:
            print(f"    ... {inserted} inserted so far")

    except Exception as e:
        db.rollback()
        # Log error
        try:
            db.add(IeltsMigrationLog(source_id=source_id, status="error", error_msg=str(e)[:500]))
            db.commit()
        except Exception:
            pass
        errors += 1
        print(f"  ✗ ERROR on {fname}: {e}")
    finally:
        db.close()

print(f"\n  Migration complete: {inserted} inserted, {skipped} skipped, {errors} errors.\n")

# ── Step 5: Verify ─────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 5 — Verification\n")
db = SessionLocal()
p_count = db.query(IeltsPassage).count()
g_count = db.query(IeltsQuestionGroup).count()
q_count = db.query(IeltsQuestion).count()
db.close()

print(f"  Passages:         {p_count}  (expected: 129)")
print(f"  Question groups:  {g_count}  (expected: ~280-320)")
print(f"  Questions:        {q_count}  (expected: ~1677)")

# Check for migration errors
db = SessionLocal()
err_rows = db.query(IeltsMigrationLog).filter_by(status="error").all()
if err_rows:
    print(f"\n  ⚠ {len(err_rows)} error(s) in migration log:")
    for r in err_rows:
        print(f"    - {r.source_id}: {r.error_msg}")
else:
    print(f"\n  ✓ No errors in migration log.")
db.close()

# Final verdict
if p_count == 129 and errors == 0:
    print("\n" + "=" * 60)
    print("✅ ALL STEPS PASSED — IELTS Reading item bank ready.")
    print("=" * 60)
else:
    print("\n" + "=" * 60)
    print(f"⚠  Check needed: expected 129 passages, got {p_count}. Errors: {errors}")
    print("=" * 60)
