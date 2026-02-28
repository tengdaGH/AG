#!/usr/bin/env python3
"""
import_itembank.py – ETL script to merge JSON item-bank files into the SQLite database.

Usage:
    cd /Users/tengda/Antigravity/toefl-2026/backend
    python -m app.scripts.import_itembank             # live import
    python -m app.scripts.import_itembank --dry-run    # validate only, no writes
"""
import argparse
import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ── Bootstrap the app so SQLAlchemy models are importable ──
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.database.connection import SessionLocal, engine, Base
from app.models.models import TestItem, TestItemQuestion, SectionType, CEFRLevel, TaskType

# ── Directories ──
DATA_DIR = Path(__file__).resolve().parents[3] / "data"

# ── Mapping: filename → (section, task_type) ──
FILE_MAP: dict[str, tuple[SectionType, TaskType]] = {
    "read-academic-passage-passages.json":    (SectionType.READING,  TaskType.READ_ACADEMIC_PASSAGE),
    "read-in-daily-life-passages.json":       (SectionType.READING,  TaskType.READ_IN_DAILY_LIFE),
    "complete-the-words-passages.json":       (SectionType.READING,  TaskType.COMPLETE_THE_WORDS),
    "complete-the-words-cefr-sets.json":      (SectionType.READING,  TaskType.COMPLETE_THE_WORDS),
    "toefl-2026-complete-the-words.json":     (SectionType.READING,  TaskType.COMPLETE_THE_WORDS),
    "build-a-sentence-sets.json":             (SectionType.WRITING,  TaskType.BUILD_A_SENTENCE),
    "toefl-2026-academic-discussion.json":    (SectionType.WRITING,  TaskType.WRITE_ACADEMIC_DISCUSSION),
    "writing-academic-discussion-prompts.json": (SectionType.WRITING, TaskType.WRITE_ACADEMIC_DISCUSSION),
    "toefl-2026-write-email.json":            (SectionType.WRITING,  TaskType.WRITE_AN_EMAIL),
    "writing-email-prompts.json":             (SectionType.WRITING,  TaskType.WRITE_AN_EMAIL),
    "toefl-2026-take-interview.json":         (SectionType.SPEAKING, TaskType.TAKE_AN_INTERVIEW),
    "ets_official_reading_academic.json":     (SectionType.READING,  TaskType.READ_ACADEMIC_PASSAGE),
    "ets_official_reading_daily_life.json":   (SectionType.READING,  TaskType.READ_IN_DAILY_LIFE),
    "ets_official_reading_ctest.json":        (SectionType.READING,  TaskType.COMPLETE_THE_WORDS),
    "ets_official_listening_cr.json":         (SectionType.LISTENING, TaskType.LISTEN_CHOOSE_RESPONSE),
    "ets_official_listening_passages.json":   (SectionType.LISTENING, TaskType.LISTEN_CONVERSATION),
    "ets_official_writing_bas.json":          (SectionType.WRITING,  TaskType.BUILD_A_SENTENCE),
    "ets_official_writing_email.json":        (SectionType.WRITING,  TaskType.WRITE_AN_EMAIL),
    "ets_official_writing_wad.json":          (SectionType.WRITING,  TaskType.WRITE_ACADEMIC_DISCUSSION),
    "ets_official_speaking_repeat.json":      (SectionType.SPEAKING, TaskType.LISTEN_AND_REPEAT),
    "ets_official_speaking_interview.json":   (SectionType.SPEAKING, TaskType.TAKE_AN_INTERVIEW),
}


# ── Normalised import record ──
@dataclass
class ImportRecord:
    source_file: str
    source_id: str
    section: SectionType
    task_type: TaskType
    target_level: CEFRLevel
    prompt_content: str          # JSON-serialised payload
    media_url: Optional[str] = None
    errors: list[str] = field(default_factory=list)


# ── CEFR helpers ──
CEFR_MAP = {v.value: v for v in CEFRLevel}

def resolve_cefr(raw: Optional[str]) -> CEFRLevel:
    """Best-effort CEFR resolution; defaults to B2."""
    if not raw:
        return CEFRLevel.B2
    raw = raw.upper().strip()
    if raw in CEFR_MAP:
        return CEFR_MAP[raw]
    # Handle labels like "B2 — Routing module"
    for k in CEFR_MAP:
        if raw.startswith(k):
            return CEFR_MAP[k]
    return CEFRLevel.B2


