---
name: design_research
description: How to conduct comprehensive design language and UI/UX research, extract visual identity DNA, and document it in the themes-and-designs library.
---

# Design Research Skill

This skill outlines the process for researching a target company's website design language, theme, and visual style. The goal is to extract their fundamental design principles and UI/UX DNA, and document it into a reusable design reference library.

## Goal Structure
When instructed to research a brand's design language, follow this comprehensive workflow.

---

### Step 1: Visual Reconnaissance

Use the `browser_subagent` tool to visit the target brand's key digital properties (Homepage, Product Pages, Documentation, News/Company pages) and take multiple screenshots as you scroll.

**Capture specific details:**
1.  **Color Palette:** Background colors, text colors, accent/brand colors, footer backgrounds.
2.  **Typography:** Headline fonts (Serif vs Sans-serif), body text, navigation fonts, font sizes, and weights.
3.  **Layout Patterns:** Spacing (whitespace/padding), grid systems, card styling (borders vs borderless), section divisions.
4.  **Visual Elements:** Illustration styles (e.g. line art, 3D), iconography, photography style (e.g. conceptual, lifestyle, product).
5.  **Interactive Design:** Button styles (fill, outline), hover states, micro-animations, transitions.
6.  **Navigation:** Header/menu design, footer organization.

---

### Step 2: Information Gathering

Use the `search_web` and `read_url_content` tools to find specific technical details:
*   Search for things like: `[Brand] website design system brand identity typography color palette visual style`
*   Identify the exact font families used (e.g. Poppins, Lora, Inter).
*   Find exact hex color codes from design blogs, agency case studies, or developer CSS.
*   Read the company's "About" or "Mission" pages to extract their core values. This helps understand the *why* behind their design choices (e.g., safety, playfulness, speed).

---

### Step 3: Analysis & Synthesis

Synthesize your findings into a coherent "Design DNA." Group your observations into:
*   **Brand Identity:** The core philosophy (e.g. "Intellectual Minimalism" or "Playful Utility").
*   **Color Palette:** Primary, Secondary, Backgrounds, Accents. Extract Hex codes.
*   **Typography:** The font pairing system, hierarchy, and usage roles.
*   **Layout & Spatial Design:** Grids, spacing patterns, key UX patterns (pills, sticky cards).
*   **Visual Elements:** Rules for photography, illustration, and icons.
*   **Interaction Design:** Button styles, transition behaviors (calm vs energetic).
*   **Core Principles:** The fundamental design axioms driving their UI.

---

### Step 4: Documentation (The Themes & Designs Library)

All design research must be stored in the `/Users/tengda/Antigravity/themes-and-designs/` library for future reference.

1.  **Create the Subfolder Structure:**
    Create a new directory for the brand: `/Users/tengda/Antigravity/themes-and-designs/[brand]-design-dna/`
    Create an `assets/` subdirectory inside it.

2.  **Save Visual Assets:**
    Use `run_command` (e.g., `cp`) to copy the relevant screenshots and `browser_subagent` recording files (.webp) from the `.gemini/antigravity/brain/` artifact directory into the new `assets/` folder.

3.  **Create the README.md:**
    Write a comprehensive `README.md` inside the brand's folder containing the synthesized analysis. **Must include:**
    *   A "Quick Reference" summary.
    *   Markdown tables for the Color Palette (with hex color previews) and CSS variable snippets.
    *   Typography details (with CSS `@import` snippets).
    *   Layout & Visual Element descriptions.
    *   Button & Interactive Design rules.
    *   A list of Core Design Principles linked to company values.
    *   A `mermaid` mindmap summarizing the Design DNA.
    *   A Visual Reference gallery embedding the saved screenshots from the `assets/` folder using relative paths.

4.  **Update the Index:**
    Edit `/Users/tengda/Antigravity/themes-and-designs/README.md` to add a new index link pointing to your newly created design study folder, marking its status as "Complete".
