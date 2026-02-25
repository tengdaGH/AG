---
name: pilot_test_flow
description: Automated pilot agent that verifies the complete TOEFL 2026 test flow against ETS spec expectations
---

# Pilot Test Flow Agent

Use this skill to run an end-to-end verification of the TOEFL 2026 test flow. The agent clicks through every item and validates each screen against ETS spec expectations.

> **Crucial Reference:** The exact delivery sequence (e.g., hidden questions during audio, strict forward navigation, split-screen timings) is documented at the bottom of each task spec file inside `/Users/tengda/Antigravity/toefl-2026/specs/task_types/*.md` under the `3. Interaction & Delivery Mechanics` section. Your verification MUST ensure the interface respects these specific mechanics!

## Expected Flow (ETS Spec)

The test MUST follow this exact section order: **Reading → Listening → Writing → Speaking**

### Expected Screens

```
1. LOADING         → "Assembling Your Test..." text visible
2. SECTION_INTRO   → "Section 1 of 4" + "Reading Section" + "Begin Section" button
3. READING items   → Mix of:
   - Complete the Words (cloze gaps with input fields)
   - Read in Daily Life (split-screen: passage left, MCQ right)
   - Read Academic Passage (split-screen: passage left, MCQ right)
4. SECTION_INTRO   → "Section 2 of 4" + "Listening Section"
5. LISTENING items  → Mix of:
   - Choose the best response (dialogue + options)
   - Listen to a Conversation (transcript + questions)
   - Listen to an Announcement (transcript + questions)
   - Listen to an Academic Talk (transcript + questions)
6. SECTION_INTRO   → "Section 3 of 4" + "Writing Section"
7. WRITING items   → In order:
   - Build a Sentence (drag-and-drop word fragments)
   - Write an Email (prompt + editor)
   - Write for an Academic Discussion (professor post + student posts + editor)
8. SECTION_INTRO   → "Section 4 of 4" + "Speaking Section"
9. SPEAKING items  → In order:
   - Listen and Repeat (image + audio)
   - Take an Interview (video + record)
10. SCORE          → Score Report Dashboard with band scores
```

### Verification Checklist

For EACH item, verify:
- [ ] Task type label or header is visible
- [ ] Real content from DB is displayed (not blank/placeholder)
- [ ] Interactive elements are present (radio buttons, inputs, editors)
- [ ] No JavaScript errors in console

For EACH section transition, verify:
- [ ] Correct section number (1-4)
- [ ] Correct section name
- [ ] "Begin Section" button works

For the score report, verify:
- [ ] Page renders without crash
- [ ] Band scores visible
- [ ] Section scores visible

## How to Run

Use the `browser_subagent` tool with the following task:

```
Navigate to http://localhost:3000/test-session/full

VERIFICATION PROTOCOL:
1. Wait for loading to complete — check text says "Assembling Your Test..."
2. When section intro appears, check:
   - Section number matches expected (1 of 4, 2 of 4, etc.)
   - Section name matches expected (Reading, Listening, Writing, Speaking)
   - Click "Begin Section"
3. For each item:
   - Read the header/label to identify the task type
   - Check the DOM for real content (text passages, options, inputs)
   - Check for any error messages or blank areas
   - If radio buttons exist, select one to test interactivity
   - Click "Next" to advance
4. Count total items per section
5. After "Finish Test", verify the score report renders

REPORT FORMAT:
For each item: [Section] Item N: [TaskType] — [PASS/FAIL] [details]
Summary: Total items, items passed, items failed, sections verified
```

## Pass Criteria

| Check | Pass | Fail |
|-------|------|------|
| Section order | R→L→W→S | Any other order |
| All 12 task types present | At least 1 of each | Any type missing |
| Content visible | Real text/questions shown | Blank or placeholder |
| Score report | Renders with bands | Crash or blank |
| Total items | ≥ 18 | Below 18 |
