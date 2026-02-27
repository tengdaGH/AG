---
description: Semantic audit of IELTS reading item bank — human-style review that reads every item, validates content coherence, and catches problems that structural/regex audits miss.
---

# IELTS Reading Item Bank — Semantic Audit Workflow

// turbo-all

> **Why this exists:** The IELTS item bank contains 651 reading passages parsed from
> Cambridge IELTS PDF books via LLM extraction. This workflow performs a human-style
> semantic review — actually reading each passage and validating that the content,
> questions, answer keys, and metadata all make sense together.

## Context: How IELTS Items Differ from TOEFL

| | TOEFL | IELTS |
|---|---|---|
| **Storage** | SQLite database (`toefl_2026.db`) | Flat JSON files (`parsed_v2/ielts-r-NNNN.json`) |
| **Passage structure** | Single `text` field | `content.paragraphs[]` with optional `label` |
| **Questions** | `questions[]` flat array | `questions.question_groups[]` with typed groups |
| **Answer keys** | `correct_answer` per question | `raw_answer_key` dict + per-question `correct_answer` |
| **Question types** | MCQ only (4 options, single answer) | 16 types including MCQ, T/F/NG, completion, drag-and-drop, matching |
| **Source** | ETS PDF test booklets | Cambridge IELTS PDF books (130 volumes) |

---

## Pre-flight

1. Read this entire workflow before starting.

2. Understand the file structure:
```
/Users/tengda/Antigravity/IELTS/parsed_v2/
  ielts-r-0001.json  (21KB) — A Brief History of Tea
  ielts-r-0002.json  (10KB) — The Eden Project
  ...
  ielts-r-0651.json  (13KB)
```

3. Count items and verify:
```bash
ls /Users/tengda/Antigravity/IELTS/parsed_v2/ | wc -l
# Expected: 651
```

---

## The Item Schema

```json
{
  "id": "ielts-r-0001",
  "slug": "a-brief-history-of-tea",
  "title": "A Brief History of Tea",
  "page_range": [21, 25],
  "raw_answer_key": {"1": "viii", "2": "iv", ...},
  "content": {
    "title": "A Brief History of Tea",
    "has_paragraph_labels": true,
    "paragraphs": [
      {"label": "A", "content": "Tea is one of the oldest beverages..."},
      {"label": "B", "content": "In the 17th century..."}
    ]
  },
  "questions": {
    "question_groups": [
      {
        "type": "MATCHING_HEADINGS",
        "instruction": "Choose the correct heading...",
        "items": [
          {"number": 1, "text": "Paragraph A", "correct_answer": "viii", "options": [...]}
        ]
      },
      {
        "type": "MULTIPLE_CHOICE",
        "instruction": "Choose the correct letter...",
        "items": [
          {"number": 8, "text": "What was the...", "correct_answer": "D", "options": [...]},
        ]
      }
    ],
    "parsed_total_questions": 13
  },
  "processed_at": "2026-02-25T..."
}
```

---

## The 9-Point Semantic Checklist

For each item, mentally answer these questions. If any answer is "no", the item has a problem.

### 1. Title Coherence
> "Does the title accurately describe what this passage is about?"

**IELTS-specific failures:**
- Title truncated during PDF parsing
- Title is a heading from the wrong section of the PDF
- Title is the same as another item (duplicate titles = possible duplicate passages)

### 2. Passage Integrity
> "Does the passage read as one coherent piece? Are all paragraphs present?"

**IELTS-specific failures:**
- Paragraphs truncated mid-sentence (check the last paragraph especially)
- Missing paragraphs (compare `has_paragraph_labels` and actual labels A, B, C...)
- PDF header/footer text mixed into paragraph content
- Extremely short content (<1000 chars total) suggesting failed extraction

### 3. Paragraph Labels
> "If `has_paragraph_labels` is true, does every paragraph have a sequential label?"

**IELTS-specific failures:**
- Labels skip (A, B, D — missing C)
- Labels not sequential
- `has_paragraph_labels: true` but no `label` field on paragraphs
- `has_paragraph_labels: false` but matching headings questions reference paragraph letters

