# Writing Task Types

> See also: `specs/task_types/writing_*.md` and `specs/rubrics/writing_*.md`

## 1. Build a Sentence (10 items, ~6 min)

| Property | Value |
|----------|-------|
| Count | 10 per test |
| Time | ~6 min total (~36 sec each) |
| Format | Scrambled words/phrases → drag into correct order |
| Words per sentence | 5–7 |
| Scoring | 1/0 per item (key-scored, exact match) |
| DB task_type | `BUILD_A_SENTENCE` |
| Items in bank | 120 |

**Mechanic**: Drag-and-drop interface. Words/phrases displayed in randomized order. Test-taker arranges them into a grammatically correct sentence. Snap-to-slot logic. Tests syntax and word order knowledge.

---

## 2. Write an Email (1 item, 7 min)

| Property | Value |
|----------|-------|
| Count | 1 per test |
| Time | 7 min |
| Format | Read scenario → compose email |
| Expected length | ~50+ words |
| Scoring | 0–5 (AI engine + human rater) |
| Features | Content elaboration, social conventions, syntactic variety, accuracy |
| DB task_type | `WRITE_AN_EMAIL` |
| Items in bank | 35 |

**Mechanic**: Split-screen — scenario/prompt on left, email editor on right. Editor has To/Subject fields (pre-filled), Cut/Paste/Undo/Redo toolbar (ETS isolated clipboard), word count display. OS clipboard is blocked.

**Rubric highlights** (from `specs/rubrics/writing_email_rubric.md`):
- Band 5: Fully addresses all bullets, appropriate register, varied syntax
- Band 3: Addresses most points, basic vocabulary, some errors
- Band 1: Off-topic or too short to evaluate

---

## 3. Write for an Academic Discussion (1 item, 10 min)

| Property | Value |
|----------|-------|
| Count | 1 per test |
| Time | 10 min |
| Format | Read professor's post + 2 student responses → write your contribution |
| Expected length | ~100+ words |
| Scoring | 0–5 (AI engine + human rater) |
| Features | Content elaboration, syntactic variety, lexical accuracy |
| DB task_type | `WRITE_ACADEMIC_DISCUSSION` |
| Items in bank | 86 |

**Mechanic**: Discussion board UI. Professor's question and two student posts shown on the left. Editor on the right with the same ETS toolbar. Test-taker contributes to the discussion with a clear opinion and supporting ideas. Same format as pre-2026 "Writing for an Academic Discussion" task.

**Rubric highlights** (from `specs/rubrics/writing_academic_discussion_rubric.md`):
- Band 5: Well-developed contribution, engages with prior posts
- Band 3: Addresses topic but limited development
- Band 1: Minimal/off-topic
