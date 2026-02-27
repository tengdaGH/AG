# ============================================================
# Purpose:       Canonical schema normalizer for test_items.prompt_content.
#                Prevents field-naming drift (correct vs correct_answer,
#                content vs text, etc.) regardless of which ingest script
#                created the row.
# Usage:         from app.services.prompt_schema import normalize_prompt
# Created:       2026-02-27
# Self-Destruct: No
# ============================================================
"""
prompt_schema — single source of truth for prompt_content field naming.

Call ``normalize_prompt(pc, task_type)`` on any parsed prompt_content dict
before writing it back to the database. The function is idempotent: calling
it on already-clean data is a no-op.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any

# ── Public API ────────────────────────────────────────────────────────────────

def normalize_prompt(pc: dict, task_type: str) -> dict:
    """Apply every normalisation rule and return the (mutated) dict.

    Rules
    -----
    1. ``content`` → ``text``  (if ``text`` is absent)
    2. ``correct`` → ``correct_answer``  on every question
    3. Populate ``text`` from ``messages`` array when ``text`` is empty
    4. Strip duplicate ``correct`` key when ``correct_answer`` already exists
    """
    # 1. content → text
    if "content" in pc and "text" not in pc:
        pc["text"] = pc.pop("content")

    # 2 + 4. correct → correct_answer  /  remove duplicate correct
    for q in pc.get("questions", []):
        if "correct" in q and "correct_answer" not in q:
            q["correct_answer"] = q.pop("correct")
        elif "correct" in q and "correct_answer" in q:
            del q["correct"]

    # 3. messages → text  (text-chain items)
    if "messages" in pc and not (pc.get("text") or "").strip():
        msgs = pc["messages"]
        lines = [f'{m.get("sender", "")}: {m.get("text", "")}' for m in msgs]
        pc["text"] = "\n".join(lines)

    return pc


def enforce_all(
    db_path: str,
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Scan every row in ``test_items``, normalise, and optionally write back.

    Returns a summary dict::

        {
            "scanned": 1087,
            "modified": 12,
            "details": [
                {"id": "abc12345...", "fixes": ["content→text", "correct→correct_answer x2"]},
                ...
            ]
        }
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    rows = cur.execute(
        "SELECT id, task_type, prompt_content FROM test_items"
    ).fetchall()

    summary: dict[str, Any] = {"scanned": len(rows), "modified": 0, "details": []}

    for item_id, task_type, pc_raw in rows:
        pc = json.loads(pc_raw)
        original = json.dumps(pc, sort_keys=True)

        normalize_prompt(pc, task_type or "")

        updated = json.dumps(pc, sort_keys=True)
        if updated != original:
            fixes = _diff_description(json.loads(original), pc)
            summary["details"].append({"id": item_id, "fixes": fixes})
            summary["modified"] += 1

            if not dry_run:
                cur.execute(
                    "UPDATE test_items SET prompt_content = ? WHERE id = ?",
                    (json.dumps(pc, ensure_ascii=False), item_id),
                )

    if not dry_run:
        conn.commit()
    conn.close()
    return summary


# ── Private helpers ───────────────────────────────────────────────────────────

def _diff_description(old: dict, new: dict) -> list[str]:
    """Return human-readable list of what changed."""
    fixes: list[str] = []

    if "content" in old and "content" not in new:
        fixes.append("content→text")

    old_qs = old.get("questions", [])
    new_qs = new.get("questions", [])
    correct_fixes = sum(
        1
        for oq, nq in zip(old_qs, new_qs)
        if "correct" in oq and "correct" not in nq
    )
    if correct_fixes:
        fixes.append(f"correct→correct_answer x{correct_fixes}")

    if "messages" in old and not (old.get("text") or "").strip() and (new.get("text") or "").strip():
        fixes.append("messages→text")

    return fixes or ["minor normalisation"]
