# Complete TOEFL iBT 2026 Test Flow

## Sources

| ID | Source | Type | URL |
|----|--------|------|-----|
| S1 | ETS Technical Manual RR-25-12 (Oct 2025) | Primary (official) | Internal: `specs/toefl_2026_technical_manual.md` |
| S2 | ETS — Test Content and Structure | Primary (official) | https://www.ets.org/toefl/test-takers/ibt/about/content.html |
| S3 | ETS — TOEFL iBT About | Primary (official) | https://www.ets.org/toefl/test-takers/ibt/about.html |
| S4 | toeflresources.com | Secondary (expert) | https://www.toeflresources.com |
| S5 | study.com TOEFL 2026 Guide | Secondary (expert) | https://study.com |
| S6 | testsucceed.com | Secondary (expert) | https://testsucceed.com |
| S7 | magoosh.com TOEFL Guide | Secondary (expert) | https://magoosh.com |
| S8 | manyagroup.com | Secondary (prep) | https://manyagroup.com |
| S9 | myspeakingscore.com | Secondary (speaking) | https://myspeakingscore.com |
| S10 | shiksha.com | Secondary (prep) | https://shiksha.com |
| S11 | simpliboards.com | Secondary (prep) | https://simpliboards.com |
| S12 | englishwitharik.id | Secondary (prep) | https://englishwitharik.id |

---

## Variance Log

> This log tracks data points where sources disagree. Each entry records what each source claims and our resolution.

### VAR-001: Section Order

| Source | Claim |
|--------|-------|
| S1 (ETS Tech Manual) | Table lists: 1.Reading, 2.Listening, 3.Writing, 4.Speaking |
| S2 (ETS Content Page) | Task list order: Reading → Listening → Writing → Speaking |
| S3 (ETS About Page) | Prose says: "Reading, Listening, Speaking and Writing" |
| S8 (manyagroup) | R → L → W → S |
| S5 (study.com) | R → L → S → W |
| S4 (toeflresources.com) | R → L → S → W |

**Resolution**: ⚠️ **R → L → W → S** — The ETS Technical Manual (S1, our highest-authority source) and the ETS content page (S2) both list Writing before Speaking. The "R-L-S-W" ordering in S3 prose likely refers to the traditional TOEFL convention, not the 2026 test delivery order. We follow S1.

---

### VAR-002: Build a Sentence — Item Count

| Source | Claim |
|--------|-------|
| S1 (ETS Tech Manual) | 10 items (Table: "Build a Sentence, 10, Raw 0–10") |
| S4 (toeflresources) | "9 sentences" |
| S5 (study.com) | "up to 12 items" |
| S6 (testsucceed) | "around 6–12" |
| S11 (simpliboards) | "10 items" |

**Resolution**: **10 items** — S1 (Tech Manual) is definitive. S5/S6 may include unscored tryout items in their count.

---

### VAR-003: Reading Section Time

| Source | Claim |
|--------|-------|
| S4 (toeflresources) | 18–27 min |
| S5 (study.com) | 18–27 min |
| S8 (manyagroup) | ~35 min |
| S7 (magoosh) | ~30 min |
| S2 (ETS Content Page) | "test time and items may vary" (no exact time given) |

**Resolution**: ⚠️ **~18–27 min** for scored items. ETS does not publish exact section times; they state time varies with adaptive path. The 30–35 min estimates likely include direction time and unscored items.

---

### VAR-004: Listening Section Question Count

| Source | Claim |
|--------|-------|
| S1 (ETS Tech Manual) | 35 scored (20 router + 15 stage 2) |
| S5 (study.com) | 35–45 questions |
| S4 (toeflresources) | 30–40 questions |

**Resolution**: **35 scored** — S1 definitive. Higher counts in S4/S5 include unscored tryout items (up to 12).

---

### VAR-005: Total Test Duration

