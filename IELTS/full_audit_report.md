# IELTS Item Bank — Full Audit Report

**Generated**: 2026-02-26 16:52:24 CST  
**Source**: 651 newly processed IELTS Reading JSON objects  
**Pipeline**: `extracted/ → (LLM via Minimax) → parsed_v2/ → staging/`

---

## Phase 1: Structural & Schema Validation

### Summary

| Metric | Count | % |
|---|---|---|
| Total extracted (raw) | 651 | — |
| Successfully parsed by LLM | 646 | 99.2% |
| **Missing from parsed_v2** (LLM failures) | 5 | 0.8% |
| Extra in parsed_v2 (unexpected) | 0 | — |
| ✅ Clean schema | 611 | 94.6% |
| ⚠️ Minor warnings | 35 | 5.4% |
| ❌ Critical schema failures | 0 | 0.0% |
| 🔁 Duplicate IDs | 0 | — |

### Files Missing from parsed_v2 (LLM never processed these)

These items require re-processing via `structure_v2.py`.

- `ielts-r-0194.json`
- `ielts-r-0291.json`
- `ielts-r-0429.json`
- `ielts-r-0476.json`
- `ielts-r-0609.json`

### Issue Type Breakdown (parsed_v2 files)

| Issue Type | Count |
|---|---|
| `answer_count_mismatch` | 20 |
| `raw_answer_key_mismatch` | 17 |

---

## Phase 2: Pedagogical Spec Audit

### Passage Classification

| Classification | Count | % |
|---|---|---|
| ✅ IDEAL (700–900w, 13–14q) | 247 | 37.9% |
| 📎 MINI_PASSAGE (≤350 words, 1 MCQ) | 27 | 4.1% |
| ⚠️ WARN_WORD_COUNT | 349 | 53.6% |
| ⚠️ WARN_QUESTION_COUNT | 17 | 2.6% |
| ⚠️ WARN_OVERSIZED | 6 | 0.9% |
| ❌ EMPTY_OR_STUB | 0 | 0.0% |
| ❌ NOT_PROCESSED (missing parsed_v2) | 5 | 0.8% |

### Word Count Statistics (passage_text only)

| Stat | Value |
|---|---|
| Min | 57 words |
| Max | 1551 words |
| Avg | 878.9 words |

### Question Count Statistics (full passages only)

| Stat | Value |
|---|---|
| Min | 4 |
| Max | 19 |
| Avg | 13.0 |

### Question Type Distribution

> This shows how many question groups of each type exist across all 651 items.

| Question Type | Groups |
|---|---|
| `TRUE_FALSE_NOT_GIVEN` | 336 |
| `MULTIPLE_CHOICE` | 297 |
| `SUMMARY_COMPLETION` | 231 |
| `MATCHING_PARAGRAPH_INFORMATION` | 174 |
| `MATCHING_FEATURES` | 160 |
| `SENTENCE_COMPLETION` | 157 |
| `MATCHING_HEADINGS` | 119 |
| `SHORT_ANSWER_QUESTIONS` | 75 |
| `YES_NO_NOT_GIVEN` | 58 |
| `TABLE_COMPLETION` | 33 |
| `DIAGRAM_LABEL_COMPLETION` | 17 |
| `FLOW_CHART_COMPLETION` | 15 |
| `MATCHING_SENTENCE_ENDINGS` | 15 |
| `CLASSIFICATION` | 5 |
| `LABEL_DIAGRAM` | 1 |
| `MATCHING_INFORMATION` | 1 |

### Critical Pedagogical Issues (27)

