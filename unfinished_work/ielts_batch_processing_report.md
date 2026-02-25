# IELTS Reading Item Bank — Batch Processing Report

> **Date:** 2026-02-25  
> **Status:** ⚠️ INCOMPLETE — 92 files still need LLM structuring  
> **Blocker:** macOS proxy (Surge/Clash) black-holes all requests to `api.minimaxi.chat`

---

## 1. Project Context

We are building a comprehensive IELTS Academic Reading item bank. The source material is a single 46MB PDF (`IELTS/雅思阅读new最全题库.pdf`) containing **3,291 pages** of practice tests — each test containing reading passages, questions, and answer keys. 

The ingestion pipeline has **three phases:**

```
Phase 1: PDF → Extracted JSON       (COMPLETE ✅ — 651 files)
Phase 2: Extracted → Structured JSON (INCOMPLETE ⚠️ — 551/651)
Phase 3: Validation & QA            (NOT STARTED)
```

### 1.1 Pre-Existing Item Bank

Before this pipeline, there was already a curated bank of **130 individual passage PDFs** in `IELTS/IELTS Reading 130/`, processed through an earlier pipeline into `IELTS/parsed/` (129 files with 3-digit IDs like `ielts-r-001.json`). The new pipeline produces 4-digit IDs (`ielts-r-0001.json`) into `IELTS/parsed_v2/`.

### 1.2 Key Directories

| Directory | Description | Count |
|---|---|---|
| `IELTS/雅思阅读new最全题库.pdf` | Source PDF (46MB, 3,291 pages) | 1 file |
| `IELTS/IELTS Reading 130/` | Original curated PDFs (individual passages) | 130 PDFs |
| `IELTS/extracted/` | Phase 1 output — raw JSON from PDF extraction | 651 files |
| `IELTS/parsed/` | Old item bank (v1 pipeline, 3-digit IDs) | 129 files |
| `IELTS/parsed_v2/` | Phase 2 output — LLM-structured JSON | 551 files |
| `IELTS/broken/` | Error stubs from failed Phase 2 runs | 0 (cleared) |
| `IELTS/parsed_raw/` | Debug artifacts from earlier testing | misc |
| `IELTS/pdf_text_dump/` | Raw text dumps from PDFs for verification | 131 files |
| `IELTS/scripts/` | All pipeline scripts | — |
| `IELTS/specs/` | IELTS interaction model specs | — |

### 1.3 Key Scripts

| Script | Purpose |
|---|---|
| `scripts/structure_v2.py` | **Phase 2 core** — sends extracted JSON to Minimax LLM API to produce structured passage + questions JSON. Uses `curl` subprocess (not Python HTTP) to bypass macOS networking issues. Supports `--workers N` for concurrency and `--test-id` for single-file testing. |
| `scripts/validate_and_verify.py` | **Phase 3** — validates structured JSON files for correct passage structure, question types, answer keys, and counts. |
| `scripts/monitor_progress.py` | Real-time progress monitor for the batch job. |

---

## 2. What Was Done

### 2.1 Phase 1: PDF Extraction (COMPLETE ✅)

The source PDF was split into 651 individual JSON files in `IELTS/extracted/`. Each file contains:
- `title`: passage title
- `passage_text`: raw text of the reading passage  
- `questions_text`: raw text of all questions
- `answer_keys`: answer key text (if present)
- Additional metadata from the PDF structure

### 2.2 Phase 2: LLM Structuring (551/651 DONE)

`structure_v2.py` sends each extracted JSON to the **Minimax API** (`api.minimaxi.chat`, model `MiniMax-Text-01`) with a carefully crafted prompt to produce structured output:
- Clean passage text (paragraphs separated, formatting fixed)
- Questions parsed into typed objects (MCQ, True/False/Not Given, Matching, Gap Fill, etc.)
- Answer keys linked to individual questions
- Metadata (difficulty markers, passage position, etc.)

**Configuration used for the batch run:**
- Workers: 10 (ThreadPoolExecutor)
- API timeout: 60s hard limit via `curl -m 60`
- Retry logic: up to 8 attempts per file with exponential backoff
- Skip logic: files already in `parsed_v2/` are skipped automatically

**Results:**
- **551 files** successfully structured → `parsed_v2/`
- **100 files** failed due to API timeouts (curl exit code 28)
- Total runtime: ~2h 55min
- The script ran via `nohup` in the background

### 2.3 The Timeout Problem

The 100 failures are **all** curl exit code 28 — 60-second timeout with 0 bytes received. Root cause:

1. A macOS system proxy (Surge/Clash) intercepts outbound HTTP connections
2. Connections to `api.minimaxi.chat` are routed through a tunnel that silently drops packets
3. No TCP RST or FIN is returned, so the connection hangs forever
4. The earlier version of the script used Python's `openai` library and `requests`/`httpx`, which **hung indefinitely** — the fix was switching to `curl` subprocess with a hard `-m 60` timeout
5. `curl` catches the timeout but can't actually deliver the request

**Three retry attempts were made** (with 3–10 workers each) — all failed identically. The proxy must be **disabled** before retrying.

