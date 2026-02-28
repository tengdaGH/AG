---
name: item_writer
description: >
  Generates new TOEFL 2026 test items (MCQ, C-Test, Listen-and-Choose, Build-a-Sentence, etc.)
  from a topic/passage seed. Runs the mcq_item_quality self-check, assigns IRT parameters,
  and inserts items directly into item_bank.db. Use this skill whenever the item bank needs
  topping up or a specific task type is running low.
---

# item_writer — Automated Item Generation Agent

The item_writer generates, validates, and ingests new TOEFL 2026 test items.
It is supervised by Alfred: Alfred detects when item counts drop and may invoke item_writer automatically.

---

## item_writer's Mandate

> "Every item I write is indistinguishable from an item written by a senior ETS item writer."

item_writer does not write items in bulk and hope they are good.
It writes ONE item at a time, validates it against ETS standards, and only inserts it if it passes.

---

## Task Types item_writer Can Generate

| Section | Task Type | DB `task_type` value |
|---------|-----------|----------------------|
| Reading | Complete the Words (C-Test) | `C_TEST` |
| Reading | Read in Daily Life (MCQ) | `DAILY_LIFE` |
| Reading | Read an Academic Passage (MCQ) | `ACADEMIC_PASSAGE` |
| Listening | Listen and Choose a Response | `LISTEN_CHOOSE_RESPONSE` |
| Listening | Listen to a Conversation | `LISTEN_CONVERSATION` |
| Listening | Listen to an Announcement | `LISTEN_ANNOUNCEMENT` |
| Listening | Listen to an Academic Talk | `LISTEN_ACADEMIC_TALK` |
| Writing | Build a Sentence | `BUILD_SENTENCE` |
| Writing | Write an Email | `WRITE_EMAIL` |
| Speaking | Listen and Repeat | `LISTEN_REPEAT` |

---

## Generation Protocol

### Step 1 — Check what the bank needs

Before generating, query the item bank to find which types are running low:

```bash
cd /Users/tengda/Documents/Antigravity/toefl-2026
source backend/venv/bin/activate
python3 - <<'EOF'
import sqlite3
conn = sqlite3.connect("backend/item_bank.db")
rows = conn.execute("""
    SELECT task_type, COUNT(*) as n
    FROM test_items
    WHERE lifecycle_status='ACTIVE'
    GROUP BY task_type
    ORDER BY n ASC
""").fetchall()
for r in rows:
    print(f"  {r[1]:4d}  {r[0]}")
conn.close()
EOF
```

Prioritize task types with the fewest items. Target: ≥ 50 items per task type. ETS minimum for safe MST operation: ≥ 30.

---

### Step 2 — Choose a topic seed

ETS-compliant topics (from `specs/toefl_2026_spec_sheet.md`):
- History, art/music, business/economics, life science, physical science, social science
- No specialized background knowledge required
- No excessive proper nouns or technical jargon
- Content reviewed for fairness (gender, L1, age, nationality)

Pick a topic NOT already heavily represented in the bank. Check with:
```sql
SELECT title, task_type FROM test_items WHERE lifecycle_status='ACTIVE' ORDER BY RANDOM() LIMIT 20;
```

---

### Step 3 — Generate the item

Use the **existing generation scripts** as templates. Reference:
- `agents/scripts/agent_generate_compliant_items.py` — the master generation script
- `specs/task_types/<type>.md` — ETS spec for each task type
- `specs/toefl_2026_spec_sheet.md` — structural constraints

For **MCQ items** (DAILY_LIFE, ACADEMIC_PASSAGE, LISTEN_*):
- Must have: `prompt_content`, `options` (JSON array of 4), `correct_answer` (A/B/C/D)
- Distractor rule: each wrong answer must be plausible but clearly incorrect on re-read
- No "all of the above", "none of the above"
- Key is never always A or always D (vary position)
- Apply the `mcq_item_quality` SKILL self-check before inserting

For **C-Test items** (C_TEST):
- Minimum 8 gap markers (`_` characters per gap)
- No `(blank lines)` annotations — use actual `___` underscores in prompt_content
- Gaps should be mid-word deletions of the second half, not whole-word gaps
- CEFR target: B1–B2 for Stage 1, B2–C1 for Stage 2 Upper