| ID | Words | Questions | Issue |
|---|---|---|---|
| `ielts-r-0011` | 379 | 5 | WARN: passage below ideal length (379 words, target 700+); CRITICAL: too few que |
| `ielts-r-0033` | 859 | 9 | CRITICAL: too few questions (9, min 10) |
| `ielts-r-0048` | 448 | 9 | WARN: passage below ideal length (448 words, target 700+); CRITICAL: too few que |
| `ielts-r-0059` | 684 | 7 | WARN: passage below ideal length (684 words, target 700+); CRITICAL: too few que |
| `ielts-r-0066` | 409 | 6 | WARN: passage below ideal length (409 words, target 700+); CRITICAL: too few que |
| `ielts-r-0076` | 444 | 7 | WARN: passage below ideal length (444 words, target 700+); CRITICAL: too few que |
| `ielts-r-0081` | 735 | 5 | CRITICAL: too few questions (5, min 10) |
| `ielts-r-0163` | 724 | 9 | CRITICAL: too few questions (9, min 10) |
| `ielts-r-0215` | 517 | 7 | WARN: passage below ideal length (517 words, target 700+); CRITICAL: too few que |
| `ielts-r-0262` | 384 | 7 | WARN: passage below ideal length (384 words, target 700+); CRITICAL: too few que |
| `ielts-r-0269` | 497 | 6 | WARN: passage below ideal length (497 words, target 700+); CRITICAL: too few que |
| `ielts-r-0315` | 815 | 4 | CRITICAL: too few questions (4, min 10) |
| `ielts-r-0372` | 396 | 5 | WARN: passage below ideal length (396 words, target 700+); CRITICAL: too few que |
| `ielts-r-0378` | 362 | 7 | WARN: passage below ideal length (362 words, target 700+); CRITICAL: too few que |
| `ielts-r-0395` | 426 | 5 | WARN: passage below ideal length (426 words, target 700+); CRITICAL: too few que |
| `ielts-r-0414` | 538 | 6 | WARN: passage below ideal length (538 words, target 700+); CRITICAL: too few que |
| `ielts-r-0430` | 913 | 8 | CRITICAL: too few questions (8, min 10) |
| `ielts-r-0434` | 391 | 5 | WARN: passage below ideal length (391 words, target 700+); CRITICAL: too few que |
| `ielts-r-0480` | 577 | 8 | WARN: passage below ideal length (577 words, target 700+); CRITICAL: too few que |
| `ielts-r-0490` | 520 | 7 | WARN: passage below ideal length (520 words, target 700+); CRITICAL: too few que |
| `ielts-r-0509` | 425 | 8 | WARN: passage below ideal length (425 words, target 700+); CRITICAL: too few que |
| `ielts-r-0520` | 519 | 8 | WARN: passage below ideal length (519 words, target 700+); CRITICAL: too few que |
| `ielts-r-0560` | 817 | 9 | CRITICAL: too few questions (9, min 10) |
| `ielts-r-0574` | 375 | 7 | WARN: passage below ideal length (375 words, target 700+); CRITICAL: too few que |
| `ielts-r-0590` | 367 | 5 | WARN: passage below ideal length (367 words, target 700+); CRITICAL: too few que |
| `ielts-r-0602` | 396 | 6 | WARN: passage below ideal length (396 words, target 700+); CRITICAL: too few que |
| `ielts-r-0645` | 880 | 6 | CRITICAL: too few questions (6, min 10) |

---

## Phase 3: Controlled Integration

### Staging Summary

| Metric | Count | % |
|---|---|---|
| Total parsed_v2 files | 646 | — |
| ✅ Successfully staged | 0 | 0.0% |
| ❌ Excluded from staging | 646 | 100.0% |

### Exclusion Reasons

| Reason | Count |
|---|---|
| `schema_critical_failures` | 0 |
| `duplicate_slugs` | 0 |
| `duplicate_titles` | 4 |
| `db_collisions` | 642 |
| `load_errors` | 0 |

> ✅ **DB collision check**: 642 existing source_ids found in `ielts_passages`

### Duplicate Titles

| Title | Files |
|---|---|
| australian parrots and their adaptation to habitat change | ielts-r-0050.json, ielts-r-0051.json |
| children’s literature | ielts-r-0093.json, ielts-r-0094.json |
| rainwater harvesting | ielts-r-0355.json, ielts-r-0356.json |
| the water hyacinth | ielts-r-0571.json, ielts-r-0572.json |

---

## Recommended Action Items

1. **Re-run `structure_v2.py`** for 5 files missing from `parsed_v2/` (LLM timeouts during batch processing).
2. **Import 0 staged files** from `IELTS/staging/` into the database using `scripts/migrate_reading_to_db.py` (update it to read from `staging/`).
