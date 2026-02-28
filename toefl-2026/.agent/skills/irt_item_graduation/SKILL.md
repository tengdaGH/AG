---
name: irt_item_graduation
description: >
  IRT simulation and calibration protocol to run when an item reaches ETS Gold review
  standard. Covers per-item calibration, fit diagnostics, lifecycle promotion, and
  the decision rules for ACTIVE vs SUSPENDED. Use this skill every time a batch of
  items is approved through the review pipeline.
---

# IRT Item Graduation Protocol

Run this skill whenever items have **passed ETS Gold review** (lifecycle_status transitions
from `REVIEW` → ready for live testing). The goal is to attach calibrated IRT parameters
before the item is ever served to a real student.

> **Rule:** No item enters a live test with `irt_difficulty = NULL` or `lifecycle_status != 'ACTIVE'`.
> This skill is the gate that enforces that rule.

---

## When to Trigger This Skill

| Trigger | Condition |
|---------|-----------|
| Single item approved | A human reviewer or AI QA pipeline sets an item's status to `APPROVED` or `GOLD` |
| Batch approval | A review script promotes a cohort of items (e.g., task_type=READ_ACADEMIC_PASSAGE) |
| Post-remediation | An item that was `SUSPENDED` (poor fit) has been rewritten and needs re-calibration |
| Scheduled re-calibration | Monthly sweep of all ACTIVE items to update parameters with accumulated real response data |

---

## Step 1: Pre-Flight Check

Before running any simulation, verify the item is structurally complete:

```python
# Checks required before calibration
assert item.prompt_content is not None and len(item.prompt_content) > 20
assert item.questions is not None and len(item.questions) >= 1
assert item.target_level in ['A1','A2','B1','B2','C1','C2']
assert item.task_type is not None
assert item.section in ['READING','LISTENING','SPEAKING','WRITING']

# For MCQ: at least 4 options and a valid correct_answer
for q in item.questions:
    if q.options:
        assert len(q.options) == 4, f"MCQ must have 4 options, got {len(q.options)}"
        assert q.correct_answer in ['0','1','2','3'], "correct_answer must be 0-3"
```

If any check fails → **do not calibrate**. Return the item to the review queue with a note.

---

## Step 2: Choose Calibration Mode

Use **Monte Carlo (MML 2PL)** for all items except Writing/Speaking CR.

| Item Type | Calibration Mode | Script |
|-----------|-----------------|--------|
| READ_*, LISTEN_MCQ_*, C_TEST | Monte Carlo MML 2PL | `calibrate_full_itembank.py` |
| SPEAK_*, WRITE_* (CR) | CEFR-anchored fallback | `calibrate_full_itembank.py` |
| Any with n_panel < 20 | CEFR-anchored fallback | automatic fallback in script |

---

## Step 3: Run the Calibration

### Option A — Single Item (quick, post-approval)

```bash
cd /Users/tengda/Documents/Antigravity/toefl-2026/backend
source venv/bin/activate

python3 scripts/calibrate_full_itembank.py \
    --item-id <ITEM_UUID> \
    --apply
```

If `--item-id` flag doesn't exist in the current script, use:

```bash
python3 scripts/calibrate_full_itembank.py \
    --section READING \
    --task-type READ_ACADEMIC_PASSAGE \
    --apply
```
and then filter results by item ID in the output log.

### Option B — Full Batch (after bulk approval)

```bash
python3 scripts/calibrate_full_itembank.py --apply
```

This calibrates every item regardless of current status, then:
- Sets `lifecycle_status = 'ACTIVE'` for good-fit items
- Sets `lifecycle_status = 'SUSPENDED'` for poor-fit items
- Writes `irt_difficulty`, `irt_discrimination`, `exposure_count = 0`
- Appends a timestamp + calibration summary to `generation_notes`

### Option C — Dry Run (verify without writing to DB)

```bash
python3 scripts/calibrate_full_itembank.py
# (no --apply flag → dry run mode)
```

Always do a dry run first on unfamiliar batches.

---

## Step 4: Interpret Calibration Output

For each item, the script produces:

```
item_id=abc123  task=READ_ACADEMIC_PASSAGE  level=B2
  Panel n=800 examinees
  MML 2PL: b=0.512  a=1.234
  Anchor:  b_anchor=0.500
  delta_b=0.012  → fit=Good
  → ACTIVE ✅
```

### Decision Rules

| delta_b | Interpretation | Action |
|---------|---------------|--------|
| < 2.0 logits | **Good fit** — estimated b close to CEFR anchor | Set `ACTIVE` ✅ |
| 2.0 – 3.0 logits | **Borderline** — monitor in first 50 real responses | Set `ACTIVE` with flag in notes |
| > 3.0 logits | **Poor fit** — estimated difficulty far from item's stated level | Set `SUSPENDED`, route to remediation |

### Parameter Interpretation

