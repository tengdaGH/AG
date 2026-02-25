---
name: listening_item_classification
description: Classifying, validating, and reclassifying TOEFL 2026 listening items based on the official RR-25-12 spec.
---

# Listening Item Classification Skill

This skill provides the rules and tooling for ensuring every listening item in the item bank is assigned the correct `task_type` based on the official TOEFL 2026 Technical Manual (RR-25-12).

## 📋 Classification Rules

### Listen and Choose a Response (`LISTEN_CHOOSE_RESPONSE`)
- **Format**: ≤2 dialogue lines + exactly 1 question asking for "the most appropriate response"
- **CEFR**: A1–B2
- **Content**: Single spoken utterance (question/statement) → 4 written response options
- **Key signal**: `dialogue` array + 1 question with "appropriate response" in text

### Listen to a Conversation (`LISTEN_CONVERSATION`)
- **Format**: Multi-turn `text` with speaker labels (F:/M:) + ≥3 MCQ questions
- **CEFR**: A2–C1
- **Content**: Full dialogue between 2 speakers (100–180 words)
- **Key signal**: `text` field with speaker turn markers + multiple questions about meaning/inference

### Listen to an Announcement (`LISTEN_ANNOUNCEMENT`)
- **Format**: Monologic `text` (80–150 words) + 2–3 MCQ questions
- **CEFR**: A2–B2
- **Content**: Campus-related announcement (schedules, rules, events)
- **Key signal**: Monologic text + campus/service context keywords (library, parking, dining, registration)

### Listen to an Academic Talk (`LISTEN_ACADEMIC_TALK`)
- **Format**: Monologic `text` (175–250 words) + 3–5 MCQ questions
- **CEFR**: B1–C2
- **Content**: Academic subject lecture (history, biology, physics, etc.)
- **Key signal**: Monologic text ≥150 words + academic subject context keywords

## 🛠 Script

### [reclassify_listening_items.py](file:///Users/tengda/Antigravity/toefl-2026/agents/scripts/reclassify_listening_items.py)

Deterministic classifier that audits all listening items and reclassifies mismatches.

```bash
cd toefl-2026
source backend/venv/bin/activate

# Dry-run: preview changes
python agents/scripts/reclassify_listening_items.py

# Apply: commit reclassifications to DB
python agents/scripts/reclassify_listening_items.py --apply
```

**Classification logic priority order**:
1. Dialogue key + 1 response question → `LISTEN_CHOOSE_RESPONSE`
2. Multi-turn text with speaker labels + ≥3 questions → `LISTEN_CONVERSATION`
3. Monologic text with campus context → `LISTEN_ANNOUNCEMENT`
4. Monologic text ≥150 words with academic context → `LISTEN_ACADEMIC_TALK`
5. Audio-only items (no transcript): classified by title/context keywords

## ⚠️ Important Notes
- Always run a dry-run first before applying changes
- The script preserves generation notes by prepending reclassification history
- Items with ambiguous context (e.g., "library orientation" could be either announcement or talk) are resolved by campus vs. academic keyword priority

## 🔄 Schema Normalization

After reclassification, always verify question schemas match the canonical format:
```json
{"text": "...", "options": ["A","B","C","D"], "correct_answer": 0}
```
Known legacy variants to normalize:
- `question_text` → `text`, `stem` → `text`
- `correct_option_index` / `correct` → `correct_answer`
- Letter answers (`"A"`) → integer indices (`0`)
- `options` as dict → convert to list

