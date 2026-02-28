# ============================================================
# Purpose:       Normalize question schemas and fix key distribution imbalance in 6 specific DRAFT items.
# Usage:         python backend/scripts/fix_draft_items.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
fix_draft_items.py

Fixes the 6 DRAFT items that failed QA due to:
 1. Non-standard question key names (e.g. 'question', 'question_text' instead of 'text')
 2. Non-standard correct_answer formats (full-text string, 1-based integer string)
 3. Key distribution imbalance (>50% answers on one option)

For each item, we:
  - Normalize all question dicts to use 'text' for the stem
  - Normalize options to {text: str} format consistently
  - Convert correct_answer to a 0-based int
  - Shuffle/rotate options to fix key distribution imbalance
"""

import os, sys, json, random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import SessionLocal
from app.models.models import TestItem, ItemVersionHistory

DRAFT_IDS = [
    "434f26a2-5be5-490e-baa8-56c040a4caf8",
    "e40820df-a448-49e0-8979-2104c2fdd073",
    "5cc29b65-2744-4a7d-a45a-2de68bedf6bd",
    "f6c458f4-9167-4d8c-bf92-a64a145b79a9",
    "324cef3d-48eb-487b-b567-3d29d3cc702f",
    "39dbbac9-2f65-4c4b-84ec-24c03ebc43ac",
]


def normalize_question(q: dict) -> dict:
    """Normalize a question dict to the canonical schema."""
    # Normalize stem to 'text'
    stem = q.get("text") or q.get("question") or q.get("stem") or q.get("question_text") or ""
    # Normalize options: always list of plain strings
    raw_opts = q.get("options", [])
    options = []
    for opt in raw_opts:
        if isinstance(opt, dict):
            options.append(opt.get("text", opt.get("value", "")))
        else:
            options.append(str(opt) if opt is not None else "")

    # Normalize correct_answer to 0-based int
    correct = q.get("correct_answer")
    if isinstance(correct, str) and len(correct) == 1 and correct.lower() in "abcd":
        correct_idx = ord(correct.lower()) - ord("a")
    elif isinstance(correct, str):
        # Could be a 1-based int string or full-text answer
        try:
            val = int(correct)
            # 1-based index
            correct_idx = val - 1
        except ValueError:
            # Full text — find the matching option
            correct_lower = correct.strip().lower()
            correct_idx = next(
                (i for i, o in enumerate(options) if o.strip().lower() == correct_lower),
                0
            )
    elif isinstance(correct, int):
        # Could be 0-based or 1-based depending on the source
        # If it's already 0-based it should be < len(options)
        correct_idx = correct if correct < len(options) else correct - 1
    else:
        correct_idx = 0

    return {
        "text": stem,
        "options": options,
        "correct_answer": correct_idx,
    }


def fix_key_distribution(questions: list[dict]) -> list[dict]:
    """
    Shuffle options to ensure no single position holds > 50% of keys.
    Uses a deterministic rotation pattern: spread keys across A, B, C, D.
    """
    if len(questions) < 3:
        return questions

    key_positions = [q["correct_answer"] for q in questions]
    n = len(questions)
    
    # Check if distribution is imbalanced
    from collections import Counter
    counts = Counter(key_positions)
    if max(counts.values()) / n <= 0.5:
        return questions  # Already balanced

    # Assign target positions in a round-robin pattern
    target_positions = [i % 4 for i in range(n)]
    # Make target positions look natural by mixing the pattern slightly
    # We'll cycle through A=0, B=1, C=2, D=3 in a pattern
    pattern = [0, 2, 1, 3, 1, 0, 3, 2, 2, 1, 3, 0]
    target_positions = [pattern[i % len(pattern)] for i in range(n)]

    fixed_questions = []
    for q, target_pos in zip(questions, target_positions):
        opts = q["options"]
        current_key = q["correct_answer"]
        if current_key >= len(opts):
            fixed_questions.append(q)
            continue
        if current_key == target_pos:
            fixed_questions.append(q)
            continue
        # Swap current key position with target position
        new_opts = opts[:]
        new_opts[current_key], new_opts[target_pos] = new_opts[target_pos], new_opts[current_key]
        fixed_questions.append({
            **q,
            "options": new_opts,
            "correct_answer": target_pos,
        })
    return fixed_questions


def fix_item(item: TestItem, db) -> str:
    """Fix and save a single item. Returns a status message."""
    try:
        data = json.loads(item.prompt_content)
    except Exception as e:
        return f"SKIP {item.id[:8]}: JSON parse error: {e}"

    raw_questions = data.get("questions", [])
    if not raw_questions:
        return f"SKIP {item.id[:8]}: No questions found."

    # Step 1: Normalize question schemas
    normalized = [normalize_question(q) for q in raw_questions]

    # Step 2: Fix key distribution
    balanced = fix_key_distribution(normalized)

    # Step 3: Save back
    data["questions"] = balanced

    new_content = json.dumps(data, ensure_ascii=False)

    # Save version history
    db.add(ItemVersionHistory(
        item_id=item.id,
        version_number=item.version,
        prompt_content=item.prompt_content,
        changed_by="QA-Fixer-v1"
    ))
    item.version += 1
    item.prompt_content = new_content
    item.generation_notes = "Schema normalized and key distribution fixed by QA-Fixer-v1."
    db.commit()

    # Verify key distribution after fix
    from collections import Counter
    key_positions = [q["correct_answer"] for q in balanced]
    counts = Counter(key_positions)
    max_pct = max(counts.values()) / len(balanced) * 100
    return f"FIXED {item.id[:8]}: {len(balanced)} questions, max key concentration = {max_pct:.0f}%"


def main():
    db = SessionLocal()
    print("=" * 60)
    print("QA Fixer: Normalizing 6 DRAFT items")
    print("=" * 60)
    for item_id in DRAFT_IDS:
        item = db.query(TestItem).filter(TestItem.id == item_id).first()
        if not item:
            print(f"NOT FOUND: {item_id[:8]}")
            continue
        result = fix_item(item, db)
        print(result)
    db.close()
    print("\nDone. Re-run QA pipeline to verify.")


if __name__ == "__main__":
    main()