For **Build-a-Sentence** (BUILD_SENTENCE):
- `prompt_content` = scrambled word tokens (JSON array)
- `correct_answer` = correct sentence string
- `options` = null (not MCQ)
- Sentence should be grammatically unambiguous — only ONE correct order

---

### Step 4 — Validate with mcq_item_quality skill

Read and apply: `.agent/skills/mcq_item_quality/SKILL.md`

Mandatory checks before any insert:
- [ ] Stem is complete and unambiguous without the options
- [ ] Correct answer is definitively correct (not just "best guess")
- [ ] All 3 distractors are plausible but clearly wrong
- [ ] No clang associations (key word in stem echoed in correct answer)
- [ ] No negative phrasing ("Which of the following is NOT...")
- [ ] Reading level matches target CEFR band
- [ ] Topic is ETS-compliant (no nationality/gender bias)

---

### Step 5 — Assign IRT parameters

All new items start with **estimated** IRT parameters (not calibrated from real student data).
Read the `irt_item_graduation` SKILL for full details.

Initial parameter estimates:
```python
# Starting values by CEFR target:
# A1-A2 (Easy Stage 2):    b = -1.5, a = 1.0
# B1 (Stage 1 Router):     b =  0.0, a = 1.0
# B2 (Stage 1 Router):     b =  0.5, a = 1.0
# C1 (Hard Stage 2):       b =  1.5, a = 1.2
# C2 (Hard Stage 2 Upper): b =  2.0, a = 1.3
```

Set `lifecycle_status = 'DRAFT'` on insert. Items go ACTIVE only after ETS Gold review.

---

### Step 6 — Insert into item_bank.db

Use parameterized SQL — never f-string interpolation:

```python
import sqlite3, json, datetime

conn = sqlite3.connect("backend/item_bank.db")
conn.execute("""
    INSERT INTO test_items (
        task_type, section, title, prompt_content, options, correct_answer,
        irt_difficulty, irt_discrimination, lifecycle_status, cefr_level,
        exposure_count, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', ?, 0, ?)
""", (
    task_type,           # e.g. 'DAILY_LIFE'
    section,             # e.g. 'READING'
    title,
    prompt_content,
    json.dumps(options) if options else None,  # JSON array or None
    correct_answer,      # 'A', 'B', 'C', 'D', or full sentence string
    irt_difficulty,      # float
    irt_discrimination,  # float
    cefr_level,          # e.g. 'B1'
    datetime.datetime.utcnow().isoformat()
))
conn.commit()
conn.close()
print(f"✅ Inserted 1 new DRAFT item: {title}")
```

---

## Alfred Supervision Hooks

Alfred monitors item_writer outcomes:

| Alfred Check | Threshold | item_writer Response |
|-------------|-----------|---------------------|
| ACTIVE items < 1,000 | 🟡 Watch | Generate 20 items per section until ≥ 1,000 |
| ACTIVE items < 900 | 🔴 Red | Generate 50+ items immediately, escalate to user |
| SUSPENDED items > 30 | 🟡 Watch | Review suspended items first — some may be fixable |
| Any task type < 30 items | 🟡 Watch | Top up that task type to 50 minimum |

---

## Batch Generation Script

For bulk generation, use the workflow:

```bash
/generate-items --type C_TEST --count 20 --cefr B1
```

(Create the `/generate-items` workflow using this skill as its instructions.)

The script `agents/scripts/agent_generate_compliant_items.py` is the canonical batch generator.
Always specify `task_type` and `count`. Default CEFR = B1 unless told otherwise.

---

## Files item_writer Always Reads

1. `specs/task_types/<task_type>.md` — ETS item spec for the target type
2. `specs/toefl_2026_spec_sheet.md` — structural constraints
3. `.agent/skills/mcq_item_quality/SKILL.md` — quality gate
4. `.agent/skills/irt_item_graduation/SKILL.md` — IRT parameter assignment
5. `agents/scripts/agent_generate_compliant_items.py` — reference implementation

---

## Relationship to Other Skills

- **Alfred** supervises item_writer — he triggers it when counts drop
- **mcq_item_quality** is item_writer's mandatory quality gate
- **irt_item_graduation** runs AFTER items are approved, promoting DRAFT → ACTIVE
- **toefl_voice_direction** is called for any item that needs audio generation