DIFFICULTY_TO_CEFR = {
    "Easier": CEFRLevel.B2,
    "Harder": CEFRLevel.C1,
}


# ═══════════════════════════════════════════════════════════════
# Parsers – one per JSON shape
# ═══════════════════════════════════════════════════════════════

def parse_academic_passages(data: dict, filename: str, section: SectionType, task_type: TaskType) -> list[ImportRecord]:
    """Shape: {meta, sets: {DOMAIN: {label, passages: [{id, title, ...}]}}}"""
    records: list[ImportRecord] = []
    for _domain_key, domain in data.get("sets", {}).items():
        for p in domain.get("passages", []):
            cefr = DIFFICULTY_TO_CEFR.get(p.get("difficulty"), CEFRLevel.B2)
            rec = ImportRecord(
                source_file=filename, source_id=p["id"],
                section=section, task_type=task_type,
                target_level=cefr,
                prompt_content=json.dumps(p, ensure_ascii=False),
            )
            # Validate
            if not p.get("content"):
                rec.errors.append("Empty passage content")
            qs = p.get("questions", [])
            if len(qs) < 2:
                rec.errors.append(f"Only {len(qs)} questions (need ≥2)")
            for q in qs:
                if len(q.get("options", [])) < 2:
                    rec.errors.append(f"Question has <2 options")
            records.append(rec)
    return records


def parse_daily_life(data: dict, filename: str, section: SectionType, task_type: TaskType) -> list[ImportRecord]:
    """Shape: {meta, sets: {D01: {label, passages: [{id, type, ...}]}}}"""
    records: list[ImportRecord] = []
    for _set_key, s in data.get("sets", {}).items():
        for p in s.get("passages", []):
            cefr = resolve_cefr(p.get("difficulty"))
            rec = ImportRecord(
                source_file=filename, source_id=p["id"],
                section=section, task_type=task_type,
                target_level=cefr,
                prompt_content=json.dumps(p, ensure_ascii=False),
            )
            # Some daily-life passages use "messages" (chat format) instead of "content"
            if not p.get("content") and not p.get("messages"):
                rec.errors.append("Empty passage content (no 'content' or 'messages')")
            records.append(rec)
    return records


def parse_ctest_passages(data: dict, filename: str, section: SectionType, task_type: TaskType) -> list[ImportRecord]:
    """Shape: {meta, passages: [list of passage objects]}"""
    records: list[ImportRecord] = []
    for p in data.get("passages", []):
        cefr = resolve_cefr(p.get("tier") or p.get("difficulty") or p.get("level"))
        sid = p.get("id", p.get("passageId", ""))
        rec = ImportRecord(
            source_file=filename, source_id=str(sid),
            section=section, task_type=task_type,
            target_level=cefr,
            prompt_content=json.dumps(p, ensure_ascii=False),
        )
        records.append(rec)
    return records


def _apply_c_test_truncation(raw_item: dict) -> dict:
    """Apply deterministic C-test truncation to a raw passage item.

    Takes an item with un-truncated 'text' and 'hints', and returns a new dict
    with truncated text, 10 fill-in questions, and preserved hints.
    Uses the same algorithm as c_test_generator._build_c_test.
    """
    import re as _re

    raw_text = raw_item.get("text", "")
    if not raw_text:
        return raw_item

    # Split first sentence from rest
    m = _re.search(r'^([A-Z].*?[.!?])\s+(.*)$', raw_text, _re.DOTALL)
    if m:
        first_sentence, rest_text = m.group(1), m.group(2)
    else:
        words = raw_text.split()
        first_sentence = " ".join(words[:10]) + "."
        rest_text = " ".join(words[10:])

    tokens = _re.findall(r"[\w']+|[.,!?;:]", rest_text)
    final_words: list[str] = []
    questions: list[dict] = []
    word_idx = 0

    for token in tokens:
        if _re.match(r'^[.,!?;:]$', token):
            if final_words:
                final_words[-1] += token
            else:
                final_words.append(token)
            continue

        word_idx += 1

        if word_idx % 2 == 0 and len(questions) < 10 and len(token) >= 2:
            half = len(token) // 2
            visible = token[:half]
            hidden = token[half:]
            truncated = visible + "_" * len(hidden)
            final_words.append(truncated)
            questions.append({
                "question_num": len(questions) + 1,
                "text": truncated,
                "correct_answer": token,
            })
        else:
            final_words.append(token)

    full_text = first_sentence + " " + " ".join(final_words)
    full_text = _re.sub(r'\s+([.,!?;:])', r'\1', full_text)

    result = {
        "id": raw_item.get("id", ""),
        "type": "Complete the Words",
        "title": first_sentence[:60] + "..." if len(first_sentence) > 60 else first_sentence,
        "text": full_text,
        "questions": questions,
    }
    if raw_item.get("hints"):
        result["hints"] = raw_item["hints"]
    return result