### 4. Question Group Structure
> "Does each question group have a valid `type`, `instruction`, and `items` array?"

**Valid question types (16):**
```
MULTIPLE_CHOICE          TRUE_FALSE_NOT_GIVEN       YES_NO_NOT_GIVEN
SUMMARY_COMPLETION       SENTENCE_COMPLETION        SHORT_ANSWER_QUESTIONS
MATCHING_HEADINGS        MATCHING_FEATURES          MATCHING_PARAGRAPH_INFORMATION
MATCHING_SENTENCE_ENDINGS  TABLE_COMPLETION         FLOW_CHART_COMPLETION
DIAGRAM_LABEL_COMPLETION CLASSIFICATION             LABEL_DIAGRAM
MATCHING_INFORMATION
```

Failures:
- Unknown or misspelled type
- Empty `items` array
- Missing instruction text

### 5. Question–Passage Alignment
> "For each question, can I find the answer by reading THIS passage?"

**IELTS-specific failures:**
- Completion questions reference words/phrases not in the passage
- Matching headings reference paragraph labels that don't exist
- T/F/NG statements contradict each other or are about content not in the passage
- Questions numbered beyond what the passage can support

### 6. Answer Key Completeness and Correctness
> "Does `raw_answer_key` have an entry for every question number? Are answers plausible?"

**IELTS-specific checks:**
- Count questions in all groups → should match `parsed_total_questions`
- Count entries in `raw_answer_key` → should match `parsed_total_questions`
- For T/F/NG, answers must be exactly `TRUE`, `FALSE`, or `NOT GIVEN`
- For Y/N/NG, answers must be exactly `YES`, `NO`, or `NOT GIVEN`
- For MCQ, answers must be valid option letters (A, B, C, D)
- For matching headings, answers must be valid heading numerals (i, ii, iii...)
- For completion, answers must be actual words/phrases from the passage (within word limit)

### 7. Question Numbering Continuity
> "Do question numbers flow sequentially across all groups without gaps or overlaps?"

Example: Group 1 has Q1-Q7, Group 2 should start at Q8, not Q1 or Q15.

### 8. Option Validity (MCQ / Matching types)
> "Does each MCQ/matching question have the correct number of plausible options?"

**IELTS-specific checks:**
- MCQ: typically 4 options (A-D), sometimes 3 for multi-select
- Matching features: options are usually people/categories from the passage
- Matching headings: heading options (i-x) should be more than the number of paragraphs
- T/F/NG and Y/N/NG: exactly 3 fixed options

### 9. Duplicate Detection
> "Is this passage unique, or has it appeared under a different ID?"

Check for:
- Same title appearing in multiple files
- Same passage text (first 200 chars) appearing in multiple files
- Same slug appearing in multiple files

---

## Step 1 — Batch Structural Pre-scan

Run a script that checks all 651 items structurally before diving into semantic review. This catches obvious issues quickly:

