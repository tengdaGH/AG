# Speaking Task Types

> See also: `specs/task_types/speaking_*.md` and `specs/rubrics/speaking_*.md`

## 1. Listen and Repeat (7 items)

| Property | Value |
|----------|-------|
| Count | 7 per test |
| Prep time | None |
| Response time | 8–12 sec per sentence |
| Format | Hear sentence once → repeat immediately |
| Visual | Location-themed image (no text shown) |
| Audio length | 4–6 sec (increasing complexity) |
| Scoring | 0–5 overall (AI-scored) |
| Features scored | Fluency, intelligibility, repeat accuracy |
| DB task_type | `LISTEN_AND_REPEAT` |
| Items in bank | 98 |

**Mechanic**: Audio plays automatically with a contextual background image. No text displayed. Sentences increase in complexity from simple (4 sec) to complex (6 sec). Recording starts immediately after audio ends.

**Rubric highlights** (from `specs/rubrics/speaking_listen_repeat_rubric.md`):
- Band 5: Near-native fluency, all content words reproduced
- Band 3: Intelligible, some omissions/substitutions
- Band 1: Largely unintelligible, major omissions

---

## 2. Take an Interview (4 items)

| Property | Value |
|----------|-------|
| Count | 4 per test |
| Prep time | None |
| Response time | 45 sec per question |
| Format | Simulated video interview, 4 Qs on one topic |
| Visual | Pre-recorded interviewer video |
| Progression | Personal → experience → opinion → broader |
| Scoring | 0–5 overall (AI-scored) |
| Features scored | Fluency, intelligibility, vocabulary/grammar, organization |
| DB task_type | `TAKE_AN_INTERVIEW` |
| Items in bank | 53 |

**Mechanic**: Video of interviewer plays, asks a question. No text shown, no prep time — recording starts immediately. Questions build on a single topic (e.g., "What's your favorite hobby?" → "Why do you think hobbies are important?"). Each response is 45 sec max.

**Rubric highlights** (from `specs/rubrics/speaking_interview_rubric.md`):
- Band 5: Fluent, well-organized responses with varied vocabulary
- Band 3: Generally clear, some hesitation, basic vocabulary
- Band 1: Mostly silent or unintelligible
