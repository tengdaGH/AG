# ============================================================
# Purpose:       Fix ETS official items that have no correct_answer set.
#                The raw answer keys exist in keys.raw_keys but were never
#                applied to individual questions during PDF parsing.
# Usage:         cd backend && python scripts/fix_ets_answer_keys.py [--dry-run]
# Created:       2026-02-26
# Self-Destruct: Yes (after successful execution)
# ============================================================
"""
Root cause:
  parse_ets_pdfs.py → parse_question_block() only returns {text, options},
  never sets correct_answer.  Answer keys are extracted by _parse_answer_keys()
  into a sibling 'keys.raw_keys' array but never mapped back to questions.

  raw_keys format per module:
    Reading: ['Number', ctest1..ctest10, mcq_Q11..mcq_Q20]
    Listening: ['Number', cr_Q1..cr_Q8, passage_Q9..passage_Q18]
  
  The letter at raw_keys[N] is the answer key for question number N.

Fix:
  1. Read each ETS official JSON file
  2. For each item, extract the question number from the question text
  3. Look up raw_keys[question_number] to get the letter (A/B/C/D)
  4. Convert letter to 0-based index and set correct_answer
  5. Write the fixed JSON back AND update the database
"""
import json, re, os, sys, argparse
from pathlib import Path

# Database access
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database.connection import SessionLocal
from app.models.models import TestItem

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
LETTER_TO_IDX = {'A': 0, 'B': 1, 'C': 2, 'D': 3}

# Files to fix (only MCQ items with raw_keys)
ETS_MCQ_FILES = [
    "ets_official_reading_academic.json",
    "ets_official_reading_daily_life.json",
    "ets_official_listening_passages.json",
]


def extract_question_number(q_text: str) -> int | None:
    """Extract the question number from text like '13. What is ...'"""
    m = re.match(r"^\s*(\d+)\.", q_text)
    return int(m.group(1)) if m else None


def apply_keys_to_items(items: list[dict], dry_run: bool) -> tuple[int, int]:
    """Apply raw_keys answer letters to individual questions.
    Returns (fixed_count, error_count)."""
    fixed = 0
    errors = 0
    
    for item in items:
        raw_keys = item.get("keys", {}).get("raw_keys", [])
        questions = item.get("questions", [])
        
        if not raw_keys or not questions:
            continue
        
        # Build a lookup: position → letter (only single A/B/C/D entries)
        key_map = {}
        for i, val in enumerate(raw_keys):
            if isinstance(val, str) and val.strip().upper() in LETTER_TO_IDX:
                key_map[i] = val.strip().upper()
        
        for q in questions:
            q_num = extract_question_number(q.get("text", ""))
            if q_num is None:
                errors += 1
                print(f"  ⚠ Could not extract Q# from: {q.get('text', '?')[:60]}")
                continue
            
            if q_num in key_map:
                letter = key_map[q_num]
                idx = LETTER_TO_IDX[letter]
                old = q.get("correct_answer")
                q["correct_answer"] = idx
                fixed += 1
                if not dry_run:
                    pass  # changes are in-place
                label = f"Q{q_num}: {letter} → {idx}"
                if old is not None and old != idx:
                    label += f" (was {old})"
                # Only print first few per item
            else:
                # Try to find the answer by looking at absolute position
                # For reading, raw_keys has 'Number' at [0], then items start at [1]
                # Questions 11-20 map to indices 11-20 in raw_keys
                errors += 1
                print(f"  ⚠ No key found for Q{q_num} in {item.get('id', '?')} "
                      f"(raw_keys has {len(raw_keys)} entries, key_map keys: {sorted(key_map.keys())})")
    
    return fixed, errors


