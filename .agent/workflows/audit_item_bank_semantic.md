---
description: Semantic audit of TOEFL item bank items — human-style review that reads every item, validates content coherence, and catches problems that structural/regex audits miss.
---

# TOEFL Item Bank — Semantic Audit Workflow

// turbo-all

> **Why this exists:** Structural audits (regex, field presence, option counts) miss
> content-level problems: spliced questions from wrong passages, misclassified task
> types, titles that don't match passages, and answer keys for the wrong content.
> This workflow performs a human-style semantic review — actually reading each item
> and validating that every piece makes sense together.

---

## The Item Bank at a Glance

**Total:** 1,087 items in SQLite at `/Users/tengda/Antigravity/toefl-2026/backend/toefl_2026.db`

| Source Model | Count | Audit Status |
|---|---|---|
| ETS (S1, S2, T1–T5) | 310 | ✅ Audited 2026-02-27 |
| JSON-Import | 280 | ✅ Audited 2026-02-27 |
| Inworld_Sliced | 151 | ❌ Not audited |
| Legacy | 103 | ✅ Audited 2026-02-27 |
| Minimax-M2.5-Extraction | 86 | ❌ Not audited |
| Inworld | 75 | ❌ Not audited |
| gemini-2.5-flash | 31 | ❌ Not audited |
| Legacy-Import-Fixed | 19 | ✅ Audited 2026-02-27 |
| MiniMax-M2.5-Refactor | 11 | ❌ Not audited |
| MiniMax-M2.5 | 11 | ❌ Not audited |
| Gemini-2.5-Flash | 10 | ❌ Not audited |

---

## How to Work Through the Full Bank

### Batch Strategy

Do NOT try to review all 777 items at once. Process them **one source model at a time**, in this priority order:

| Pass | Source Model | Items | Why |
|------|-------------|-------|-----|
| 1 | `JSON-Import` | 280 | Largest block, parsed from external JSON — highest risk of schema issues |
| 2 | `Legacy` + `Legacy-Import-Fixed` | 122 | Old pipeline items — may have outdated schema or missing fields |
| 3 | `Inworld` + `Inworld_Sliced` | 226 | Audio-generated items — check transcript/question alignment |
| 4 | `Minimax-M2.5-Extraction` | 86 | LLM-extracted items — may have hallucinated options or keys |
| 5 | `MiniMax-M2.5` + `MiniMax-M2.5-Refactor` | 22 | Small batch, same risk as above |
| 6 | `gemini-2.5-flash` + `Gemini-2.5-Flash` | 41 | Most recent pipeline — likely cleanest |

### Within Each Pass: The Review Procedure

For each source model pass, follow these exact steps:

#### Step A — Dump items for review

Write a script to export ALL items from that source model. **Do not load them all into your context at once.** Instead, export them to a file and review in chunks of 10–15 items.

```python
import sqlite3, json
conn = sqlite3.connect('/Users/tengda/Antigravity/toefl-2026/backend/toefl_2026.db')

# Change MODEL for each pass
MODEL = 'JSON-Import'
OFFSET = 0   # Increment by 15 for each chunk: 0, 15, 30, ...
LIMIT = 15

rows = conn.execute("""
    SELECT id, section, task_type, target_level, prompt_content, media_url
    FROM test_items
    WHERE generated_by_model = ?
    ORDER BY section, task_type, id
    LIMIT ? OFFSET ?
""", (MODEL, LIMIT, OFFSET)).fetchall()

for row in rows:
    item_id, section, task_type, level, pc_raw, media = row
    pc = json.loads(pc_raw)
    title = pc.get('title') or pc.get('topic') or ''
    text = pc.get('text') or pc.get('content') or ''
    questions = pc.get('questions', [])

    print(f"{'='*60}")
    print(f"[{item_id[:8]}] {section} | {task_type} | {level}")
    print(f"Title: {title}")
    print(f"Text ({len(str(text))} chars): {str(text)[:400]}")
    if len(str(text)) > 400: print("...")
    print(f"Questions: {len(questions)}")
    for qi, q in enumerate(questions):
        qtext = q.get('text', '')
        opts = q.get('options', [])
        ans = q.get('correct_answer')
        print(f"  Q{qi+1}: {qtext[:70]}")
        for oi, o in enumerate(opts):
            m = '→' if oi == ans else ' '
            print(f"    {m} {chr(65+oi)}. {str(o)[:60]}")
    print(f"Media: {media or 'NONE'}")
    print()
conn.close()
```

#### Step B — Read each item and apply the 7-point checklist

For every item displayed, mentally answer these 7 questions. If any answer is "no", log an issue.

1. **Title–Passage Coherence** — Does the title accurately describe this passage?
2. **Passage Integrity** — Is this one coherent piece? Are there spliced pages or preamble?
3. **Question–Passage Alignment** — Can EVERY question be answered from THIS passage? *(This is the most critical check.)*
4. **Answer Key Correctness** — Is the keyed answer actually correct? Could a different option be defended?
5. **Classification Correctness** — Does `task_type` match the content? (e.g., academic vs daily-life)
6. **Schema Consistency** — Are field names correct? (`text` vs `content`, `correct_answer` present, etc.)
7. **Media Completeness** — If this is a listening/speaking item, does `media_url` exist?

