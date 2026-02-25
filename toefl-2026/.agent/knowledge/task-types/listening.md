# Listening Task Types

> See also: `specs/task_types/listening_*.md` for item generation specs

## 1. Listen and Choose a Response

| Property | Value |
|----------|-------|
| Stage 1 count | 8 |
| Easy path total | 15 |
| Hard path total | 11 |
| Format | Hear one sentence → pick best response from 4 options |
| Audio | Single play, no replay |
| Duration | ~3–5 sec per sentence |
| Scoring | 1/0 per item |
| DB task_type | `LISTEN_CHOOSE_RESPONSE` |
| Items in bank | 150 |

**Mechanic**: Pragmatic response selection. Tests understanding of intent, tone, and conversational context. Audio plays once automatically.

---

## 2. Listen to a Conversation

| Property | Value |
|----------|-------|
| Stage 1 count | 4 |
| Easy/Hard path total | 8 |
| Format | Short conversation + MCQ |
| Audio | ~60–90 sec conversation, single play |
| Speakers | 2 speakers with varied accents (NA, UK, AU, NZ) |
| Scoring | 1/0 per question |
| DB task_type | `LISTEN_CONVERSATION` |
| Items in bank | 20 |

**Mechanic**: Listen to a campus/academic conversation. Questions assess tone, speaker intentions, details, and idiomatic understanding.

---

## 3. Listen to an Announcement

| Property | Value |
|----------|-------|
| Stage 1 count | 4 |
| Easy path total | 8 |
| Hard path total | 4 |
| Format | Campus announcement + MCQ |
| Audio | ~45–75 sec, single play |
| Scoring | 1/0 per question |
| DB task_type | `LISTEN_ANNOUNCEMENT` |
| Items in bank | 21 |

**Mechanic**: Brief campus/institutional announcement. Questions test main purpose, specific details, and implied information.

---

## 4. Listen to an Academic Talk

| Property | Value |
|----------|-------|
| Stage 1 count | 4 |
| Easy path total | 4 |
| Hard path total | 12 |
| Format | Academic lecture/talk + MCQ |
| Audio | ~2–3 min, single play |
| Topics | Science, history, social science, arts |
| Scoring | 1/0 per question |
| DB task_type | `LISTEN_ACADEMIC_TALK` |
| Items in bank | 12 |

**Mechanic**: Academic lecture or discussion. Similar to pre-2026 lecture tasks. Questions on main ideas, supporting details, speaker's attitude, organization.
