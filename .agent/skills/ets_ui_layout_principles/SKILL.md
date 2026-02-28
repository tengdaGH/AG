---
name: ets_ui_layout_principles
description: Industry-standard UI layout and responsiveness principles for high-stakes Computer-Based Testing (CBT), specifically ETS TOEFL and IELTS platforms. Contains rules on window locking, pane decoupling, fold prioritization, and responsive behaviors.
tags:
  - ets
  - toefl
  - ielts
  - ui
  - layout
  - responsiveness
  - flexbox
---

# ETS/CBT High-Stakes Exam UI Layout Principles

When developing standardized computer-based testing interfaces (e.g., TOEFL, IELTS, GRE), the overriding principles are **"Fairness"** and **"Visual Isolation"**. You must prioritize these over standard consumer web development patterns (like fluid pages or document-level scrolling).

## 1. Window Lock (Global Lock & No Body Scroll)
- **Rule**: Never allow the `<body`> or root container to scroll.
- **Why**: Regardless of physical screen size, the persistent system UI elements (Header with timer/question numbers and Footer with Previous/Next navigation controls) must remain permanently visible at the literal edges of the screen.
- **Implementation**:
  - The main application wrapper must be restricted using `100vh` and `overflow: hidden`.
  - Headers and Footers must be absolute or flex-shrunk to remain sticky.
  - Doing this ensures candidates never "lose" the submit or next buttons when encountering extra-long reading passages.

## 2. Decoupled Pane Scrolling (Internal Scroll Delegation)
- **Rule**: In multi-pane views (like Reading sections), the Stimulus (reading passage) pane and the Questions pane must scroll entirely independently.
- **Implementation**:
  - Assign `overflowY: auto` exclusively to the independent content layers.
  - Crucially: Flexbox layers wrapping these scrollable inner panes MUST be restricted with `minHeight: 0` (or `position: relative` with an absolute child) to prevent "Flex-scroll Bleed". 
  - Without this, deep nested children with `height: 100%` will force the parent flex container to grow boundless, pushing the footer off the bottom of small screens.
  - **Golden snippet**:
    ```tsx
    <main style={{ flex: 1, position: 'relative', minHeight: 0 }}>
        {/* The Absolute Inset Layer enforces strict bounds */}
        <div style={{ position: 'absolute', inset: 0, overflowY: 'auto' }}>
            {/* Scrollable content goes here */}
        </div>
    </main>
    ```

## 3. Above the Fold Prioritization (Safety-First Rendering)
- **Rule**: System controls must never compete for space with dynamic test content.
- **Why**: Time is critical in high-stakes testing. Candidates on 13-inch (or 1366x768 resolution) screens must have the exact same one-click access to the "Next" button as candidates on 27-inch 4K monitors. If a multiple-choice question has exceptionally long localized text, the question must spawn its own internal scrollbar within the `absolute inset` boundary—the footer must never be pushed physically downward.

## 4. Responsive + Restrictive Layouts
- **Rule**: Wide-screen layout and narrow-screen layout should provide visually equitable experiences. 
- **Implementation**:
  - Set an absolute maximum content width (e.g., `max-width: 1200px`) and center it (`margin: 0 auto`), rather than letting text lines extend infinitely sideways on ultrawide monitors.
  - Do NOT give wide-screen candidates the unfair advantage of seeing more text content without scrolling (comparable to lower-res screens) merely because they have a larger monitor. 
  - The interface layout must scale proportionately or lock into a centered island, rather than aggressively fluidly adapting in ways that alter cognitive load.

## 5. UI Sanity Checklist for Exam View Components
Before finalizing any new test-taking layout view, verify:
- [ ] No scrollbar appears on the main browser window frame.
- [ ] Changing browser height vigorously does not hide the Top Bar or Footer row.
- [ ] Extremely long passages trigger an internal scrollbar on the LEFT pane only.
- [ ] Extremely long question options trigger an internal scrollbar on the RIGHT pane only.
- [ ] (Testing hack) Inject a 5000px div into the content area; the footer MUST stay on screen.
