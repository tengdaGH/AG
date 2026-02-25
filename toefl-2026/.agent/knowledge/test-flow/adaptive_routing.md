# MST Adaptive Routing — Reading & Listening

> Source: ETS Technical Manual RR-25-12, englishwitharik.id, testsucceed.com

## What is MST?

**Multistage Adaptive Testing (MST)** adapts difficulty at the *module level* (not per-question like CAT). Once a path is chosen after Stage 1, it stays for the entire Stage 2.

## Two-Stage Architecture

```
                    ┌──────────────┐
                    │   Stage 1    │
                    │   (Router)   │
                    │  B1–B2 level │
                    │  20 scored   │
                    └──────┬───────┘
                           │
               ┌───────────┴───────────┐
               │                       │
        Score ≥ 60%              Score < 60%
               │                       │
      ┌────────▼────────┐    ┌─────────▼─────────┐
      │    Stage 2       │    │    Stage 2          │
      │  Upper (Hard)    │    │  Lower (Easy)       │
      │  15 scored       │    │  15 scored           │
      │  More academic   │    │  More daily life     │
      └─────────────────┘    └──────────────────────┘
```

## Key Properties

| Property | Value |
|----------|-------|
| Adaptation level | Module (not per-question) |
| Stage 1 difficulty | Moderate (CEFR B1–B2) |
| Routing threshold | ~60% correct |
| Total scored per path | 35 (20 + 15) |
| Unscored tryouts | Reading: up to 15 • Listening: up to 12 |
| Scoring method | IRT true score equating across paths |

## Scoring Implication

Two students with the **same raw score** may receive **different scaled scores** depending on their path. The hard path has higher scoring potential — answering correctly in the upper module carries more weight in the IRT model.

## Implementation Notes

For our practice platform:
- **Stage 1**: Pull 20 items from the DB at moderate difficulty
- **Routing logic**: Count correct answers, route at 60% threshold
- **Stage 2**: Pull 15 items from the appropriate difficulty pool
- Items should be tagged with `difficulty_level` (easy/moderate/hard) in the DB
- Current DB does NOT have difficulty tagging — this is a gap to address
