# IELTS Reading Pipeline — Agent Handoff

**Date**: 2026-02-24T03:00  
**Status**: Plan approved, execution not started  
**Priority**: High — user wants to proceed immediately

---

## What Was Done

1. **Corpus analysis** of all 130 PDFs in `/Users/tengda/Antigravity/IELTS/IELTS Reading 130/`
2. Sampled and deeply analyzed 8 passages (3×P1, 3×P2, 2×P3)
3. Cataloged **14 IELTS question types** with frequency counts
4. Designed a JSON schema for structured output
5. Wrote and got approval on implementation plan

### Key Stats
| Metric | Value |
|---|---|
| Total PDFs | 130 (41 P1, 39 P2, 50 P3) |
| Avg chars/PDF | ~7,800 |
| Question types | 14 distinct types |
| Answer keys in PDFs | **None** — LLM generation needed |
| Difficulty markers | 54 高 / 29 次 / 47 unmarked |

---

## What Needs To Be Done

### 1. Build `parse_ielts_reading.py`
**Location**: `/Users/tengda/Antigravity/IELTS/parse_ielts_reading.py`

Core script with these functions:
- `extract_pdf_text(path)` — PyPDF2 extraction (already confirmed available)
- `split_passage_and_questions(text, position)` — Split on first question group header
- `parse_passage(text)` — Detect paragraph labels (A–H) or auto-split by double newlines
- `parse_question_groups(text)` — Route to 14 type-specific parsers:
  - `TFNG`, `YNNG` — Statement lists
  - `MCQ`, `MCQ_MULTI` — Questions with A–D/E options
  - `PARAGRAPH_MATCHING` — Info descriptions → paragraph letter
  - `HEADING_MATCHING` — Heading list (i–x Roman numerals) → paragraph mapping
  - `SUMMARY_COMPLETION` — Gapped text, answers from passage
  - `SUMMARY_WORDBANK` — Gapped text + word list (A–I)
  - `SENTENCE_COMPLETION` — Sentences with blanks
  - `SENTENCE_ENDING` — Sentence starts + ending list (A–G)
  - `PERSON_MATCHING` — Statements + person/feature list
  - `SHORT_ANSWER` — Questions with "NO MORE THAN X WORDS" constraint
  - `DIAGRAM_LABEL` — Labels for visual elements (only 3 PDFs, may need manual)
  - `TABLE_COMPLETION` — Table/notes with blanks

### 2. Build `structure_with_llm.py`
**Location**: `/Users/tengda/Antigravity/IELTS/structure_with_llm.py`

For each pre-parsed item, send to Gemini 2.5 Flash to:
1. Clean OCR artifacts and fix split words
2. Generate correct answers (flagged `answer_source: "llm_generated"`)
3. Validate question count = 13 per passage

**API key**: Reuse `GEMINI_API_KEY` from `/Users/tengda/Antigravity/toefl-2026/backend/.env`

### 3. Run pipeline → output to `/Users/tengda/Antigravity/IELTS/parsed/`
- One JSON per passage (schema in implementation plan)
- `_index.json` master index
- Start with 20-passage pilot, then process remaining 110

### 4. Build `validate_parsed.py`
Post-parse validation: schema conformance, question counts, type coverage.

---

## Known Bug

> **Filename apostrophe issue**: File `38. P2 - Egypt's ancient boat-builders 古埃及造船.pdf` has a curly/smart apostrophe (`'` U+2019) in the filename that causes `FileNotFoundError` when passed through Python string literals in shell. 
>
> **Fix**: Use `os.listdir()` to get exact filenames rather than hardcoding paths. Always iterate files from the directory listing, never construct paths from the PDF numbering/naming pattern.

---

## Reference Files

- **Approved implementation plan**: [implementation_plan.md](file:///Users/tengda/.gemini/antigravity/brain/0ca47c9a-6249-468e-a1dc-f87bac1e1580/implementation_plan.md)
- **JSON schema**: Defined in implementation plan under "Proposed JSON Schema"
- **Question type enum**: 14 types defined in implementation plan
- **PDF folder**: `/Users/tengda/Antigravity/IELTS/IELTS Reading 130/`
- **TOEFL backend .env (for Gemini key)**: `/Users/tengda/Antigravity/toefl-2026/backend/.env`

---

## Environment Notes

- Python available via TOEFL venv: `source /Users/tengda/Antigravity/toefl-2026/backend/venv/bin/activate`
- `PyPDF2` is installed in that venv
- `google-genai` is installed (for Gemini API)
- `pdfplumber` and `pymupdf` are NOT installed (use PyPDF2)
