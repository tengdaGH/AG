---
name: item_bank_management
description: Managing, versioning, and previewing test items in the TOEFL 2026 platform.
---

# Item Bank Management Skill

This skill provides instructions on how to maintain the TOEFL 2026 Item Bank, including versioning, exposure tracking, quality assurance, and schema integrity.

## 🏛 Database Schema
Items are stored in the `test_items` table with the following audit fields:
- `version`: Integer tracking the number of revisions.
- `generated_by_model`: The AI model or human author responsible.
- `exposure_count`: Number of times the item has been served in tests.
- `created_at` / `updated_at`: Timestamps for age and freshness tracking.

### Canonical Question Schema
All questions **must** use these exact keys:
```json
{
  "text": "What is the main idea?",
  "options": ["A", "B", "C", "D"],
  "correct_answer": 0
}
```

> [!WARNING]
> Legacy items may use non-standard keys. Known variants that need normalization:
> - `question_text` → `text`
> - `stem` → `text`
> - `correct_option_index` → `correct_answer`
> - `correct` → `correct_answer`
> - Letter answers (`"A"`, `"B"`) → integer indices (`0`, `1`)
> - `options` as `dict` → convert to `list`

### Canonical Content Keys
- **Reading**: passage text must be in `text` (not `passage` or `content`)
- **Listening LCR**: uses `dialogue` array (not `text`)
- **Listening Conversation**: uses `text` with F:/M: speaker labels
- **Listening Announcement/Talk**: uses `text` for monologic transcript

## 🛠 Admin Tools

### Dashboard
Location: `/dashboard/admin/items`
- **Filters**: Use the "Section" and "Status" dropdowns to filter the view.
- **In-Page Preview**: Click on any **Content Title** to open a modal preview.
- **Age Tracking**: Monitor the "Age" column to identify items that may need rotation (Shelf life: 2 years).

### Item Editor
Location: `/dashboard/admin/items/[id]/edit`
- **Type-Specific Fields**: The editor layout changes based on the item type.
- **Preview Toggle**: Use the "Eye" icon to toggle between raw editing and student-facing preview.
- **Saving**: Saving an item should automatically increment its `version`.

## 🔍 Quality Assurance (QA)

### Comprehensive Audit Script
[audit_items.py](file:///Users/tengda/Antigravity/toefl-2026/agents/scripts/audit_items.py) runs a full compliance check across all items:

```bash
cd toefl-2026
source backend/venv/bin/activate
python agents/scripts/audit_items.py
```

**Checks performed:**
| Section | Check |
|---------|-------|
| Listening | Audio file exists, transcript text ≥20 words, questions have text + options + answer |
| Reading (Academic) | Passage ≥50 words, questions present |
| Reading (Daily Life) | Text ≥3 words or situation field exists |
| Reading (C-Test) | Passage present (short is OK for C-Test format), questions present |
| Reading (Discussion) | Professor prompt ≥5 words |

### Manual QA Checklist
1. `Complete the Words` items should have exactly 10 blanks
2. Academic Passages should have ~5 questions spanning different cognitive levels
3. Listening Conversations should have 4–5 MCQs covering main idea, detail, inference

## 📊 Psychometric Policies
1. **Exposure / Burn Rate**: If `exposure_count > 500`, flag for retirement.
2. **IRT Parameters**: Items start with estimated `irt_difficulty` (b-parameter). After ~100 administrations, recalibrate using actual response data.

## 🧹 Maintenance Operations

### Delete Empty Shells
Items with no title and no questions are broken generation artifacts:
```python
# Find and delete empty shells for any task type
for item in db.query(TestItem).filter(TestItem.task_type == TaskType.COMPLETE_THE_WORDS).all():
    c = json.loads(item.prompt_content)
    if not c.get('title') and not c.get('questions'):
        db.delete(item)
db.commit()
```

### Frontend Text Resolution
`content-utils.ts` resolves passage text via this fallback chain:
```
raw.text || raw.passage || raw.content || raw.situation || raw.scenario || raw.professor_prompt || raw.professorQuestion || raw.question
```
If a new key is introduced in generation, it must be added to this chain.
