# Read an Academic Passage

**Section**: Reading
**CEFR Range**: B1–C2 (academic proficiency)

## Construct

Measures the ability to read and comprehend short expository passages typical of secondary and higher education. Assesses academic reading skills including understanding main ideas, details, vocabulary in context, inferences, rhetorical structure, and relationships between ideas.

## Format

- **Stimulus**: Short expository passages (~200 words) from academic subject areas
- **Subject areas**: History, art and music, business and economics, life science, physical science, social science
- **Questions**: Typically 5 multiple-choice questions per passage

## Question Types

Questions may ask about:
- Factual information
- Vocabulary in context
- Inferences
- Relationships between ideas
- Purpose of part or all of the text

## Constraints

- **MCQ Quality**: All multiple-choice questions MUST strictly adhere to the guidelines in `.agent/knowledge/item-quality/mcq_item_quality.md` to ensure psychometric validity.
- Background knowledge must NOT be required
- Topics drawn from common academic subject areas
- Passages must be self-contained and comprehensible without prior knowledge
- Standard academic written English

## Skills Assessed

- Identify the main ideas and basic context of a short, linear text
- Understand the important details in a short text
- Understand the range of grammatical structures used by academic writers
- Infer meaning from information that is not explicitly stated
- Understand a broad range of academic vocabulary
- Understand a range of figurative and idiomatic expressions
- Understand ideas expressed with grammatical complexity
- Understand the relationship between ideas across sentences and paragraphs
- Recognize the rhetorical structure of all or part of a written text

## MST Distribution

| Stage | Scored Questions |
|-------|-----------------|
| Stage 1 (Router) | 5 |
| Stage 2 Lower | 0 |
| Stage 2 Upper | 5 |
| Easy path total | 5 |
| Hard path total | 10 |

## Example

**Topic**: Academic passage on a scientific, historical, or social science topic.

**Passage**: ~200-word expository text from an academic source.

**Sample Question Types**:
1. "According to the passage, what is [factual detail]?"
2. "The word '[term]' in paragraph 1 is closest in meaning to..."
3. "What can be inferred from the passage about [topic]?"
4. "The author mentions [detail] in order to..."
5. "Which of the following best describes the organization of the passage?"

**Golden Standard MCQ Example**:

*Passage Excerpt: "...Because of their small size, hummingbirds have extremely high metabolic rates. To maintain this energy output, they must consume nectar frequently. If a hummingbird fails to feed for even a few hours, it may enter a state of torpor—a hibernation-like reduction in body temperature—to prevent starvation."*

**Question**: The author mentions that hummingbirds enter a state of "torpor" in order to...
- A) reduce their overall body size over time.
- B) avoid freezing during very cold weather.
- C) conserve energy when food is unavailable.
- D) digest the large amounts of nectar they consume.

**Key**: C
**Distractor Rationales**: 
*   **A (reduce their overall body size)**: Plausible because "small size" is mentioned in the first sentence, but an erroneous cause-and-effect relationship.
*   **B (avoid freezing)**: Plausible because "reduction in body temperature" is mentioned, but misinterprets the primary causal driver (starvation/energy).
*   **C (conserve energy)**: Correct. It directly paraphrases "prevent starvation" and links to the high "energy output" context.
*   **D (digest large amounts of nectar)**: Plausible because "consume nectar frequently" is stated, but misattributes the purpose of torpor.
*   *Note on Parity: Option lengths are near-identical, varying from 7 to 9 words. No distinct grammatically clued outliers.*


## Interaction & Delivery Mechanics
### Delivery Sequence & States
1. **Initial State (Passage Only)**: When the item first loads, only the passage is visible (full width). The user must scroll to the bottom of the passage.
2. **Interactive State (Split-Screen)**: Only after clicking "Next" from the passage-only view does the screen split (50/50). The passage is anchored on the left, and the question appears on the right.
3. **Scroll Behavior**: The left and right panels scroll completely independently.
4. **Text Selection**: Highlighting behavior depends on the question type. Sometimes a vocabulary word is pre-highlighted in yellow (`#FFF2CC`) and clicking the highlight may anchor the scroll.
5. **Navigation**: Native free navigation. The user has access to `Back`, `Next`, and `Review` buttons to jump between questions within the Reading section safely.
