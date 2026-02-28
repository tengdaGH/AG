# Listen to an Announcement

**Section**: Listening
**CEFR Range**: A2–B2 (academic context announcements)

## Construct

Measures the ability to comprehend short, monologic spoken messages in academic contexts — simulating what a listener would hear during an in-person or broadcasted message in a classroom or school-related event.

## Format

- **Stimulus**: Short academic-related announcement (monologic speech)
- **Content types**: Schedules, directions, rules and regulations, student achievements
- **Context**: Classroom, school event, campus setting
- **Questions**: Multiple-choice questions about the announcement
- **Speakers**: Accents from North America, UK, Australia, New Zealand

## Constraints

- **MCQ Quality**: All multiple-choice questions MUST strictly adhere to the guidelines in `.agent/knowledge/item-quality/mcq_item_quality.md` to ensure psychometric validity.
- Academic context only (school-related settings)
- Monologic format (single speaker)
- Short duration
- No specialized subject knowledge required

## Skills Assessed

- Identify the main ideas and basic context of a short message
- Understand the important details in a short message
- Understand the range of grammatical structures used by proficient speakers
- Understand a wide range of vocabulary including idiomatic and colloquial expressions
- Infer meaning from information that is not explicitly stated
- Predict future actions based on what a speaker has said
- Recognize the purpose of a speaker's message

## MST Distribution

| Stage | Scored Questions |
|-------|-----------------|
| Stage 1 (Router) | 4 |
| Stage 2 Lower | 4 |
| Stage 2 Upper | 0 |
| Easy path total | 8 |
| Hard path total | 4 |

## Example

**Announcement transcript**:
"Good afternoon, everyone. I am excited to inform you that Dr. Cynthia Palmer, a renowned expert in environmental science, will be giving a guest lecture next Monday at 2 pm in Waldman Auditorium. Dr. Palmer will discuss the latest advancements in sustainable energy solutions and their impact on global climate change. Due to her popularity and the high interest in her work, I highly recommend arriving early to secure a seat."


## Visual Asset Generation (Pic Gen)

All visual assets must strictly adhere to the ETS testing visualization guidelines:
- **Style**: Clean, flat, educational textbook style vector art; minimalist and non-distracting.
- **Color Palette**: Muted colors, neutral backgrounds. Avoid overly vibrant or aggressive contrasting colors.
- **Characters**: Use distinct figures (e.g., specific male/female silhouettes) for dialogues, or generic/unisex figures for monologues.
- **No Text**: Do NOT include any readable English text or numbers in the illustrations.
- **Cultural Neutrality**: Settings must be universally recognizable (e.g., standard library, cafeteria) unless specifically dictated by the scenario.

## Interaction & Delivery Mechanics
### Delivery Sequence & States
1. **Introductory Prompt**: Audio introduces the context, e.g., "Now listen to an announcement..."
2. **Audio Playback**: Auto-plays once without controls.
3. **Hidden Question State**: Questions are hidden while the announcement plays.
4. **Question Reveal**: The question appears post-audio.
5. **Strict Navigation**: Forward-only. No back button.
6. **Confirmation Step**: Clicking "Next" requires clicking "OK" to lock in the answer.