| Source | Claim |
|--------|-------|
| S2 (ETS Content Page) | "approximately two hours" |
| S5 (study.com) | 67–85 min |
| S8 (manyagroup) | ~90 min |

**Resolution**: **~85–90 min active testing + directions ≈ ~2 hours total**. ETS says "allow approximately two hours." Active test time (excl. directions) is shorter.

---

### VAR-006: Speaking — Listen and Repeat Response Time

| Source | Claim |
|--------|-------|
| S5 (study.com) | 8–12 sec |
| S9 (myspeakingscore) | 8–12 sec |
| S4 (toeflresources) | 8–12 sec |

**Resolution**: **8–12 sec** — Consistent across all sources. ✅ No variance.

---

### VAR-007: Writing — Write an Email Time

| Source | Claim |
|--------|-------|
| S2 (ETS Content Page) | Not specified per task |
| S4 (toeflresources) | 7 min |
| S5 (study.com) | 7 min |
| S10 (shiksha) | 7 min |

**Resolution**: **7 min** — Consistent across all secondary sources. ✅

---

## Test Overview

| Property | Value | Source |
|----------|-------|--------|
| Launch Date | January 21, 2026 | S2, S3 |
| Total Scored Questions | 93 | S1 |
| Total Test Time | ~85–90 min excl. directions (~2h with directions) | S2, S5 (VAR-005) |
| Section Order | Reading → Listening → Writing → Speaking | S1, S2 (VAR-001) |
| Scoring | 1–6 band per section (0.5 increments) | S1, S2 |
| Overall Score | Average of 4 section bands, rounded to nearest 0.5 | S2 |
| Transition Period | 2026–2028: both 1–6 band AND legacy 0–120 total | S2 |
| Score Delivery | Within 72 hours | S5 |
| Break | None (removed from pre-2026) | S5, S8 |

## Section Flow

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 1. READING   │→ │ 2. LISTENING │→ │ 3. WRITING   │→ │ 4. SPEAKING  │
│ ~18–27 min   │  │ ~18–27 min   │  │ ~23 min      │  │ ~8 min       │
│ 35 scored    │  │ 35 scored    │  │ 12 items     │  │ 11 items     │
│ 2-stage MST  │  │ 2-stage MST  │  │ Linear       │  │ Linear       │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

### 1. Reading (MST — 2 stages) [S1]

**Stage 1: Router** (~10–12 min)
- 20 scored questions at moderate difficulty (B1–B2)
- Up to 15 additional unscored tryout questions
- Mix: C-Test (10) + Daily Life (5) + Academic (5)

**Routing** → ≥60% correct = Upper path; <60% = Lower path [S6, S12]

**Stage 2** (15 scored questions)

| Task Type | Stage 1 | Stage 2 Lower | Stage 2 Upper | Easy Path | Hard Path |
|-----------|---------|---------------|---------------|-----------|-----------|
| Complete the Words | 10 | 10 | 10 | 20 | 20 |
| Read in Daily Life | 5 | 5 | 0 | 10 | 5 |
| Read an Academic Passage | 5 | 0 | 5 | 5 | 10 |
| **Total** | **20** | **15** | **15** | **35** | **35** |

### 2. Listening (MST — 2 stages) [S1]

Same 2-stage architecture. Audio plays once — no replay. [S2, S4]

| Task Type | Stage 1 | Stage 2 Lower | Stage 2 Upper | Easy Path | Hard Path |
|-----------|---------|---------------|---------------|-----------|-----------|
| Listen and Choose a Response | 8 | 7 | 3 | 15 | 11 |
| Listen to a Conversation | 4 | 4 | 4 | 8 | 8 |
| Listen to an Announcement | 4 | 4 | 0 | 8 | 4 |
| Listen to an Academic Talk | 4 | 0 | 8 | 4 | 12 |
| **Total** | **20** | **15** | **15** | **35** | **35** |

Speaker accents: NA, UK, AU, NZ [S1]

