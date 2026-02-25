# Frontend Routes Map

> Last updated: 2026-02-25

## Public Pages

| Route | Purpose | Status |
|-------|---------|--------|
| `/` | Student landing page | ✅ Live |
| `/login` | Role-based login (Student/Admin/Proctor) | ✅ Live |

## Dashboard Pages

| Route | Purpose | Status |
|-------|---------|--------|
| `/dashboard/student` | Student assessment hub | ✅ Live |
| `/dashboard/admin/items` | Admin item bank browser | ✅ Live |
| `/dashboard/proctor` | Proctor dashboard | ✅ Live |

## Demo Test Session Pages

| Route | Task Type | Section | Fetches DB? |
|-------|-----------|---------|-------------|
| `/test-session/demo` | Complete the Words (Reading) | Reading | ✅ Yes |
| `/test-session/demo/reading` | Reading hub | Reading | Needs check |
| `/test-session/demo/reading-academic-passage` | Read Academic Passage | Reading | Needs check |
| `/test-session/demo/reading-daily-life` | Read in Daily Life | Reading | Needs check |
| `/test-session/demo/listening` | Listening hub | Listening | Needs check |
| `/test-session/demo/listen-choose-response` | Listen & Choose | Listening | Needs check |
| `/test-session/demo/listen-conversation` | Listen to Conversation | Listening | Needs check |
| `/test-session/demo/listen-announcement` | Listen to Announcement | Listening | Needs check |
| `/test-session/demo/listen-academic-talk` | Listen to Academic Talk | Listening | Needs check |
| `/test-session/demo/speaking` | Speaking hub | Speaking | Needs check |
| `/test-session/demo/listen-repeat` | Listen and Repeat | Speaking | Needs check |
| `/test-session/demo/interview` | Take an Interview | Speaking | Needs check |
| `/test-session/demo/writing` | Write an Email | Writing | ❌ Hardcoded |
| `/test-session/demo/build-sentence` | Build a Sentence | Writing | Needs check |
| `/test-session/demo/academic-discussion` | Academic Discussion | Writing | Needs check |

## Full Test Session

| Route | Purpose | Status |
|-------|---------|--------|
| `/test-session/full` | TestSequencer (full test) | ⚠️ Uses mock data |

## Key Components

| Component | File | Purpose |
|-----------|------|---------|
| `TestSequencer` | `components/TestSequencer.tsx` | Orchestrates full test flow |
| `TestShell` | `components/TestShell.tsx` | Lockdown environment wrapper |
| `TestTimer` | `components/TestTimer.tsx` | Countdown timer |
| `WriteEmail` | `components/WriteEmail.tsx` | Email editor with ETS clipboard |
| `ScoreReportDashboard` | `components/ScoreReportDashboard.tsx` | Score report display |