### 2.4 Cross-Reference Against Old Item Bank

We fuzzy-matched the 100 failed file titles against the 130-item bank titles (from `parsed/`):

**8 files are already covered** by the old item bank:

| Failed File | Title | Old Bank Match |
|---|---|---|
| `ielts-r-0001` | A Brief History of Tea | `ielts-r-001` (100%) |
| `ielts-r-0070` | Bird Migration | `ielts-r-036` (100%) |
| `ielts-r-0194` | Grimm's Fairy Tales | `ielts-r-069` (100%) |
| `ielts-r-0394` | Skyscraper Farming | `ielts-r-047` (100%) |
| `ielts-r-0399` | SOSUS: Listening to the Ocean | `ielts-r-009` (86%) |
| `ielts-r-0475` | The Fluoridation Controversy | `ielts-r-088` (100%) |
| `ielts-r-0476` | The Fruit Book | `ielts-r-089` (100%) |
| `ielts-r-0641` | William Gilbert and Magnetism | `ielts-r-031` (100%) |

**92 files are truly missing** and must be reprocessed.

### 2.5 Text Dump for Verification

A raw text extraction from the source PDF was created for future content verification:
- **File:** `IELTS/pdf_text_dump/雅思阅读_全题库_dump.txt` (4.9 MB)
- **Pages:** 3,291 pages extracted
- **Format:** `========== PAGE N ==========` delimiters between each page
- **Purpose:** Can be used to verify that the LLM-structured output in `parsed_v2/` faithfully represents the original PDF content

---

## 3. What Remains

### 3.1 Re-process 92 Failed Files (BLOCKED)

**Prerequisite:** Disable the macOS proxy (Surge/Clash).

```bash
cd /Users/tengda/Antigravity/IELTS
rm -f broken/*.json                    # Clear any stale error stubs
source /Users/tengda/Antigravity/toefl-2026/backend/venv/bin/activate
python -u scripts/structure_v2.py --workers 5
```

The script will skip the 551 already in `parsed_v2/` and process only the remaining 100. At ~5 workers, this should take ~20-30 minutes.

### 3.2 Run Phase 3 Validation

After all files are structured:

```bash
python scripts/validate_and_verify.py
```

This checks every file in `parsed_v2/` for:
- Valid passage structure (title, paragraphs, metadata)
- Question type integrity (MCQ options, gap fill blanks, matching pairs)
- Answer key completeness and correctness
- Question count ranges

### 3.3 Content Verification Against Source PDF

Use the text dump (`pdf_text_dump/雅思阅读_全题库_dump.txt`) to verify that the LLM-structured passages match the original PDF content. This could be done via:
- Title matching between `parsed_v2/` files and the text dump
- Passage text similarity scoring
- Answer key spot-checking

### 3.4 Merge Old + New Item Banks

The old 130-item bank (`parsed/`, 3-digit IDs) and new bank (`parsed_v2/`, 4-digit IDs) use different JSON schemas. A merge step may be needed to:
- Deduplicate overlapping passages
- Normalize to a single schema
- Assign final canonical IDs
- Ingest into the backend database

---

## 4. Technical Notes for Future Agents

### 4.1 The macOS Proxy Problem

This is the #1 gotcha. If API calls to Minimax hang or timeout:
- **Python's native HTTP libraries** (`requests`, `httpx`, `openai` SDK) will **hang forever** — no timeout parameter works because the proxy swallows the TCP connection
- The **only reliable approach** is `subprocess.run(["curl", "-m", "60", ...])` which enforces a hard OS-level timeout
- If curl returns exit code 28 (timeout), the proxy is active and blocking the connection
- **Solution:** User must disable the proxy, or use a direct network connection

### 4.2 Environment Setup

- **Python venv:** `/Users/tengda/Antigravity/toefl-2026/backend/venv/bin/python`
- **Required packages:** `openai`, `PyPDF2` (installed in venv)
- **API key:** `MINIMAX_API_KEY` loaded from `IELTS/.env`
- **API endpoint:** `https://api.minimaxi.chat/v1/text/chatcompletion_v2`
- **Model:** `MiniMax-Text-01`

### 4.3 Running with nohup

When running long batch jobs:
```bash
PYTHONUNBUFFERED=1 nohup /Users/tengda/Antigravity/toefl-2026/backend/venv/bin/python -u scripts/structure_v2.py --workers 5 > process_v2_retry.log 2>&1 &
```
- `PYTHONUNBUFFERED=1` and `-u` flag prevent output buffering with nohup
- Without these, the log file will appear empty until the process finishes
- Use `tail -f process_v2_retry.log` to monitor

### 4.4 File ID Mapping

- Old bank: 3-digit IDs (`ielts-r-001` to `ielts-r-129`) in `parsed/`
- New bank: 4-digit IDs (`ielts-r-0001` to `ielts-r-0651`) in `parsed_v2/`
- IDs do **NOT** correspond between banks — matching must be done by passage title/content
- The `extracted/` directory contains the raw input for the new pipeline
