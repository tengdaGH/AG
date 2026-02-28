# Read in Daily Life

**Section**: Reading
**CEFR Range**: A1–B2 (primarily lower/mid proficiency, daily life contexts)

## Construct

Measures the ability to comprehend short, nonacademic texts commonly encountered in daily life around the world. Tests practical reading skills including skimming, scanning, and understanding informal language.

## Format

- **Stimulus**: Short nonacademic texts (15–150 words) in formats such as:
  - Poster, sign, or notice
  - Menu
  - Social media post or webpage
  - Schedule
  - Email
  - Chain of text messages
  - Advertisements
  - News article
  - Form, invoice, or receipt
- **Questions**: 2–3 multiple-choice questions per text (depending on text length)

## Constraints

- **MCQ Quality**: All multiple-choice questions MUST strictly adhere to the guidelines in `.agent/knowledge/item-quality/mcq_item_quality.md` to ensure psychometric validity.
- Texts must represent daily life contexts from around the world (not US-centric)
- Nonacademic content only
- No specialized background knowledge required
- Common, accessible topics

## Skills Assessed

- Understand information in common, nonlinear text formats
- Identify the main purpose of a written communication
- Understand informal language, including common idiomatic expressions
- Make inferences based on text
- Understand telegraphic language
- Skim and scan for information

## MST Distribution

| Stage | Scored Questions |
|-------|-----------------|
| Stage 1 (Router) | 5 |
| Stage 2 Lower | 5 |
| Stage 2 Upper | 0 |
| Easy path total | 10 |
| Hard path total | 5 |

## Example

**Format**: Memo/notice

"To all registered students: Beginning October 1st, the Student Health Center will transition to a fully digital appointment system. Walk-in consultations for non-emergencies will no longer be accepted. You must schedule your visit via the university portal at least 24 hours in advance. For sudden acute illness, please call the triage nurse hotline rather than arriving unannounced."

**Question**: What action should a student take if they experience a sudden acute illness after October 1st?
- (A) Walk into the Student Health Center immediately.
- (B) Schedule an appointment 24 hours in advance.
- **(C) Call the triage nurse hotline.** ✓
- (D) Email the university portal administrator.


## Interaction & Delivery Mechanics
### Delivery Sequence & States
1. **Initial State (Passage Only)**: The short daily life text (email, schedule, message) is displayed full width.
2. **Interactive State (Split-Screen)**: Clicking "Next" splits the screen. The text anchors left, the question appears right.
3. **Scroll Behavior**: Independent scrolling.
4. **Navigation**: Native free navigation (`Back`, `Next`, `Review`). The user can freely change answers before finalizing the section.
