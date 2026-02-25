# MCQ Batch Audit Work Log

## 2026-02-25 — Deep Interface Research (TOEFL 2026 & CD-IELTS)
- Conducted extensive structured research on the real test platform interfaces for both TOEFL iBT 2026 and Computer-Delivered IELTS.
- Created `toefl-2026-interface-research.md` documenting the paradigm shift to MST, new communicative task types, shortened duration, and CEFR bands.
- Created `ielts-cd-interface-research.md` documenting the split-screen layout, universal bottom navigation grid, independent pan scrolling, and accessibility options.
- Saved both documents to `.agent/knowledge/test-flow/` and updated the `README.md` index.
## 2026-02-25 — Full Batch Audit & Remediation

### Summary
| Metric | Before | After | Δ |
|--------|--------|-------|---|
| Total Items | 369 | 369 | — |
| Clean Items | 242 | 302 | +60 |
| Items with Issues | 127 | 67 | −60 |
| MCQ Quality Flags | 136 | 21 | −115 |
| Items Patched | — | 84 | — |
| Fixes Applied | — | 108 | — |

### Fixes Applied
- **KEY_TRIM** (97 fixes): Over-long correct answers trimmed to ≤1.4× mean distractor word count
- **KEY_ABS_FIX** (11 fixes): Absolute words in keys replaced with softer alternatives (always→typically, never→rarely, etc.)

### Items by Section
- READ_ACADEMIC_PASSAGE: 14 items patched
- READ_IN_DAILY_LIFE: 21 items patched
- LISTEN_ANNOUNCEMENT: 7 items patched
- LISTEN_ACADEMIC_TALK: 4 items patched
- LISTEN_CHOOSE_RESPONSE: 38 items patched

### Remaining Issues (67)
- Majority are **PASSAGE_SHORT** flags on `COMPLETE_THE_WORDS` items — these are short fill-in-the-blank passages by design (35–50 words), not MCQ quality issues
- 21 remaining MCQ quality flags: residual PARITY issues where key trimming alone was insufficient (would require distractor expansion or deeper rewriting)

### Items Not Auto-Remediated
- Items with PARITY_FAIL where the key was already at minimum viable length after trimming — these require manual content rewriting to expand distractors
- Backend was offline, so the LLM-based QA pipeline endpoint could not be used for deeper semantic fixes