def parse_cefr_sets(data: dict, filename: str, section: SectionType, task_type: TaskType) -> list[ImportRecord]:
    """Shape: {meta, sets: {A1: [list of passage objects], A2: [...], ...}}"""
    records: list[ImportRecord] = []
    is_ctest = (task_type == TaskType.COMPLETE_THE_WORDS)

    for cefr_key, items in data.get("sets", {}).items():
        cefr = resolve_cefr(cefr_key)
        if isinstance(items, dict):
            # {label: ..., passages/sentences: [...]}
            actual_items = items.get("passages") or items.get("sentences") or items.get("questions") or []
        elif isinstance(items, list):
            actual_items = items
        else:
            continue
        for p in actual_items:
            sid = p.get("id", "")
            # Apply C-test truncation for Complete the Words items
            payload = _apply_c_test_truncation(p) if is_ctest else p
            rec = ImportRecord(
                source_file=filename, source_id=str(sid),
                section=section, task_type=task_type,
                target_level=cefr,
                prompt_content=json.dumps(payload, ensure_ascii=False),
            )
            records.append(rec)
    return records


def parse_build_sentence(data: dict, filename: str, section: SectionType, task_type: TaskType) -> list[ImportRecord]:
    """Shape: {meta, sets: {A1: {label, sentences: [{id, fragments, ...}]}, ...}}"""
    records: list[ImportRecord] = []
    for cefr_key, level_data in data.get("sets", {}).items():
        cefr = resolve_cefr(cefr_key)
        sentences = level_data.get("sentences", []) if isinstance(level_data, dict) else []
        for s in sentences:
            sid = s.get("id", "")
            rec = ImportRecord(
                source_file=filename, source_id=f"{cefr_key}-{sid}",
                section=section, task_type=task_type,
                target_level=cefr,
                prompt_content=json.dumps(s, ensure_ascii=False),
            )
            if not s.get("fragments"):
                rec.errors.append("No fragments in sentence")
            records.append(rec)
    return records


def parse_flat_prompts(data: dict, key: str, filename: str, section: SectionType, task_type: TaskType) -> list[ImportRecord]:
    """Shape: {meta, prompts|questions: [flat list]}"""
    records: list[ImportRecord] = []
    for p in data.get(key, []):
        sid = p.get("id", "")
        cefr = resolve_cefr(p.get("level") or p.get("difficulty"))
        rec = ImportRecord(
            source_file=filename, source_id=str(sid),
            section=section, task_type=task_type,
            target_level=cefr,
            prompt_content=json.dumps(p, ensure_ascii=False),
        )
        records.append(rec)
    return records


def parse_interview(data: dict, filename: str, section: SectionType, task_type: TaskType) -> list[ImportRecord]:
    """Shape: {meta, sets: [list of interview set objects]}"""
    records: list[ImportRecord] = []
    for s in data.get("sets", []):
        sid = s.get("id", "")
        cefr = resolve_cefr(s.get("level") or s.get("difficulty"))
        rec = ImportRecord(
            source_file=filename, source_id=str(sid),
            section=section, task_type=task_type,
            target_level=cefr,
            prompt_content=json.dumps(s, ensure_ascii=False),
        )
        qs = s.get("questions", [])
        if len(qs) < 1:
            rec.errors.append("Interview set has no questions")
        records.append(rec)
    return records


def parse_ets_list(data: dict, filename: str, section: SectionType, task_type: TaskType) -> list[ImportRecord]:
    """Generic parser for ETS official JSONs generated by parse_ets_pdfs.py"""
    records: list[ImportRecord] = []
    
    items = []
    if "sets" in data and "ETS" in data["sets"]:
        items = data["sets"]["ETS"].get("passages", [])
    elif "passages" in data:
        items = data["passages"]
    elif "items" in data:
        items = data["items"]
    elif "prompts" in data:
        items = data["prompts"]
    elif "interviews" in data:
        items = data["interviews"]
        
    for item in items:
        # Module routing determines CEFR: M1 -> B2, M2 -> C1
        cefr = CEFRLevel.C1 if "-M2-" in item.get("id", "") else CEFRLevel.B2
        rec = ImportRecord(
            source_file=filename, source_id=item["id"],
            section=section, task_type=task_type,
            target_level=cefr,
            prompt_content=json.dumps(item, ensure_ascii=False),
        )
        records.append(rec)
    return records


