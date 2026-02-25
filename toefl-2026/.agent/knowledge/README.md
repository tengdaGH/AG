# TOEFL 2026 — Global Knowledge Bank

This directory serves as the **single source of truth** for all project intelligence. Every conversation, agent script, and UI component should reference this bank instead of relying on ad-hoc context.

## Directory Structure

```
knowledge/
├── README.md                     ← You are here
├── test-flow/
│   ├── complete_test_flow.md     ← Official ETS test flow (section order, timing, routing)
│   ├── adaptive_routing.md       ← MST 2-stage design for Reading & Listening
│   ├── scoring.md                ← Band scores, CEFR mapping, IRT equating
│   ├── toefl-2026-interface-research.md ← Deep research on the 2026 TOEFL testing shell
│   └── ielts-cd-interface-research.md   ← Deep research on the CD-IELTS computer interface
├── task-types/
│   ├── reading.md                ← All 3 Reading task types
│   ├── listening.md              ← All 4 Listening task types
│   ├── speaking.md               ← All 2 Speaking task types
│   └── writing.md                ← All 3 Writing task types
├── implementation/
│   ├── coverage_matrix.md        ← What we've built vs what's needed
│   ├── frontend_routes.md        ← All frontend routes and their status
│   └── backend_api.md            ← All backend endpoints and their status
├── item-quality/
│   └── mcq_item_quality.md       ← Bulletproof MCQ standards (stems, keys, distractors, parity)
└── history/
    └── work_log.md               ← Chronological log of major milestones
```

## Usage

- **Before building a feature**: Read `test-flow/complete_test_flow.md` and the relevant `task-types/*.md`
- **Before writing items**: Reference `specs/task_types/` (12 individual spec files) and `specs/rubrics/`
- **Before modifying UI**: Check `implementation/coverage_matrix.md` and `implementation/frontend_routes.md`
- **After completing work**: Update `history/work_log.md`

## Related Directories

- `specs/` — ETS specification documents (spec sheet, technical manual, task types, rubrics)
- `agents/scripts/` — Generation and population scripts
- `.agent/rules/` — Agent behavioral rules