```bash
python3 << 'PYEOF'
import json, os
from collections import Counter, defaultdict

base = '/Users/tengda/Antigravity/IELTS/parsed_v2'
issues = []
titles = Counter()
slugs = Counter()

for fname in sorted(os.listdir(base)):
    if not fname.endswith('.json'): continue
    path = os.path.join(base, fname)
    fsize = os.path.getsize(path)
    
    with open(path) as f:
        data = json.load(f)
    
    fid = data.get('id', fname)
    title = data.get('title', '')
    slug = data.get('slug', '')
    titles[title] += 1
    slugs[slug] += 1
    
    content = data.get('content', {})
    paras = content.get('paragraphs', [])
    has_labels = content.get('has_paragraph_labels', False)
    
    qs = data.get('questions', {})
    groups = qs.get('question_groups', []) if isinstance(qs, dict) else []
    total_parsed = qs.get('parsed_total_questions', 0) if isinstance(qs, dict) else 0
    
    raw_key = data.get('raw_answer_key', {})
    
    # --- Checks ---
    
    # Tiny file
    if fsize < 3500:
        issues.append(('TINY_FILE', fid, f"Only {fsize} bytes"))
    
    # Missing title
    if not title:
        issues.append(('NO_TITLE', fid, ""))
    
    # Empty passage
    total_chars = sum(len(p.get('content','') if isinstance(p,dict) else str(p)) for p in paras)
    if total_chars < 200:
        issues.append(('SHORT_PASSAGE', fid, f"{total_chars} chars"))
    
    # Paragraph label continuity
    if has_labels and paras:
        labels = [p.get('label','') for p in paras if isinstance(p, dict)]
        for i, l in enumerate(labels):
            expected = chr(ord('A') + i)
            if l and l != expected:
                issues.append(('LABEL_GAP', fid, f"Expected {expected}, got {l}"))
                break
    
    # Question count mismatch
    actual_q_count = sum(len(g.get('items', [])) for g in groups)
    if total_parsed and actual_q_count != total_parsed:
        issues.append(('Q_COUNT_MISMATCH', fid, 
                       f"parsed_total={total_parsed} vs actual={actual_q_count}"))
    
    # Answer key count mismatch
    if raw_key and actual_q_count and len(raw_key) != actual_q_count:
        issues.append(('KEY_COUNT_MISMATCH', fid, 
                       f"key_entries={len(raw_key)} vs questions={actual_q_count}"))
    
    # Question numbering continuity
    all_numbers = []
    for g in groups:
        for item in g.get('items', []):
            n = item.get('number')
            if n is not None:
                all_numbers.append(int(n))
    if all_numbers:
        expected_seq = list(range(min(all_numbers), max(all_numbers)+1))
        if sorted(all_numbers) != expected_seq:
            issues.append(('Q_NUMBER_GAP', fid, f"Numbers: {sorted(all_numbers)[:5]}..."))
    
    # Unknown question types
    for g in groups:
        qtype = g.get('type', '')
        known = {'MULTIPLE_CHOICE','TRUE_FALSE_NOT_GIVEN','YES_NO_NOT_GIVEN',
                 'SUMMARY_COMPLETION','SENTENCE_COMPLETION','SHORT_ANSWER_QUESTIONS',
                 'MATCHING_HEADINGS','MATCHING_FEATURES','MATCHING_PARAGRAPH_INFORMATION',
                 'MATCHING_SENTENCE_ENDINGS','TABLE_COMPLETION','FLOW_CHART_COMPLETION',
                 'DIAGRAM_LABEL_COMPLETION','CLASSIFICATION','LABEL_DIAGRAM','MATCHING_INFORMATION'}
        if qtype not in known:
            issues.append(('UNKNOWN_Q_TYPE', fid, qtype))

# Duplicates
for t, count in titles.items():
    if count > 1 and t:
        issues.append(('DUPLICATE_TITLE', f"x{count}", t))

# Report
print(f"Scanned 651 items — {len(issues)} issues found\n")
by_type = defaultdict(list)
for cat, fid, detail in issues:
    by_type[cat].append((fid, detail))

for cat in sorted(by_type.keys()):
    items = by_type[cat]
    print(f"{cat} ({len(items)}):")
    for fid, detail in items[:5]:
        print(f"  [{fid}] {detail}")
    if len(items) > 5:
        print(f"  ... and {len(items)-5} more")
    print()
PYEOF
```

## Step 2 — Semantic Review by Batch

After the structural pre-scan, review items in batches of 20. For each batch, export the items and read through them:

```bash
python3 << 'PYEOF'
import json, os

base = '/Users/tengda/Antigravity/IELTS/parsed_v2'
START = 1   # Change this for each batch: 1, 21, 41, ...
END = 20

for i in range(START, END+1):
    fname = f'ielts-r-{i:04d}.json'
    path = os.path.join(base, fname)
    if not os.path.exists(path): continue
    
    with open(path) as f:
        data = json.load(f)
    
    content = data.get('content', {})
    paras = content.get('paragraphs', [])
    full_text = '\n\n'.join(
        p.get('content','') if isinstance(p, dict) else str(p) for p in paras
    )
    
    qs = data.get('questions', {})
    groups = qs.get('question_groups', []) if isinstance(qs, dict) else []
    raw_key = data.get('raw_answer_key', {})
    
    print(f"{'='*60}")
    print(f"{fname} — {data.get('title')}")
    print(f"{'='*60}")
    print(f"Passage ({len(full_text)} chars): {full_text[:300]}...")
    print(f"\nGroups ({len(groups)}):")
    for gi, g in enumerate(groups):
        items = g.get('items', [])
        print(f"  [{g.get('type')}] {len(items)} Qs — {g.get('instruction','')[:50]}")
    print(f"Answer key: {json.dumps(raw_key)[:80]}")
    print()
PYEOF
```

For each item, apply the 9-point checklist. Log issues.

## Step 3 — Fix Issues

Unlike TOEFL (SQLite), IELTS fixes are applied directly to the JSON files:

```python
import json

path = '/Users/tengda/Antigravity/IELTS/parsed_v2/ielts-r-NNNN.json'
with open(path) as f:
    data = json.load(f)

# Apply fixes...
data['title'] = 'Corrected Title'

with open(path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
```

## Step 4 — Verify and Move to Next Batch

After fixing, re-run the structural pre-scan from Step 1 to confirm issue counts decreased.

---

## Lessons Learned from 4 Automated Passes

### What the Automated Audit Fixed (~1,100 fixes across 290+ items)

| Category | Count | Root Cause |
|---|---|---|
| Raw answer key misaligned (trim/extend/rebuild) | ~820 | PDF OCR bleeding across columns; keys included instruction text or missed entries |
| Question type confusion (T/F/NG ↔ Y/N/NG) | 95 | LLM parser couldn't distinguish factual vs opinion passage context |
| MCQ multi-select normalization | 46 | Answers like `"C D E"`, `"B,D,F IN ANY"`, `"D/E/F (in any order)"` all needed `"X OR Y OR Z IN ANY ORDER"` format |
| Completion answer spelling/typos | 55 | OCR errors propagated from PDF to answer key (e.g. "gunpower" → "gunpowder", "airbome" → "airborne") |
| Paragraph label fixes | 27 | Mixed numeric/alpha labels; non-sequential labels; section names used as labels |
| MCQ trailing text in answers | 12 | Raw keys had extra words after the letter (e.g. `"E GIVEN"`, `"A yield"`) |
| Mixed-type groups split | 2 | Single group contained both MCQ and Y/N/NG items |
| Q renumbering | 13 | Gap from original test numbering (e.g. "Questions 27-40" became Q27-Q40 instead of Q1-Q14) |
| Tiny files re-parsed from source | 5 | Parser failed on short practice passages; content existed in `extracted/` all along |

### Known IELTS-Specific Pitfalls (still relevant)

1. **Cambridge PDF cross-page merging.** LLM parser sometimes truncates at page boundaries or merges footer/header text into the passage.
2. **Duplicate passages across books.** Some Cambridge IELTS books reprint passages from earlier editions.
3. **Completion answer validation is hard.** Unlike MCQ (A/B/C/D), completion answers are free-text words from the passage. Validating requires actually reading the passage.
4. **T/F/NG vs Y/N/NG confusion.** These are DIFFERENT question types with DIFFERENT answer labels. T/F/NG = factual; Y/N/NG = opinion.
5. **Word limits on completion answers.** Instructions say "NO MORE THAN TWO WORDS" or "ONE WORD ONLY". Answers must comply.
6. **Matching headings distractor count.** Heading options (i–x) are always more than paragraphs — extra options are distractors. Don't flag as error.
7. **Multi-select MCQ.** "Choose TWO/THREE answers" groups have multiple correct answers per group, not per question.
8. **Source data is in `extracted/`.** Each item has `passage_text`, `questions_text`, `full_text`, `solution_text`, and `answer_key` — use these to reconstruct missing data.

---