#### Step C — Fix issues immediately

When you find an issue, fix it before moving to the next chunk. Write fixes directly to the database:

```python
pc['title'] = "Correct Title"               # Fix title
pc['questions'] = pc['questions'][:3]        # Strip wrong questions
pc['text'] = pc.pop('content')               # Normalize field name

cur.execute("UPDATE test_items SET prompt_content = ? WHERE id = ?",
            (json.dumps(pc, ensure_ascii=False), item_id))
conn.commit()
```

For task_type reclassification:
```sql
UPDATE test_items SET task_type = 'READ_IN_DAILY_LIFE' WHERE id = '...';
```

#### Step D — Log what you found

After completing a source model, update the audit history table at the bottom of this file:
```
| 2026-MM-DD | JSON-Import | 280 | 12 issues | All fixed |
```

#### Step E — Move to next source model

Increment to the next pass in the priority table.

---

## The 7-Point Semantic Checklist — Details

### 1. Title–Passage Coherence
> "If I read only the title, would I correctly predict what this passage is about?"

**Common failures:**
- Title is the first sentence of the passage (embedded title)
- Title is a fragment from a PDF header unrelated to the passage
- Title is a generic label ("Read a text chain.") instead of content description
- Title is empty string `""`

### 2. Passage Integrity
> "Does this passage read as one coherent piece of writing? Does every paragraph belong?"

**Common failures:**
- Two passages concatenated (daily-life header + academic body from next page)
- `Reading Section, Module X` preamble left in text
- Text stored in `content` key instead of `text` key (check both)
- Passage content stored as fake numbered "questions" instead of in text field

### 3. Question–Passage Alignment
> "For each question, can I find the answer by reading THIS passage?"

**This is the most critical check.** Common failures:
- Later questions (Q4–Q8) spliced from a different passage
- Question references concepts/people not in the passage
- "The word X in the passage" but X doesn't appear

### 4. Answer Key Correctness
> "Is the keyed answer actually correct?"

**Common failures:**
- Answer index off-by-one
- All questions have the same answer (suspicious)
- Answer text doesn't match the passage content

### 5. Classification Correctness
> "Does the task_type match the actual content?"

- Text chains, emails, social media → `READ_IN_DAILY_LIFE`
- Academic topics with cited research → `READ_ACADEMIC_PASSAGE`
- `section` must match `task_type` (reading types in READING, etc.)

### 6. Schema Consistency

| Task Type | Expected Fields |
|-----------|----------------|
| `READ_ACADEMIC_PASSAGE` | `title`, `text`, `questions[].text`, `questions[].options`, `questions[].correct_answer` |
| `READ_IN_DAILY_LIFE` | Same as above. Some items use `content` instead of `text` — normalize |
| `COMPLETE_THE_WORDS` | `text` (with blanks), no `questions` array |
| `BUILD_A_SENTENCE` | `text` (instructions + sentences + word boxes). No separate `words`/`answer` fields |
| `LISTEN_*` | `transcript` or `text`, `questions`, `media_url` |
| `TAKE_AN_INTERVIEW` | `topic`, `scenario`, `questions` (open-ended, no options expected), `media_url` |

### 7. Media Completeness
> "If this item needs audio, does it have a `media_url`?"

Required for: all `LISTEN_*` and `SPEAKING` section items.

---

## Known Pitfalls

1. **Don't trust field names blindly.** Some items use `content`, others use `text`. Always check both.

2. **Don't trust keyword audits.** A word like "customer" in an academic passage about economics doesn't make it daily-life. Read the actual content.

3. **Watch for cross-page PDF concatenation.** Page N's footer glued to page N+1's header creates Frankenstein items.

4. **Question numbering is a splice signal.** If questions jump from "15." to "16." but the topic changes completely, the second set is from a different passage.

5. **BUILD_A_SENTENCE uses a non-standard schema.** Everything is in the `text` field. Don't flag missing `words`/`answer` arrays.

6. **Interview questions have no options by design.** Don't flag empty options or null keys for `TAKE_AN_INTERVIEW`.

7. **Complete-the-words has zero questions.** The blanks are in the text. Don't flag 0 questions.

---

## Audit History

| Date | Source Model | Items | Issues Found | Fixed |
|------|-------------|-------|--------------|-------|
| 2026-02-27 | ETS (all 7 models) | 310 | 9 critical + 47 medium | All fixed |
| 2026-02-27 | JSON-Import | 280 | 47 issues (14 missing correct_answer, 13 content→text, 20 empty titles) | All fixed |
| 2026-02-27 | Legacy + Legacy-Import-Fixed | 122 | 55 issues (36 correct→correct_answer, 16 content→text, 3 messages→text) | All fixed |

When you complete an audit pass, append a row to this table.
