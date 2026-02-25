---
name: ielts_reading_pipeline
description: Parsing, structuring, and validating IELTS reading PDF files into standardized JSON format for the assessment platform.
---

# IELTS Reading Pipeline Skill

This skill provides the workflow for converting raw IELTS Reading PDF files into the validated JSON format used by the assessment platform.

## 🛠 Prerequisites
- Python 3.x
- Libraries: `pdfplumber`, `json`, `pathlib`, `re`
- Workspace: `/Users/tengda/Antigravity/IELTS/` directory containing `raw/` (PDFs), `parsed_raw/` (interim JSON), and `parsed/` (final JSON).

## 🚀 The Three-Stage Pipeline

### 1. Raw Extraction
Use `parse_ielts_reading.py` to convert PDF text into a "raw" structured JSON. This script identifies passages, titles, and attempts to isolate question blocks.

```bash
# From the project root
python /Users/tengda/Antigravity/IELTS/parse_ielts_reading.py
```

### 2. Intelligent Structuring (LLM)
Use `structure_with_llm.py` to refine the raw JSON into the final schema. This step uses Gemini to:
- Properly format paragraphs.
- Categorize questions into valid types (e.g., `MATCHING`, `TRUE_FALSE_NOT_GIVEN`).
- Generate answer keys if missing.

```bash
# From the project root
python /Users/tengda/Antigravity/IELTS/structure_with_llm.py
```

### 3. Deterministic Validation
Use `validate_parsed.py` to ensure the final JSON files meet all strict schema requirements (paragraph counts, question ranges, valid types).

```bash
# From the project root
python /Users/tengda/Antigravity/IELTS/validate_parsed.py
```

## 📋 Schema Definition
Final JSON files must include:
- `id`: Unique identifier (e.g., `ielts-r-001`).
- `passage`: Object containing `title` and `paragraphs` (array of strings).
- `question_groups`: Array of objects containing `type`, `instruction`, `question_range`, and `questions`.
- `questions`: Array of objects with `number`, `text`, `options` (optional), and `answer`.

## 🧪 Common Question Types
- `MATCHING`: Heading matching (Roman numerals).
- `TRUE_FALSE_NOT_GIVEN`: T/F/NG logic.
- `NOTES_COMPLETION`: Gap fill / Summary completion.
- `MULTIPLE_CHOICE`: Standard MCQs.