### 3. Writing (Linear — ~23 min) [S1, S4, S5]

| # | Task Type | Items | Time | Scoring |
|---|-----------|-------|------|---------|
| 1 | Build a Sentence | 10 | ~6 min | 0/1 per item (VAR-002) |
| 2 | Write an Email | 1 | 7 min | 0–5 (AI + human) (VAR-007) |
| 3 | Academic Discussion | 1 | 10 min | 0–5 (AI + human) |
| | **Total** | **12** | **~23 min** | **Raw 0–20** |

### 4. Speaking (Linear — ~8 min) [S1, S4, S9]

| # | Task Type | Items | Prep | Response | Scoring |
|---|-----------|-------|------|----------|---------|
| 1 | Listen and Repeat | 7 | None | 8–12 sec | 0–5 (AI) (VAR-006) |
| 2 | Take an Interview | 4 | None | 45 sec | 0–5 (AI) |
| | **Total** | **11** | | | **Raw 0–55** |

## Post-Test Flow [S2, S5]

1. Responses collected and submitted
2. Machine scoring (R/L automated; W/S AI + human raters)
3. Score report within 72 hours
4. Report: 4 section scores (1–6), overall score, CEFR, MyBest® scores
5. During 2026–2028: legacy 0–120 comparable score included

## UI Flow (Test-Taker Experience)

```
Login → ID Verification → System Check →
  Reading Stage 1 → Reading Stage 2 →
  Listening Stage 1 → Listening Stage 2 →
  Writing: Build a Sentence (×10) → Write an Email (7 min) → Academic Discussion (10 min) →
  Speaking: Listen and Repeat (×7) → Take an Interview (×4) →
Test Complete → Unofficial Score Preview → Score Report (72h)
```

## Navigation Rules (ETS Spec)

The navigation paradigm varies strictly by section to preserve construct validity:

| Section | Back Navigation | Review Screen | Confirmation Dialog | Note |
|-------|----------------|---------------|-------------------|------|
| **Reading** | ✅ Allowed (within module) | ✅ Available | ❌ None | Test-takers can freely navigate, review, and change answers within the current module. Cannot return once advancing to the next module. |
| **Listening** | ❌ None (Forward-only) | ❌ None | ✅ "Cannot go back" | Because audio only plays once, answering is strictly forward-only. Clicking Next triggers a warning: "Once confirmed, you cannot go back." |
| **Writing** | ❌ None (Forward-only) | ❌ None | ❌ None | Standard forward progression. |
| **Speaking**| ❌ None (Forward-only) | ❌ None | ❌ None | Standard forward progression. |

## Audio Mechanics

- **Autoplay Restrictions**: Modern browsers block unmuted autoplay. Test interfaces must provide visible `<audio>` elements with `controls` (Play/Pause, Seek, Volume) so users can manually initiate playback.
- **Playback Policy**: In the Listening section, audio plays exactly once. There is no replay button or mechanism to restart the audio after completion.
- **Timing**: The section timer is paused during audio playback and only runs while the user is answering questions.

## Key Differences from Pre-2026

| Aspect | Pre-2026 | 2026+ | Source |
|--------|----------|-------|--------|
| Duration | ~116 min | ~85–90 min | S5 |
| Break | 10-min after Listening | None | S5 |
| Section order | R → L → S → W | R → L → W → S | S1 (VAR-001) |
| Scoring | 0–120 total | 1–6 band (CEFR) | S1, S2 |
| Reading/Listening | Linear | MST adaptive | S1 |
| Speaking tasks | 4 (ind + integrated) | 2 (Repeat + Interview) | S1 |
| Writing tasks | 2 (integrated + ind) | 3 (Sentence + Email + Discussion) | S1 |
| Reading passages | Long (~700 words) | Short (~200 words) | S4, S5 |
| Accents | Primarily NA | NA + UK + AU + NZ | S1 |