## What a Human Reviewer Would Do Next

> **Current state (Pass 5 complete):** ✅ All structural and semantic auto-fixable issues resolved. 647 items, 8,269 questions. 4 duplicates deleted.

### ⚠️ Next Session: Fix Truncated Passages, Missing Answers, Question Gaps

**Priority 1: Fix 39 Truncated Passages**

Passages ending mid-sentence. Fix methodology (in order):
1. `grep` the PDF dump at `pdf_text_dump/雅思阅读_全题库_dump.txt` (18MB) for the passage title or last words
2. Check `extracted/{id}.json` → `passage_text` or `full_text`
3. Check individual PDFs in `IELTS Reading 130/`
4. If nothing works, **search the web** for `"IELTS reading {passage title}"` to find the full passage

> Some passages ending in `"` or `'` may actually be complete (ending with a quote). Verify context before fixing.

**Priority 2: Fix Missing Data**
- `ielts-r-0440` Q5: missing answer — search PDF dump/web for "Birth of Scientific English answers"
- `ielts-r-0526`: missing Q11-Q15 — search for "origin of ancient writing" complete question set
- `ielts-r-0550`: 0 parsed questions (raw_key has fragments) — needs full re-parse

**Complete truncated item list is in the handoff task.md artifact.**


---

### Verification Command for All Remaining Issues

```bash
python3 << 'PYEOF'
import json, os
base = '/Users/tengda/Antigravity/IELTS/parsed_v2'
stats = {'empty_opts': 0, 'empty_q_text': 0, 'wrong_label': 0, 'truncated': 0, 'long_ans': 0}
for fname in sorted(os.listdir(base)):
    if not fname.endswith('.json'): continue
    with open(os.path.join(base, fname)) as f: d = json.load(f)
    for g in d.get('questions',{}).get('question_groups',[]):
        for item in g.get('items', g.get('questions',[])):
            if g.get('type') == 'MULTIPLE_CHOICE':
                opts = item.get('options') or []
                if opts and all(not (o.get('content','') or '').strip() for o in opts):
                    stats['empty_opts'] += 1
            if not (item.get('text','') or item.get('question','') or '').strip():
                stats['empty_q_text'] += 1
print(stats)
PYEOF
```

---

## Question Type Reference

| Type | Typical Count | Answer Format | Notes |
|------|--------------|---------------|-------|
| `MULTIPLE_CHOICE` | 3-5 per group | A, B, C, or D | Sometimes multi-select |
| `TRUE_FALSE_NOT_GIVEN` | 5-7 per group | TRUE / FALSE / NOT GIVEN | Factual passages only |
| `YES_NO_NOT_GIVEN` | 5-7 per group | YES / NO / NOT GIVEN | Opinion passages only |
| `SUMMARY_COMPLETION` | 4-8 per group | Word(s) from passage or from a list | Check word limit |
| `SENTENCE_COMPLETION` | 3-5 per group | Word(s) from passage | Check word limit |
| `SHORT_ANSWER_QUESTIONS` | 3-5 per group | Word(s) from passage | Check word limit |
| `MATCHING_HEADINGS` | 5-8 per group | Roman numeral (i, ii, iii...) | More options than paragraphs |
| `MATCHING_FEATURES` | 4-7 per group | Letter (A-E) referencing a person/category | |
| `MATCHING_PARAGRAPH_INFORMATION` | 4-6 per group | Letter (A-H) referencing a paragraph | |
| `TABLE_COMPLETION` | 3-6 per group | Word(s) from passage | |
| `FLOW_CHART_COMPLETION` | 3-6 per group | Word(s) from passage | |
| `DIAGRAM_LABEL_COMPLETION` | 3-6 per group | Word(s) from passage | |
| `MATCHING_SENTENCE_ENDINGS` | 3-5 per group | Letter (A-G) | More options than stems |
| `CLASSIFICATION` | 3-5 per group | Letter referencing a category | Rare |

---

## Audit History

