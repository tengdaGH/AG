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
| Reading | Complete the Words (C-Test) | `COMPLETE_THE_WORDS` |
| Reading | Read in Daily Life (MCQ) | `READ_IN_DAILY_LIFE` |
| Reading | Read an Academic Passage (MCQ) | `READ_ACADEMIC_PASSAGE` |
| Listening | Listen and Choose a Response | `LISTEN_CHOOSE_RESPONSE` |
| Listening | Listen to a Conversation | `LISTEN_CONVERSATION` |
| Listening | Listen to an Announcement | `LISTEN_ANNOUNCEMENT` |
| Listening | Listen to an Academic Talk | `LISTEN_ACADEMIC_TALK` |
| Writing | Build a Sentence | `BUILD_A_SENTENCE` |
| Writing | Write an Email | `WRITE_AN_EMAIL` |
| Writing | Write Academic Discussion | `WRITE_ACADEMIC_DISCUSSION` |
| Speaking | Take an Interview | `TAKE_AN_INTERVIEW` |
| Speaking | Listen and Repeat | `LISTEN_AND_REPEAT` |

> [!CAUTION]
> These are the **exact** enum values from `backend/app/models/models.py → TaskType`. Any deviation will cause a SQLAlchemy IntegrityError silent failure or type mismatch on insert. Do NOT use old names like `C_TEST`, `DAILY_LIFE`, `BUILD_SENTENCE`, `WRITE_EMAIL`, `LISTEN_REPEAT`.

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

> [!IMPORTANT]
> **Schema rule:** There is NO `title`, `options`, `correct_answer`, or `cefr_level` column on `test_items`. All item content (text, questions, options, answer keys, title, audio_url) lives inside `prompt_content` as a JSON blob. The DB row only stores metadata. Do not add non-existent columns to INSERT statements.

**DB columns on `test_items` (verified against `models.py` 2026-02-28):**
```
id, author_id, section, task_type, target_level, irt_difficulty, irt_discrimination,
prompt_content, media_url, rubric_id, lifecycle_status, is_active, version,
generated_by_model, generation_notes, created_at, updated_at,
exposure_count, last_exposed_at, source_file, source_id
```

**`prompt_content` JSON schema by task type (embed all item content here):**

For **MCQ items** (`READ_IN_DAILY_LIFE`, `READ_ACADEMIC_PASSAGE`, `LISTEN_CONVERSATION`, `LISTEN_ANNOUNCEMENT`, `LISTEN_ACADEMIC_TALK`, `LISTEN_CHOOSE_RESPONSE`):
```json
{
  "title": "<item title>",
  "text": "<passage or prompt text>",
  "audio_url": "<relative path for listening items, e.g. audio/listening/LCR-xxx.wav>",
  "questions": [
    {
      "text": "<question stem>",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 0
    }
  ]
}
```
- `correct_answer` is an **integer index** (0–3), NOT a letter like 'A','B','C','D'
- Distractor rule: each wrong answer must be plausible but clearly incorrect on re-read
- No "all of the above", "none of the above"
- Key index must not always be 0 (vary position)
- Apply the `mcq_item_quality` SKILL self-check before inserting

For **C-Test items** (`COMPLETE_THE_WORDS`):
```json
{"title": "<title>", "text": "Par_ial wo_ds wi_h undersc_res for g_ps."}
```
- Minimum 8 gap markers (`_` characters per gap)
- No `(blank lines)` annotations — use actual `___` underscores inline
- Gaps are mid-word deletions of the second half, not whole-word removals
- CEFR target: A1–A2 for easy, B1–B2 for Stage 1, B2–C1 for Stage 2 Upper

For **Build-a-Sentence** (`BUILD_A_SENTENCE`):
```json
{"title": "<title>", "sentences": [{"words": ["scrambled", "tokens", "here"], "answer": "Full correct sentence."}]}
```
- Sentence must be grammatically unambiguous — only ONE correct ordering
- No MCQ options

For **Write an Email** (`WRITE_AN_EMAIL`) and **Write Academic Discussion** (`WRITE_ACADEMIC_DISCUSSION`):
```json
{"title": "<title>", "prompt": "<the writing task prompt>"}
```

