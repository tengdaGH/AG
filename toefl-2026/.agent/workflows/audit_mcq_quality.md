---
description: Batch audit and remediate all MCQ items in the TOEFL 2026 item bank using ETS bulletproof quality standards — no user input required.
---

# MCQ Batch Audit & Remediation Workflow

// turbo-all

## Pre-flight

1. Read the skill at `/Users/tengda/Antigravity/toefl-2026/.agent/skills/mcq_item_quality/SKILL.md` before doing anything else. Internalize all standards.

2. Read the standards reference at `/Users/tengda/Antigravity/toefl-2026/.agent/knowledge/item-quality/mcq_item_quality.md`.

## Step 1 — Run Structural + Quality Audit (All MCQ Types)

// turbo
3. Run the broad audit across all reading and listening MCQ items (Muted):
```bash
cd /Users/tengda/Antigravity/toefl-2026 && python agents/scripts/audit_items.py > logs/audit_structural.log 2>&1
```
Check the summary ONLY by tailing the log:
```bash
tail -n 20 logs/audit_structural.log
```
Note the "GRAND TOTAL" and "MCQ QUALITY FLAGS" counts. Do NOT report full details to user.

## Step 2 — Run Deep ETS Review (Academic Passage Items)

// turbo
4. Run the deep review script (Muted):
```bash
cd /Users/tengda/Antigravity/toefl-2026/backend && python scripts/review_academic_items.py > logs/audit_academic.log 2>&1
```
View the summary at the end:
```bash
tail -n 30 logs/audit_academic.log
```
The full Markdown report is saved to `.gemini/antigravity/brain/.../ets_review_report.md`. Do not read the whole file into context unless asked.

## Step 3 — Batch LLM Remediation via API (Preferred, no context-window risk)

// turbo
5. Trigger the silent programmatic fixer (Fast & Local):
```bash
cd /Users/tengda/Antigravity/toefl-2026/backend && python scripts/silent_mcq_fixer.py
```
This applies heuristic fixes (trimming/padding) to all DRAFT/REVIEW items.

6. Trigger the LLM QA pipeline for deeper fixes (Slow & Remote):
```bash
curl -s -X POST http://localhost:8000/items/qa-pipeline > logs/qa_pipeline.log 2>&1
```
This runs in the background. Wait 30 seconds, then check if it's still processing:
```bash
tail -n 5 logs/qa_pipeline.log
```
Repeat until `"status": "success"` or 0 items processed.

## Step 4 — Manual Patch for Flagged Items Not Covered by QA Pipeline

6. For any item flagged in Step 1 or 2 that was NOT covered by Step 3 (e.g. items in ACTIVE or PUBLISHED status), remediate them directly using the Python housekeeping skill rules:

   - Write a self-deleting Python script to `/Users/tengda/Antigravity/toefl-2026/backend/scripts/patch_mcq_quality.py`
   - The script should:
     a. Query the DB for all MCQ items (sections: READING, LISTENING, task_types with `questions` arrays)
     b. For each item, run the option-length-parity and key-dominance checks (use the formula from the skill Step 6)
     c. For any failing question, apply remediation: trim the key or expand distractors to bring ratio ≤ 1.5
     d. Use `PATCH /items/{item_id}` to write changes back (this auto-bumps version + logs history)
     e. Print a summary of all patched items
   - Run the script, verify the output, then delete it.

**IMPORTANT — Batching strategy to avoid context window limits:**
   - Process items in chunks of 20 at a time using OFFSET/LIMIT SQL queries
   - Do not load all item content into your context simultaneously
   - Let the script handle all looping and DB writes — your role is just to write and run scripts, not to read each item

## Step 5 — Re-run Audit to Verify Clean State

// turbo
7. Re-run both audit scripts from Steps 1 and 2 to confirm issue counts have decreased.

8. Compare before/after counts. If any FAIL-level issues remain (KEY_DOMINANCE, PARITY_FAIL, DUPLICATE_OPTS), go back to Step 4 and patch again.

## Step 6 — Final Report

9. After completion, create a summary report at:
   `/Users/tengda/Antigravity/toefl-2026/.agent/knowledge/history/work_log.md`
   
   Append an entry with:
   - Date: today
   - Items audited: total count
   - Items patched: count
   - Before/after Quality Score distribution
   - Any items that could not be auto-remediated and why

10. Done. No user input was needed.

---

## Key Design Principles (to avoid context window issues)

- **Scripts do the work, not the agent's context**: All iteration, DB reads, and writes happen inside Python scripts. The agent writes and runs the scripts.
- **Batch API endpoint first**: `POST /items/qa-pipeline` is the single most powerful action — it uses the LLM server-side on batches of 50 without loading everything into agent context.
- **OFFSET/LIMIT in scripts**: Any custom script must paginate with `LIMIT 20 OFFSET N` to avoid loading 700+ items at once.
- **No agent-level loops**: Never ask the agent to read item 1, fix it, read item 2, fix it... Always write a script that loops internally.