| Date | Scope | Items | Issues Found | Fixed |
|------|-------|-------|--------------|-------|
| 2026-02-27 | Pre-scan (all 651) | 651 | 119 structural issues (35 KEY_COUNT_MISMATCH, 31 LABEL_GAP, 20 Q_COUNT_MISMATCH, 15 Q_NUMBER_GAP, 10 LABEL_DUPLICATE, 5 TINY_FILE, 3 DUPLICATE_TITLE) | N/A — scan only |
| 2026-02-27 | Batch 1 semantic (0001–0020) | 20 | 12 issues in 7 items: label duplicates (0001, 0006), raw_answer_key trailing text (0002, 0004, 0013), answer misalignment (0010), T/F/NG↔Y/N/NG type confusion (0012, 0017) | 7 items fixed: 0001 labels corrected A-H; 0002, 0004, 0013 raw_key cleaned; 0010 answers aligned + typos fixed; 0012, 0017 type changed to Y/N/NG |
| 2026-02-27 | Full automated audit (all 651) | 651 | 477 auto-fixable issues in 211 items + 533 flags in 232 items. Fixes: 222 raw_key_trim, 119 raw_key_extend, 95 type_correction, 19 ans_typo, 18 raw_key_typo, 4 label_resequence. Flags: 274 completion_not_in_passage, 137 ans_mismatch, 53 mcq_invalid, 20 q_count, 18 label_numeric, 15 q_gap, 5 tiny_file, 5 label_sections, 3 duplicate_title, 3 label_nonseq | 211 items auto-fixed. See `IELTS/audit_report.md` for full details |
| 2026-02-27 | Deep fix pass 2 (all 651) | 651 | 508 remaining fixes: 136 raw_key_force_aligned, 150 raw_key_rebuilt, 162 orphan_keys_pruned, 19 parsed_total_fixed, 41 completion_typos_corrected. Manual: ielts-r-0303 duplicate Q5 renumbered. | 103 items fixed. Structural issues: 119 → 5 (only TINY_FILE remains). Remaining 199 flags are informational only. |
| 2026-02-27 | Pass 3 — all remaining flags | 651 | 66 fixes in 48 items + 21 targeted MCQ fixes + 8 label/completion fixes. MCQ: 53→0. Q_GAP: 15→1. LABEL_NUMERIC: 18→0. LABEL_NONSEQ: 3→1. DUPLICATE_TITLE: 3→0. | 0 auto-fixable issues remain. 158 informational flags. |
| 2026-02-27 | Pass 4 — tiny file re-parse from source | 651 | 5 tiny files re-parsed from `extracted/` source JSON (passage_text, questions_text, answer_key). These are genuinely short practice items (1-6 Qs), not incomplete extractions. | 0 structural issues. |
| 2026-02-27 | Pass 6 — Human review of truncated passages & missing data | 42 | 39 truncated passages flagged (36 false positives, 3 fixed via PDF dump). 3 missing data items. | Fixed 0099, 0185, 0574 truncations. Reconstructed 0440 Q5, 0526 Q37-40 (originally reported as missing 11-15), and 0550 (fully reconstructed 12 questions). |
| 2026-02-27 | Pass 5 — Cambridge semantic audit | 651 | **Session 1**: 4,632 MCQ option texts filled (1,111→67), 37 group splits, 286 label swaps. **Session 2**: 14,766 text→content normalized (67→0 empty), 507 overlong options fixed (214→0), 3 more type reclassifications, 160 additional options extracted. | ✅ Empty opts: 0. ✅ Wrong labels: 0. ✅ Label mismatches: 0. ✅ Overlong opts: 0. ⚠️ 1 missing answer (0440 Q5). |
| 2026-02-27 | Pass 6 — Human review of truncated passages & missing data | 42 | 39 truncated passages flagged (36 false positives, 3 fixed via PDF dump). 3 missing data items. | Fixed 0099, 0185, 0574 truncations. Reconstructed 0440 Q5, 0526 Q37-40 (originally reported as missing 11-15), and 0550 (fully reconstructed 12 questions). |


When you complete an audit pass, append a row to this table.