For **Take an Interview** (`TAKE_AN_INTERVIEW`) and **Listen and Repeat** (`LISTEN_AND_REPEAT`):
```json
{"title": "<title>", "prompt": "<speaking prompt>", "audio_url": "<audio path>"}
```
- No `correct_answer` — these are open-response, scored by rubric

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

Use parameterized SQL — never f-string interpolation.

> [!CAUTION]
> The columns `title`, `options`, `correct_answer`, and `cefr_level` do **NOT** exist on `test_items`. All content goes inside `prompt_content` as JSON. Use `target_level` for CEFR. Use `media_url` for audio file paths (not `audio_url`).

```python
import sqlite3, json, uuid, datetime

conn = sqlite3.connect("backend/item_bank.db")
conn.execute("""
    INSERT INTO test_items (
        id, task_type, section, target_level, prompt_content,
        irt_difficulty, irt_discrimination, lifecycle_status,
        is_active, version, exposure_count, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'DRAFT', 0, 1, 0, ?, ?)
""", (
    str(uuid.uuid4()),
    task_type,           # e.g. 'READ_IN_DAILY_LIFE' — must match TaskType enum exactly
    section,             # e.g. 'READING' — must match SectionType enum exactly
    target_level,        # e.g. 'B1' — must match CEFRLevel enum: A1,A2,B1,B2,C1,C2
    json.dumps(prompt_content_dict),  # ALL item content here — title, text, questions, audio_url
    irt_difficulty,      # float, e.g. 0.0 for B1
    irt_discrimination,  # float, e.g. 1.0 default
    datetime.datetime.utcnow().isoformat(),
    datetime.datetime.utcnow().isoformat()
))
conn.commit()
conn.close()
print(f"✅ Inserted 1 new DRAFT item: {prompt_content_dict.get('title')}")
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

## ⚡ Mandatory Post-Conditions (DO THESE BEFORE REPORTING DONE)

These are not optional. item_writer is not finished until these are complete.

### After inserting ANY Listening or Speaking items:

> **You MUST invoke `audio_generator` before you finish.**
> Do not report "done" or "20 items inserted" until audio has been generated for every new item.

```
Listening task types that trigger this:  LISTEN_CHOOSE_RESPONSE, LISTEN_CONVERSATION,
                                          LISTEN_ANNOUNCEMENT, LISTEN_ACADEMIC_TALK
Speaking task types that trigger this:   LISTEN_REPEAT
```

**The sequence is always:**
1. Insert Listening/Speaking items → `audio_url = NULL`
2. **Immediately** read `.agent/skills/audio_generator/SKILL.md`
3. Generate audio for every new item using that skill
4. Update `audio_url` in item_bank.db
5. Verify: `SELECT COUNT(*) FROM test_items WHERE audio_url IS NULL AND section='LISTENING'` → must be 0
6. **Only now** report completion to the user

**Why this is mandatory, not optional:**
Alfred checks for Listening items where `media_url IS NULL` on ACTIVE items and flags it RED.
Note: audio URL lives inside `prompt_content → audio_url` JSON field AND optionally in the `media_url` DB column.
An item without audio cannot be served to students — it is effectively broken.
Inserting Listening items without audio is like writing a dialogue without recording it.

---

### After inserting ANY items (all types):

Confirm the item count increased as expected:
```python
# Run this and show the output to the user
SELECT task_type, COUNT(*) FROM test_items
WHERE lifecycle_status='DRAFT' OR lifecycle_status='ACTIVE'
GROUP BY task_type ORDER BY task_type;
```

---

### After inserting MCQ items that passed Gold review:

Invoke `irt_item_graduation` to promote them from DRAFT → ACTIVE.
Do NOT do this automatically — wait for the user to confirm review passed.

---

## Relationship to Other Skills

| Skill | When item_writer calls it | Mandatory? |
|-------|--------------------------|------------|
| `mcq_item_quality` | Before every MCQ insert (Step 4) | ✅ Yes |
| `audio_generator` | Immediately after inserting any Listening/Speaking item | ✅ Yes — do not skip |
| `irt_item_graduation` | After items pass ETS Gold review (user confirms) | 🔲 Wait for user |
| `toefl_voice_direction` | audio_generator reads this — not called directly | indirect |
| **Alfred** | Supervises item_writer — monitors counts, not invoked by item_writer | n/a |

