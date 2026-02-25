# CD-IELTS Interaction Model & Delivery Mechanics

Unlike the TOEFL which uses distinct "task shells" per item type, the Computer-Delivered IELTS (CD-IELTS) operates on a **Unified Test Shell**. The mechanics are governed globally by the shell, with specific interactive nuances for reading, listening, and writing.

## 1. The Universal Shell & Navigation

1. **Bottom Navigation Grid**: The primary method of moving between questions is a numbered grid located at the bottom of the screen.
2. **State Indicators**:
    * **Unanswered**: Number boxes have a default background (usually black/dark grey).
    * **Answered**: Once text is input or an option selected, the corresponding number box changes styling (e.g., an underline appears or background changes) to indicate completion.
    * **Review**: Users can explicitly flag a question for "Review". This changes the number box shape/color (often from square to a circle) to remind them to double-check their answer later.
3. **Directional Controls**: Dedicated "Back" and "Next" arrows flank the navigation grid, allowing sequential movement.
4. **Global Timer**: A persistent countdown timer sits at the top center of the screen, tracking total section time.

## 2. Tools Layer

1. **Highlighter**: Users can click and drag to select any text in a reading passage or listening prompt. Right-clicking the selection opens a context menu to apply a yellow highlight.
2. **Notes**: Along with highlighting, users can select "Notes" from the right-click menu to attach a small text box to a specific part of the text.

## 3. Reading Section Mechanics

1. **Split-Screen Layout**: The screen is vertically split ~50/50 by a **resizable drag handle** (↔ icon). The reading passage is on the left; the question set is on the right.
2. **Independent Scrolling**: The left passage and right questions scroll entirely independently.
3. **Question Types (10 verified)**: See `themes-and-designs/ielts-computer-design-dna/README.md` for the complete taxonomy:
   - **Selection-Based**: MCQ Single (radio), MCQ Multi (checkbox, enforces limit), T/F/NG (radio), Matching Features (radio-matrix grid).
   - **Text Input**: Note Completion, Table Completion, Sentence Completion, Summary Completion from Text — all use `144px` inline `<input>` with blue focus border + box-shadow.
   - **Drag-and-Drop**: Summary Completion from a List (word bank pills), Matching Headings, Matching Sentence Endings — use pill bank → dashed drop zones, single-use/swap mechanics.
4. **Deselection Rules**: In the **real test**, radio buttons (MCQ single, T/F/NG, matrix) **DO** support deselection (click to uncheck) — this must be custom-implemented as it differs from native HTML radio behavior. *(Note: the Inspera sample demo does NOT support this, but the real test does — confirmed via official walkthrough.)* Checkboxes (MCQ multi) also support deselection. Drag-and-drop pills can be dragged back out.
5. **Footer Status**: Green bar for selection types, "Attempted" text for input/DnD types — triggered immediately on first interaction.

## 4. Listening Section Mechanics

1. **Unified Audio**: Audio playback is centrally controlled by the test shell.
2. **Inline Volume Control**: A volume icon (often in the top right) expands into a slider, allowing users to adjust their headset volume dynamically during the test without pausing the audio.
3. **Tab Navigation**: Due to the rapid pace, users can use the `Tab` key on their keyboard to quickly jump focus from one input field to the next (crucial for form completion tasks).

## 5. Writing Section Mechanics

1. **Split-Screen Layout**: The prompt (e.g., a chart for Task 1, or prompt text for Task 2) is on the left; the text input area is on the right. Both sides scroll independently.
2. **Live Word Count**: A real-time word counter sits below the text input area, continuously updating as the user types to ensure they meet the minimum length requirements (e.g., 150 words for Task 1; 250 words for Task 2).
3. **Drafting Tools**: Basic editing shortcuts (Ctrl+C to copy your own text, Ctrl+V to paste, Ctrl+Z to undo) are supported *within* the text editor area to facilitate drafting.
