# IELTS Global Context & Task Handover

## 1. Global Project Context: IELTS Academic
**CRITICAL:** All development, design research, UI/UX implementation, data structures, and content processing for the IELTS project within this workspace are strictly targeted at the **IELTS Academic** test format. 
* Do not apply rules, task types, or UI constraints from the IELTS General Training test.
* Assume all Reading passages, Writing prompts, and Listening contexts are Academic level and format.

---

## 2. Next Agent Instructions: UI Design Research for Listening & Writing

**To the Next Agent:**
Your primary objective is to replicate the UI/UX design research previously completed for the IELTS Reading test, but this time focusing on the **Listening** and **Writing** sections of the Computer-Delivered IELTS test.

### Step 1: Video Sources
Use the `search_web` tool or YouTube search to find the official, in-depth computer-based test tutorials. They are part of the exact same official series as the Reading tutorial you are following up on.
* 🔍 **Target Video 1:** `"IELTS on computer - Listening test tutorial"`
* 🔍 **Target Video 2:** `"IELTS on computer - Writing test tutorial"`
* Make sure you are referencing the official tutorials (typically published by IELTS Official, British Council, or IDP).

### Step 2: Browser Subagent Analysis
Deploy the `browser_subagent` to watch both tutorials. Ensure the browser is full-screen and free of YouTube UI overlays when capturing.
* **Listening UI Targets:** Capture the volume control UI, audio playback/progress indicators, multiple-choice selection layouts, map/diagram labeling interactive interfaces, and the end-of-section review screen.
* **Writing UI Targets:** Capture the layout for Writing Task 1 (Academic graph/chart pane vs. writing area) and Task 2, text input styling, real-time word count indicators, scrollbars, and any active text states.
* **Deliverables:** Take at least 5-10 screenshots per section. Rely on the WebP browser recording to capture dynamic interactive states (e.g., hover effects, drag-and-drop mechanics).

### Step 3: Synthesis & Documentation
Analyze the final media to extract the specific Design DNA for Listening and Writing, comparing them to the foundational DNA already established.
* **Action:** Expand the existing design library document at `/Users/tengda/Antigravity/themes-and-designs/ielts-computer-design-dna/README.md`.
* **Action:** Add detailed new sections for `## Listening Section UI` and `## Writing Section UI`. Document any unique layout patterns or interactive components specific to these sections.
* **Action:** Move all newly generated `.png` screenshots and `.webp` recordings to `/Users/tengda/Antigravity/themes-and-designs/ielts-computer-design-dna/assets/`.
* **Action:** Embed all new visual assets into the README for a complete reference gallery.

*Note: You MUST refer to the `design_research` skill (`/Users/tengda/Antigravity/.agent/skills/design_research/SKILL.md`) for the standardized operating procedure on how to synthesize and structure this documentation.*
