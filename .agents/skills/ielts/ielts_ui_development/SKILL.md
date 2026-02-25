---
name: ielts_ui_development
description: Guidelines for building and maintaining the Computer-Delivered IELTS (CD-IELTS) Reading Test interface.
---

# IELTS UI Development Skill

This skill provides the architectural guidelines for maintaining the CD-IELTS Reading interface, ensuring high authenticity and functional parity with official testing software.

> **Crucial Reference:** Always consult the official unified delivery blueprint at `/Users/tengda/Antigravity/IELTS/specs/interaction_model.md` for exact state machines and behavioral nuances before implementing UI changes!

## 🏗 Core Architecture

### 1. Split-Screen Layout
The IELTS workspace must maintain a strict 50vw/50vw split using the `SplitPane` component.
- **Independent Scrolling**: Each pane must have `overflow-y-auto` and maintain its own scroll position.
- **Persistence**: Scroll positions should be tracked in the global state to persist when a user return to a passage or question.

### 2. Global Navigation & Timing
- **Footer Palette**: A 1-40 question grid. Indicators include:
    - `Active`: Blue outline.
    - `Answered`: Solid underline.
    - `Review`: Circular button shape.
- **Countdown Clock**: A 60-minute timer with:
    - 10-minute warning (red flash).
    - 5-minute warning (persistent red pulse).
    - Time-hide functionality.

## 🎨 Interactive Tools

### Text Markup Engine
The `TextMarkupEngine` component wraps the passage to provide specialized interactions:
- **Right-Click Override**: Suppresses the native context menu to show Highlight and Notes tools.
- **DOM Range API**: Injects `<mark>` tags for highlights and manage sticky note placements.

## 📝 Specialized Question Types

### Heading Matcher
- **Deselection**: Users must be able to drag headings back to the bank or swap them.
- **Mutual Exclusion**: A heading can only be assigned to one paragraph at a time.

### True / False / Not Given
- **Custom Radios**: Standard HTML radios are avoided. Use custom state to allow "unselecting" an option by clicking it again.

### Gap Fill
- **Clipboard Integration**: Must allow pasting text selected from the left-hand passage pane.
- **Input Constraints**: Word counts are enforced via regex or simple split checks on the frontend.

## 🌐 Styling & Accessibility
Always use Tailwind CSS with the defined IELTS color palette:
- `Standard`: White bg, black text.
- `Yellow-on-Black`: High contrast for accessibility.
- `Blue-on-White`: Alternate accessible view.
- `Text Sizes`: Support Standard, Large, and Extra-Large shifts globally.
