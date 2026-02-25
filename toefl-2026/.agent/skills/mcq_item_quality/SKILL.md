---
name: mcq_item_quality
description: Self-check protocol for bulletproof multiple-choice question items. Use when generating or reviewing any MCQ item for TOEFL 2026 Reading and Listening sections.
---

# MCQ Item Quality Skill

Use this skill when **generating** or **reviewing** multiple-choice questions to catch quality issues before writing to the database. This prevents defective items from entering the item bank and reduces the need for post-hoc remediation.

> Full standards reference: `.agent/knowledge/item-quality/mcq_item_quality.md`

---

## When to Use This Skill

- After generating a new MCQ item (any script that calls the LLM and creates options)
- Before running `db.add(item)` or the equivalent insert operation
- As a review protocol when remediating items flagged by `review_academic_items.py` or `audit_items.py`

---

## Step 1: Stem Check (3 questions)

After writing the stem, answer these:

1. **Does the stem present a single, clear problem?** If you need to read the options to know what the question is asking, the stem is incomplete. Rewrite.
2. **Does the stem avoid negative phrasing?** If it contains "NOT" or "EXCEPT", capitalize them. If possible, rewrite positively.
3. **Does the stem accidentally reveal the key's grammar?** (e.g., "an ___" when only option B starts with a vowel) — fix by rewriting the stem or adjusting the options.

---

## Step 2: Key Check (4 questions)

After writing the correct answer:

1. **Is the key unambiguously the ONLY correct answer?** Could a different option also be defended? If yes, the key or that distractor needs to be rewritten.
2. **Is the key shorter than or comparable to the distractors?** Count words. If the key is >50% more words than the mean distractor word count, **shorten the key first**.
3. **Does the key paraphrase rather than copy the passage?** If >5 consecutive words appear verbatim in the passage, rewrite using synonyms.
4. **Does the key contain absolute words** ("always", "never", "all", "only")? Replace with "typically", "rarely", "most", "primarily".

---

## Step 3: Distractor Check (per distractor, ×3)

For each of the 3 distractors:

1. **Is it plausible?** A learner who misread or over-inferred from the passage should consider it. If it's obviously wrong on its face, rewrite.
2. **Is it clearly wrong?** When checked against the passage, an informed reader must reject it without ambiguity.
3. **Does it have absolute words** ("always", "never")? These make it too easy to eliminate. Replace.
4. **Does it overlap with another distractor?** Two distractors that make the same erroneous claim weaken the item. Rewrite one.

---

## Step 4: Option Set Check (the 4 options together)

Run through this checklist mentally or as code:

```
[ ] Exactly 4 options (A–D)
[ ] No "all of the above" or "none of the above"
[ ] No two options with identical meaning or ≥5 shared leading words
[ ] All options complete the stem grammatically
[ ] All options parallel in grammatical structure (all noun phrases, or all full sentences, etc.)
[ ] Longest option word count ≤ 2.5 × shortest option word count
[ ] Key is NOT the notably longest or shortest option
[ ] All options start with a capital letter
```

If any box is unchecked, fix before writing to DB.

---

## Step 5: Question Type Diversity (Academic Passage Items Only)

For `READ_ACADEMIC_PASSAGE` items, check that across all 5 questions, each type is represented at least once:

```
[ ] Main Idea / Purpose   → "What is the passage mainly about?"
[ ] Factual Detail        → "According to the passage, ..."
[ ] Inference             → "What can be inferred ..."
[ ] Vocabulary in Context → "The word '[X]' in paragraph N is closest in meaning to ..."
[ ] Rhetorical Purpose    → "The author mentions [X] in order to ..."
```

If a type is missing, add it. If at 5 questions already, replace the weakest item (usually a duplicate type).

---

## Step 6: Option Length Parity — Quick Calculation

This is the most commonly violated rule. Use this formula:

```python
word_counts = [len(opt.split()) for opt in options]
key_wc = word_counts[correct_answer]
distractor_wcs = [wc for i, wc in enumerate(word_counts) if i != correct_answer]
mean_distractor_wc = sum(distractor_wcs) / len(distractor_wcs)
max_wc = max(word_counts)
min_wc = min(word_counts)

# FAIL conditions:
key_too_long = key_wc > mean_distractor_wc * 1.5          # Key dominance
parity_fail  = max_wc > min_wc * 2.5                      # Overall parity
```

If `key_too_long` is True:
- Shorten the key by removing qualifiers, examples, or subordinate clauses.
- If removing them makes the key incorrect, expand the distractors instead.

If `parity_fail` is True:
- Find the outlier option (longest or shortest).
- Trim the longest, or add a plausible qualifying clause to the shortest.

---

## Quick Reference: Remediation Cheat Sheet

| Issue | Fix |
|-------|-----|
| Key >50% longer than mean distractor | Trim key; remove examples/qualifications |
| Distractor obviously wrong | Add a plausible but wrong qualifier |
| Distractor contains "always/never" | Replace with "typically/rarely" |
| Key copies passage verbatim | Paraphrase using synonyms |
| Two distractors overlap in meaning | Rewrite one with a different misconception angle |
| Stem is a vague opener | Rewrite as a specific direct question |
| Missing question type in 5-question set | Add new question or replace weakest duplicate |

---

## How This Connects to the Review Pipeline

After items are in the DB, the automated reviewers catch any issues missed at generation time:

- `backend/scripts/review_academic_items.py` — deep ETS-standards review for academic passage items
- `agents/scripts/audit_items.py` — structural audit for all reading + listening MCQ items
- `GET /items/qa-pipeline` — LLM-based QA with auto-remediation for DRAFT/REVIEW items
