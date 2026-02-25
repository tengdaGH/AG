---
name: toefl_item_generation
description: Generating high-compliance TOEFL 2026 reading items using Antigravity built-in models and official technical manuals.
---

> [!WARNING]
> **COST CONSTRAINT**: The Gemini API should be STRICTLY used for voice generation only. All text and item generation must utilize Antigravity built-in models to avoid cost incurrence.

# TOEFL 2026 Item Generation Skill

This skill provides instructions on how to generate and ingest standardized test items that strictly adhere to the TOEFL 2026 RR-25-12 Technical Manual.

> **Crucial Reference:** When generating content, ensure it aligns with the strict delivery constraints (e.g., hidden questions during audio, plain-text textareas) documented in `/Users/tengda/Antigravity/toefl-2026/specs/task_types/*.md` under the `3. Interaction & Delivery Mechanics` section.

## 🛠 Prerequisites
- Access to `/Users/tengda/Antigravity/toefl-2026/rr_25_12_extracted.txt` in the root (concatenated official manual).
- Backend dependencies installed in `/Users/tengda/Antigravity/toefl-2026/backend/venv`.

## 📖 Key Specifications (RR-25-12)
1. **Read an Academic Passage**:
   - Length: ~200 words.
   - Questions: 5 (factual, vocab, inference, etc.).
   - Tone: Formal, academic, first-language source.
2. **Read in Daily Life**:
   - Length: 15-150 words.
   - Formats: Notice, email, memo, social media.
   - Questions: 2-3 (pragmatic understanding).
3. **Complete the Words (C-Test)**:
   - Format: First sentence intact. Every second word thereafter is truncated.
   - Truncation: Use underscores (e.g., `temp___atures`).
   - Items: Exactly 10 blanks per passage.

## 🚀 How to Generate Items

### Automated Batch Generation
Use the `regenerate_full_items.py` script to generate items in batches. This script handles:
- Batching requests to avoid JSON truncation.
- Automated versioning (stamping with `v1` and model name).
- Proper ingestion into the PostgreSQL database.

```bash
# From the project root
cd /Users/tengda/Antigravity/toefl-2026/backend
source venv/bin/activate
python ../agents/scripts/regenerate_full_items.py
```

### Prompt Engineering Guidelines
When calling Antigravity built-in models for items:
- Always include the first ~15k tokens of `rr_25_12_extracted.txt` in the system prompt.
- Explicitly state "DO NOT TRUNCATE PASSAGES" as models tend to abbreviate.
- Request 3-stage CEFR distribution (e.g., A2, B1, B2 or B2, C1, C2).

## 🧪 Verification
After generation, verify integrity using the backend shell:
```python
from app.database.connection import SessionLocal
from app.models.models import TestItem
db = SessionLocal()
items = db.query(TestItem).all()
# Check word counts and JSON validity
```