def fix_json_file(filename: str, dry_run: bool) -> tuple[int, int]:
    """Fix a single JSON file. Returns (fixed, errors)."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"  ⚠ File not found: {filepath}")
        return 0, 0
    
    with open(filepath) as f:
        data = json.load(f)
    
    # Navigate to the items list based on file structure
    if "passages" in data:
        items = data["passages"]
    elif "sets" in data:
        # reading_daily_life shape: {sets: {ETS: {passages: [...]}}}
        items = []
        for _set_key, s in data["sets"].items():
            if isinstance(s, dict) and "passages" in s:
                items.extend(s["passages"])
            elif isinstance(s, list):
                items.extend(s)
    else:
        items = data.get("items", [])
    
    print(f"\n{'='*60}")
    print(f"  {filename}: {len(items)} items")
    
    fixed, errors = apply_keys_to_items(items, dry_run)
    
    if not dry_run and fixed > 0:
        with open(filepath, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  ✅ Written {filepath.name}")
    
    print(f"  Fixed: {fixed}, Errors: {errors}")
    return fixed, errors


def fix_database(dry_run: bool) -> tuple[int, int]:
    """Fix answer keys in the database for ETS official items."""
    db = SessionLocal()
    source_files = [f for f in ETS_MCQ_FILES]
    
    items = db.query(TestItem).filter(TestItem.source_file.in_(source_files)).all()
    
    print(f"\n{'='*60}")
    print(f"  Database: {len(items)} ETS items")
    
    fixed = 0
    errors = 0
    
    for item in items:
        try:
            data = json.loads(item.prompt_content)
            raw_keys = data.get("keys", {}).get("raw_keys", [])
            questions = data.get("questions", [])
            
            if not raw_keys or not questions:
                continue
            
            # Build key_map
            key_map = {}
            for i, val in enumerate(raw_keys):
                if isinstance(val, str) and val.strip().upper() in LETTER_TO_IDX:
                    key_map[i] = val.strip().upper()
            
            changed = False
            for q in questions:
                q_num = extract_question_number(q.get("text", ""))
                if q_num is None:
                    errors += 1
                    continue
                
                if q_num in key_map:
                    letter = key_map[q_num]
                    idx = LETTER_TO_IDX[letter]
                    q["correct_answer"] = idx
                    fixed += 1
                    changed = True
                else:
                    errors += 1
            
            if changed and not dry_run:
                item.prompt_content = json.dumps(data, ensure_ascii=False)
                
        except Exception as e:
            print(f"  ⚠ Error processing DB item {item.id}: {e}")
            errors += 1
    
    if not dry_run:
        db.commit()
        print(f"  ✅ Database committed")
    
    db.close()
    print(f"  Fixed: {fixed}, Errors: {errors}")
    return fixed, errors


def verify(dry_run: bool = True):
    """Verify the fix by checking distribution."""
    db = SessionLocal()
    source_files = [f for f in ETS_MCQ_FILES]
    items = db.query(TestItem).filter(TestItem.source_file.in_(source_files)).all()
    
    counts = {0: 0, 1: 0, 2: 0, 3: 0, 'missing': 0}
    total = 0
    
    for item in items:
        try:
            data = json.loads(item.prompt_content)
            for q in data.get("questions", []):
                if not isinstance(q.get("options"), list) or len(q.get("options", [])) < 2:
                    continue
                ca = q.get("correct_answer")
                total += 1
                if ca in counts:
                    counts[ca] += 1
                else:
                    counts['missing'] += 1
        except:
            pass
    
    db.close()
    
    print(f"\n{'='*60}")
    print(f"  POST-FIX VERIFICATION (ETS items only)")
    print(f"  Total MCQ questions: {total}")
    for k in [0, 1, 2, 3, 'missing']:
        label = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}.get(k, str(k))
        pct = (counts[k] / total * 100) if total else 0
        print(f"    {label}: {counts[k]} ({pct:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Fix ETS official item answer keys")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()
    
    print(f"{'DRY RUN' if args.dry_run else 'LIVE RUN'}")
    
    total_fixed = 0
    total_errors = 0
    
    # Fix JSON files
    for fname in ETS_MCQ_FILES:
        f, e = fix_json_file(fname, args.dry_run)
        total_fixed += f
        total_errors += e
    
    # Fix database
    f, e = fix_database(args.dry_run)
    total_fixed += f
    total_errors += e
    
    print(f"\n{'='*60}")
    print(f"  TOTAL: Fixed {total_fixed} answer keys, {total_errors} errors")
    
    if not args.dry_run:
        verify()


if __name__ == "__main__":
    main()
