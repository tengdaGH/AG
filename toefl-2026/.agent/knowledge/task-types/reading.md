# Reading Task Types

> See also: `specs/task_types/reading_*.md` for item generation specs

## 1. Complete the Words (C-Test)

| Property | Value |
|----------|-------|
| Stage 1 count | 10 |
| Easy path total | 20 |
| Hard path total | 20 |
| Format | Short paragraph with missing letters in words |
| Scoring | 1/0 per item (key-scored) |
| DB task_type | `COMPLETE_THE_WORDS` |
| Items in bank | 99 |

**Mechanic**: A paragraph is shown with certain words having their second half removed. Test-taker types the missing letters to complete each word. Strict character-limit input with auto-advance.

---

## 2. Read in Daily Life

| Property | Value |
|----------|-------|
| Stage 1 count | 5 |
| Easy path total | 10 |
| Hard path total | 5 |
| Format | Short non-academic text + MCQ |
| Content | Emails, menus, social media, announcements, websites |
| Scoring | 1/0 per item |
| DB task_type | `READ_IN_DAILY_LIFE` |
| Items in bank | 44 |

**Mechanic**: Split-screen — passage on left (with optional image), questions on right. Image zoom and drag prevention active. Questions test factual information and inference.

---

## 3. Read an Academic Passage

| Property | Value |
|----------|-------|
| Stage 1 count | 5 |
| Easy path total | 5 |
| Hard path total | 10 |
| Format | ~200 word academic passage + MCQ |
| Topics | History, science, social science, arts |
| Scoring | 1/0 per item |
| DB task_type | `READ_ACADEMIC_PASSAGE` |
| Items in bank | 23 |

**Mechanic**: University-level text followed by questions on main ideas, vocabulary in context, supporting details, and inferences. Shorter than pre-2026 passages (~200 words vs ~700).
