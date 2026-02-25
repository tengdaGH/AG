---
name: ielts_ui_development
description: How to build and structure authentic computer-delivered IELTS reading and listening interface components, capturing exact interaction mechanics discovered via official Cambridge test walkthroughs.
tags:
  - ielts
  - authentic
  - ui
  - tsx
  - frontend
---

# IELTS Interactive Component Development

When developing React (TSX) components for the IELTS application, it is absolutely critical that the interface perfectly matches the **Authentic Computer-Delivered IELTS**. 

Do not rely on standard web UI patterns (like radio buttons or standard drop-downs) without heavily customizing them to mimic the exact mechanics observed in the official software. 

## 1. Multiple Choice (Single Answer) & True/False/Not Given
- **Visuals**: Options should be blocks, not just tiny radio dots. The letter `A`, `B`, `C` (or the word `TRUE`, `FALSE`) must be clearly delineated.
- **Selection**: Selecting an item highlights the **entire row** with light blue background (`rgb(187, 216, 240)`).
- **De-selection (Crucial)**: Clicking an *already selected* option **deselects** it (returns the state to `null`). This differs from standard `<input type="radio">` behavior. *(Note: the Inspera demo does NOT support this, but the real test does — confirmed via official walkthrough video.)*
- **Right-Click Strikeout**: Students must be able to right-click an option to apply a visual strike-out effect (e.g., reduced opacity and `line-through` text).

## 1b. Multiple Choice (Pick TWO or more)
- **Input Type**: Square **checkboxes** replace radio buttons.
- **Selection Limit**: The interface **strictly prevents** selecting more than the required number. Extra clicks have no effect — no error, no toggle.
- **De-selection**: Clicking a selected checkbox **DOES deselect** it (unlike radio buttons).
- **Footer State**: "Attempted" shows only when the exact required count is met. 

## 2. Matching Features (Radio-Button Matrix)
- **Grid Layout**: A table grid where rows are numbered items and columns are lettered groups (A, B, C, D, E). Below the grid, a legend maps letters to descriptions.
- **Interaction**: Click intersecting cell to assign — uses **radio buttons within each cell**. One selection per row. Clicking same cell **deselects** it (same as MCQ). Columns CAN be reused across rows.
- **Visual**: Blue radio dot + entire cell highlights light blue on selection.

## 3. Matching Headings / Sentence Endings (Drag-and-Drop)
- **Bank**: A list of draggable "pills". Pill style: `1px solid #C5C5C5` (grey) or `1px solid #0E98F0` (blue) border, `4px` border-radius, white background.
- **Drop Zones**: Dashed-border rectangles (`1px dashed #C5C5C5`, `5px` radius) with centered question number. Active state: `2px dashed #418EC8` (blue).
- **Single-use**: Words/headings are **moved** (not copied). Once placed, they disappear from the bank.
- **Swap / Kickout**: Dragging a new pill into an occupied zone **replaces** the existing one, which returns to the bank.
- **More distractors**: There are typically more pills than gaps (e.g., 6 pills for 3 gaps). 

## 4. Summary/Note/Sentence/Table Completion (Inline Text Inputs)
- **Visual Placement**: Text inputs sit **inline** (`display: inline-block`) within the text flow.
- **Styling**: Width `144px`, height ~`22px`, `1px solid rgb(83, 83, 83)` border, `3px` border-radius, `16px Arial`, padding `0 8px`.
- **Focus State**: `1px solid rgb(65, 142, 200)` border + `box-shadow: rgb(65, 142, 200) 0px 0px 0px 1px` (blue glow).
- **Placeholder**: Question number (e.g., "1") centered in grey.
- **Word Limits**: Do not aggressively truncate — the real CBT allows over-typing but marks wrong later.

## 4b. Summary Completion From a List (Drag-and-Drop Word Bank)
- When the instruction says "Choose the correct answer and **move it into the gap**", use drag-and-drop, NOT text inputs.
- **Word Bank**: Horizontal flex-row of draggable pills at the bottom of the question pane.
- **Pill Style**: White bg, `1px solid #0E98F0` (blue) border, `4px` radius, blue text, `cursor: move`.
- **Drop Zone**: Inline dashed-border `1px dashed rgba(197,197,197,0.75)`, `5px` radius, contains centered gap number.
- **Populated**: Pill docks inside, number is replaced. Same single-use/swap mechanics as Matching Headings. 

## 5. Diagram & Flowchart Labeling
- **Structure**: Rendered as a base image (SVG/PNG) with absolute-positioned text `<input>` fields or drag-and-drop zones overlaid on top of the image via percentage-based `top/left` coordinates.
- **Flowchart**: Small interconnected boxes. If a box requires an answer, it acts similarly to a standard Gap Fill text input.

## Interaction Principles Summary
1. Authenticity over standard web behavior. Radio buttons **DO** support deselection (click to uncheck). This differs from native HTML `<input type="radio">` and must be custom-implemented.
2. Right-click is reserved for UI interactions (strikeout/elimination), not standard browser context menus.
3. Use verified Inspera/IELTS styling tokens:
   - Active/Focus Blue: `#418FC6` / `rgb(65, 142, 200)`
   - Row Highlight: `rgb(187, 216, 240)`
   - Border Default: `rgb(83, 83, 83)` (inputs) / `#C5C5C5` (drop zones)
   - Pill Border: `#0E98F0` (blue) or `#C5C5C5` (grey)
   - Font: `16px Arial, sans-serif`
   - IELTS Logo Red: `#D32F2F`
   - Header BG: `#333333`
4. Refer to `themes-and-designs/ielts-computer-design-dna/README.md` for comprehensive token reference.