# ═══════════════════════════════════════════════════════════════
# Router – dispatch filename → parser
# ═══════════════════════════════════════════════════════════════

def parse_file(filename: str, data: dict, section: SectionType, task_type: TaskType) -> list[ImportRecord]:
    if filename.startswith("ets_official_"):
        return parse_ets_list(data, filename, section, task_type)
    elif filename == "read-academic-passage-passages.json":
        return parse_academic_passages(data, filename, section, task_type)
    elif filename == "read-in-daily-life-passages.json":
        return parse_daily_life(data, filename, section, task_type)
    elif filename in ("complete-the-words-passages.json", "toefl-2026-complete-the-words.json"):
        return parse_ctest_passages(data, filename, section, task_type)
    elif filename == "complete-the-words-cefr-sets.json":
        return parse_cefr_sets(data, filename, section, task_type)
    elif filename == "build-a-sentence-sets.json":
        return parse_build_sentence(data, filename, section, task_type)
    elif filename == "toefl-2026-take-interview.json":
        return parse_interview(data, filename, section, task_type)
    elif filename in (
        "toefl-2026-academic-discussion.json",
        "toefl-2026-write-email.json",
    ):
        return parse_flat_prompts(data, "questions", filename, section, task_type)
    elif filename in (
        "writing-academic-discussion-prompts.json",
        "writing-email-prompts.json",
    ):
        return parse_flat_prompts(data, "prompts", filename, section, task_type)
    else:
        print(f"  ⚠ No parser for {filename}, skipping.")
        return []


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Import JSON item bank into SQLite")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, no writes")
    args = parser.parse_args()

    # Ensure tables exist (adds new columns via create_all for fresh DBs;
    # for existing DBs, we ALTER below)
    Base.metadata.create_all(bind=engine)

    # Attempt to add new columns if they don't exist (SQLite ALTER TABLE)
    from sqlalchemy import inspect as sa_inspect, text
    insp = sa_inspect(engine)
    existing_cols = {c["name"] for c in insp.get_columns("test_items")}
    with engine.begin() as conn:
        if "task_type" not in existing_cols:
            conn.execute(text('ALTER TABLE test_items ADD COLUMN task_type VARCHAR(50)'))
        if "source_file" not in existing_cols:
            conn.execute(text('ALTER TABLE test_items ADD COLUMN source_file VARCHAR(255)'))
        if "source_id" not in existing_cols:
            conn.execute(text('ALTER TABLE test_items ADD COLUMN source_id VARCHAR(100)'))

    db = SessionLocal()

    # Build dedup dict from existing rows
    existing = {}
    for item in db.query(TestItem).filter(
        TestItem.source_file.isnot(None), TestItem.source_id.isnot(None)
    ).all():
        existing[(item.source_file, item.source_id)] = item

    summary: list[dict] = []

    for filename, (section, task_type) in FILE_MAP.items():
        filepath = DATA_DIR / filename
        if not filepath.exists():
            print(f"  ✗ {filename} not found, skipping.")
            summary.append({"file": filename, "parsed": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0, "status": "NOT_FOUND"})
            continue

        data = json.loads(filepath.read_text(encoding="utf-8"))
        records = parse_file(filename, data, section, task_type)

        inserted = 0
        updated = 0
        skipped = 0
        error_count = 0

        for rec in records:
            if rec.errors:
                error_count += 1
                print(f"  ⚠ {filename}/{rec.source_id}: {', '.join(rec.errors)}")
                continue

            key = (rec.source_file, rec.source_id)
            if key in existing:
                if not args.dry_run:
                    from sqlalchemy.orm.attributes import flag_modified
                    existing_item = existing[key]
                    
                    try:
                        old_pc = json.loads(existing_item.prompt_content)
                        new_pc = json.loads(rec.prompt_content)
                        
                        if "audio_path" in old_pc:
                            new_pc["audio_path"] = old_pc["audio_path"]
                        
                        existing_item.prompt_content = json.dumps(new_pc, ensure_ascii=False)
                        existing_item.section = rec.section
                        existing_item.task_type = rec.task_type
                        existing_item.target_level = rec.target_level
                        
                        flag_modified(existing_item, "prompt_content")
                        
                        target_tasks = [TaskType.COMPLETE_THE_WORDS, TaskType.READ_ACADEMIC_PASSAGE, TaskType.READ_IN_DAILY_LIFE, TaskType.LISTEN_CHOOSE_RESPONSE, TaskType.LISTEN_ACADEMIC_TALK, TaskType.LISTEN_ANNOUNCEMENT, TaskType.LISTEN_CONVERSATION]
                        cr_tasks = {TaskType.WRITE_AN_EMAIL: 4, TaskType.WRITE_ACADEMIC_DISCUSSION: 5, TaskType.TAKE_AN_INTERVIEW: 5, TaskType.LISTEN_AND_REPEAT: 4}
                        
                        db.query(TestItemQuestion).filter(TestItemQuestion.test_item_id == existing_item.id).delete()
                        if existing_item.task_type in target_tasks:
                            for idx, q in enumerate(new_pc.get("questions", [])):
                                q_num = q.get("question_num") or q.get("number") or (idx + 1)
                                ans = q.get("correct_answer")
                                if ans is not None:
                                    db.add(TestItemQuestion(id=str(uuid.uuid4()), test_item_id=existing_item.id, question_number=q_num, question_text=q.get("question") or q.get("text"), question_audio_url=q.get("audio_path") or q.get("audio_url"), replay_audio_url=q.get("replay_audio_path") or q.get("replay_audio_url"), correct_answer=str(ans).strip(), options=q.get("options"), irt_difficulty=0.0, irt_discrimination=1.0, exposure_count=0, is_active=True))
                        elif existing_item.task_type == TaskType.TAKE_AN_INTERVIEW:
                            for idx, q in enumerate(new_pc.get("questions", [])):
                                db.add(TestItemQuestion(id=str(uuid.uuid4()), test_item_id=existing_item.id, question_number=q.get("number") or (idx+1), question_text=q.get("text", ""), question_audio_url=q.get("audio_url") or q.get("audioUrl"), correct_answer="", is_constructed_response=True, max_score=cr_tasks[existing_item.task_type], irt_difficulty=0.0, irt_discrimination=1.0, exposure_count=0, is_active=True))
                        elif existing_item.task_type == TaskType.LISTEN_AND_REPEAT:
                            for idx, s in enumerate(new_pc.get("sentences", [])):
                                db.add(TestItemQuestion(id=str(uuid.uuid4()), test_item_id=existing_item.id, question_number=idx+1, question_text=s.get("text", ""), question_audio_url=s.get("audio_url") or s.get("audioUrl"), correct_answer="", is_constructed_response=True, max_score=cr_tasks[existing_item.task_type], irt_difficulty=0.0, irt_discrimination=1.0, exposure_count=0, is_active=True))
                        elif existing_item.task_type in cr_tasks:
                            q_text = new_pc.get("scenario") or new_pc.get("professor_prompt") or new_pc.get("title") or ""
                            db.add(TestItemQuestion(id=str(uuid.uuid4()), test_item_id=existing_item.id, question_number=1, question_text=q_text, correct_answer="", is_constructed_response=True, max_score=cr_tasks[existing_item.task_type], irt_difficulty=0.0, irt_discrimination=1.0, exposure_count=0, is_active=True))
                    except json.JSONDecodeError:
                        pass
                
                updated += 1
                continue

            if not args.dry_run:
                item = TestItem(
                    id=str(uuid.uuid4()),
                    section=rec.section,
                    task_type=rec.task_type,
                    target_level=rec.target_level,
                    prompt_content=rec.prompt_content,
                    media_url=rec.media_url,
                    is_active=True,
                    version=1,
                    generated_by_model="JSON-Import",
                    generation_notes=f"Imported from {rec.source_file}",
                    source_file=rec.source_file,
                    source_id=rec.source_id,
                )
                
                target_tasks = [TaskType.COMPLETE_THE_WORDS, TaskType.READ_ACADEMIC_PASSAGE, TaskType.READ_IN_DAILY_LIFE, TaskType.LISTEN_CHOOSE_RESPONSE, TaskType.LISTEN_ACADEMIC_TALK, TaskType.LISTEN_ANNOUNCEMENT, TaskType.LISTEN_CONVERSATION]
                cr_tasks = {TaskType.WRITE_AN_EMAIL: 4, TaskType.WRITE_ACADEMIC_DISCUSSION: 5, TaskType.TAKE_AN_INTERVIEW: 5, TaskType.LISTEN_AND_REPEAT: 4}
                
                try:
                    pc = json.loads(item.prompt_content)
                    if item.task_type in target_tasks:
                        for idx, q in enumerate(pc.get("questions", [])):
                            q_num = q.get("question_num") or q.get("number") or (idx + 1)
                            ans = q.get("correct_answer")
                            if ans is not None:
                                db.add(TestItemQuestion(id=str(uuid.uuid4()), test_item_id=item.id, question_number=q_num, question_text=q.get("question") or q.get("text"), question_audio_url=q.get("audio_path") or q.get("audio_url"), replay_audio_url=q.get("replay_audio_path") or q.get("replay_audio_url"), correct_answer=str(ans).strip(), options=q.get("options"), irt_difficulty=0.0, irt_discrimination=1.0, exposure_count=0, is_active=True))
                    elif item.task_type == TaskType.TAKE_AN_INTERVIEW:
                        for idx, q in enumerate(pc.get("questions", [])):
                            db.add(TestItemQuestion(id=str(uuid.uuid4()), test_item_id=item.id, question_number=q.get("number") or (idx+1), question_text=q.get("text", ""), question_audio_url=q.get("audio_url") or q.get("audioUrl"), correct_answer="", is_constructed_response=True, max_score=cr_tasks[item.task_type], irt_difficulty=0.0, irt_discrimination=1.0, exposure_count=0, is_active=True))
                    elif item.task_type == TaskType.LISTEN_AND_REPEAT:
                        for idx, s in enumerate(pc.get("sentences", [])):
                            db.add(TestItemQuestion(id=str(uuid.uuid4()), test_item_id=item.id, question_number=idx+1, question_text=s.get("text", ""), question_audio_url=s.get("audio_url") or s.get("audioUrl"), correct_answer="", is_constructed_response=True, max_score=cr_tasks[item.task_type], irt_difficulty=0.0, irt_discrimination=1.0, exposure_count=0, is_active=True))
                    elif item.task_type in cr_tasks:
                        q_text = pc.get("scenario") or pc.get("professor_prompt") or pc.get("title") or ""
                        db.add(TestItemQuestion(id=str(uuid.uuid4()), test_item_id=item.id, question_number=1, question_text=q_text, correct_answer="", is_constructed_response=True, max_score=cr_tasks[item.task_type], irt_difficulty=0.0, irt_discrimination=1.0, exposure_count=0, is_active=True))
                except:
                    pass

                db.add(item)
                existing[key] = item

            inserted += 1

        if not args.dry_run and (inserted > 0 or updated > 0):
            db.commit()

        summary.append({
            "file": filename,
            "parsed": len(records),
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "errors": error_count,
            "status": "DRY_RUN" if args.dry_run else "OK",
        })
        print(f"  {'🔍' if args.dry_run else '✓'} {filename}: {len(records)} parsed, {inserted} inserted, {updated} updated, {skipped} skipped, {error_count} errors")

    db.close()

    # ── Summary table ──
    print("\n" + "=" * 80)
    print(f"{'File':<48} {'Parsed':>6} {'Insert':>6} {'Update':>6} {'Skip':>6} {'Err':>4}")
    print("-" * 80)
    total_parsed = total_ins = total_upd = total_skip = total_err = 0
    for s in summary:
        print(f"{s['file']:<48} {s['parsed']:>6} {s['inserted']:>6} {s['updated']:>6} {s['skipped']:>6} {s['errors']:>4}")
        total_parsed += s["parsed"]
        total_ins += s["inserted"]
        total_upd += s["updated"]
        total_skip += s["skipped"]
        total_err += s["errors"]
    print("-" * 80)
    print(f"{'TOTAL':<48} {total_parsed:>6} {total_ins:>6} {total_upd:>6} {total_skip:>6} {total_err:>4}")
    print("=" * 80)
    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(f"\nMode: {mode} | Grand total: {total_parsed} parsed, {total_ins} inserted, {total_upd} updated\n")


if __name__ == "__main__":
    main()