| Parameter | Healthy Range | Warning |
|-----------|--------------|---------|
| `irt_difficulty` (b) | −2.5 to +2.5 | Outside ±3.0: borderline item |
| `irt_discrimination` (a) | 0.5 to 2.5 | < 0.3: item does not differentiate; > 3.0: suspiciously sharp |
| `exposure_count` | 0 after calibration | Non-zero means item was already served — check for contamination |

---

## Step 5: Post-Calibration Verification

After running `--apply`, verify success in the database:

```python
# Quick sanity check — run this in a Python shell
import sqlite3, json

db = sqlite3.connect('item_bank.db')
cur = db.cursor()

# Check newly calibrated items
cur.execute("""
    SELECT id, target_level, irt_difficulty, irt_discrimination,
           lifecycle_status, exposure_count
    FROM test_items
    WHERE lifecycle_status = 'ACTIVE'
    AND irt_difficulty IS NOT NULL
    ORDER BY created_at DESC
    LIMIT 20
""")
rows = cur.fetchall()
for r in rows:
    item_id, level, b, a, status, exp = r
    cefr_theta = {'A1':-2.5,'A2':-1.5,'B1':-0.5,'B2':0.5,'C1':1.5,'C2':2.5}
    anchor = cefr_theta.get(level, 0.0)
    delta = abs(b - anchor)
    flag = '⚠️' if delta > 2.0 else '✅'
    print(f"{flag} {item_id[:8]}  {level}  b={b:+.3f}  a={a:.3f}  Δ={delta:.2f}  exp={exp}")
```

Expected: all items with `ACTIVE` status should have `|b − anchor| < 2.0` and `a > 0.3`.

---

## Step 6: Handle SUSPENDED Items

If any items come out `SUSPENDED` (poor fit), follow this remediation path:

1. **Read the `generation_notes`** field — it contains the delta_b and the specific mis-calibration direction
2. **Determine cause:**
   - `b >> anchor` (item harder than stated level): Simplify the stem or add a more obvious correct answer
   - `b << anchor` (item easier than stated level): Increase lexical complexity or add more nuanced distractors
   - `a < 0.3` (does not discriminate): Usually means the distractors are too random — rewrite with principled misconceptions
3. **Edit the item** using the item bank dashboard or API
4. **Re-run calibration** for that specific item (Step 3, Option A)
5. If item fails calibration **twice**, escalate to human domain expert review

---

## Step 7: Update lifecycle_status in Item Bank

After calibration and verification, ensure the lifecycle is complete:

```
DRAFT → REVIEW → APPROVED → [IRT CALIBRATION] → ACTIVE
                                                     ↓
                                              SUSPENDED (if poor fit)
                                                     ↓
                                            (Remediation) → Re-calibrate → ACTIVE
```

The calibration script handles this transition automatically with `--apply`.

---

## Quick Reference: Calibration Quality Pass/Fail

```
PASS if ALL of:
  ✅ irt_difficulty is not NULL
  ✅ irt_discrimination >= 0.3
  ✅ |irt_difficulty - cefr_anchor| < 2.0 logits
  ✅ lifecycle_status set to 'ACTIVE'
  ✅ exposure_count = 0 (fresh item, not pre-contaminated)

FAIL (route to SUSPENDED) if ANY of:
  ❌ |irt_difficulty - cefr_anchor| >= 3.0 logits
  ❌ irt_discrimination < 0.3 (no discriminating power)
  ❌ Calibration script raised ValueError or returned fallback only
```

---

## Files Reference

| File | Role |
|------|------|
| `backend/item_bank.db` | **Item bank database** — the only DB this skill touches. See `specs/database_guide.md`. |
| `backend/scripts/calibrate_full_itembank.py` | Main calibration engine (MML 2PL + CEFR fallback) |
| `backend/scripts/simulate_field_test_v2.py` | Monte Carlo / LLM examinee simulation for FIELD_TEST items |
| `backend/app/services/score_calculator.py` | MAP θ estimator — used to validate calibrated parameters |
| `backend/app/api/routes/items.py` | `/filter` endpoint — exposure-ordered item serving |

> [!CAUTION]
> This skill operates **exclusively** on `item_bank.db`. Never point calibration scripts at `user_data.db`.
> If in doubt, read `specs/database_guide.md` before proceeding.

---

## Connection to the Live Test Pipeline

Once an item is `ACTIVE`, it enters the live assembly pool:

```
Item ACTIVE
    │
    ▼ GET /api/items/filter?section=READING
    │   ORDER BY exposure_count ASC, RANDOM()
    │
    ▼ Served in Stage 1 (Router) or Stage 2 (Upper/Lower)
    │
    ▼ Student responds → POST /sessions/{id}/submit
    │   exposure_count += 1 (written back to item bank)
    │
    ▼ GET /sessions/{id}/results
        IRT MAP θ estimation using this item's (b, a, c)
        → Band, CEFR, SEM in score report
```

Monitor `exposure_count` monthly. ETS standard maximum exposure rate is **15% of test-takers** per item per year. Items exceeding this should be retired to `RETIRED` status and replaced with fresh calibrated items.
