# Coverage Matrix — What's Built vs What's Needed

> Last updated: 2026-02-25

## Item Bank Coverage

| Section | Task Type | DB Key | Items in Bank | Official Count per Test | Status |
|---------|-----------|--------|---------------|------------------------|--------|
| Reading | Complete the Words | `COMPLETE_THE_WORDS` | 99 | 20 | ✅ Sufficient |
| Reading | Read in Daily Life | `READ_IN_DAILY_LIFE` | 44 | 5–10 | ✅ Sufficient |
| Reading | Read Academic Passage | `READ_ACADEMIC_PASSAGE` | 23 | 5–10 | ✅ Sufficient |
| Listening | Listen & Choose Response | `LISTEN_CHOOSE_RESPONSE` | 150 | 11–15 | ✅ Sufficient |
| Listening | Listen to Conversation | `LISTEN_CONVERSATION` | 20 | 8 | ✅ Sufficient |
| Listening | Listen to Announcement | `LISTEN_ANNOUNCEMENT` | 21 | 4–8 | ✅ Sufficient |
| Listening | Listen to Academic Talk | `LISTEN_ACADEMIC_TALK` | 12 | 4–12 | ✅ Sufficient |
| Speaking | Listen and Repeat | `LISTEN_AND_REPEAT` | 98 | 7 | ✅ Sufficient |
| Speaking | Take an Interview | `TAKE_AN_INTERVIEW` | 53 | 4 | ✅ Sufficient |
| Writing | Build a Sentence | `BUILD_A_SENTENCE` | 120 | 10 | ✅ Sufficient |
| Writing | Write an Email | `WRITE_AN_EMAIL` | 35 | 1 | ✅ Sufficient |
| Writing | Academic Discussion | `WRITE_ACADEMIC_DISCUSSION` | 86 | 1 | ✅ Sufficient |
| **Total** | | | **761** | **93** | |

## UI Component Coverage

| Task Type | Individual Demo Page | Component Built | Fetches from DB | In Full Test Flow |
|-----------|---------------------|-----------------|-----------------|-------------------|
| Complete the Words | ✅ `/demo` | ✅ CTest | ✅ | ❌ Hardcoded |
| Read in Daily Life | ✅ `/demo/reading-daily-life` | ✅ DailyLifeReader | Needs verify | ❌ |
| Read Academic Passage | ✅ `/demo/reading-academic-passage` | ✅ AcademicPassage | Needs verify | ❌ |
| Listen & Choose | ✅ `/demo/listen-choose-response` | ✅ | Needs verify | ❌ |
| Listen to Conversation | ✅ `/demo/listen-conversation` | ✅ | Needs verify | ❌ |
| Listen to Announcement | ✅ `/demo/listen-announcement` | ✅ | Needs verify | ❌ |
| Listen to Academic Talk | ✅ `/demo/listen-academic-talk` | ✅ | Needs verify | ❌ |
| Listen and Repeat | ✅ `/demo/listen-repeat` | ✅ ListenRepeat | Needs verify | ❌ |
| Take an Interview | ✅ `/demo/interview` | ✅ VirtualInterview | Needs verify | ❌ |
| Build a Sentence | ✅ `/demo/build-sentence` | ✅ BuildSentence | Needs verify | ❌ |
| Write an Email | ✅ `/demo/writing` | ✅ WriteEmail | ❌ Hardcoded | ❌ Hardcoded |
| Academic Discussion | ✅ `/demo/academic-discussion` | ✅ AcademicDiscussion | Needs verify | ❌ |

## Critical Gaps

### 🔴 No End-to-End Test Sequencer Pulling from DB
The `TestSequencer` component uses mock data for all sections. It does NOT:
- Fetch items from the DB for any section except Reading (C-Test only in `/demo`)
- Implement MST adaptive routing (2-stage with router → easy/hard)
- Present all 12 task types in the correct official order
- Track time per section correctly

### 🟡 Missing DB Fields
- No `difficulty_level` field on items (needed for MST routing)
- No `cefr_level` tagging
- No `stage` assignment (router vs stage-2-easy vs stage-2-hard)

### 🟡 Audio Status
- Many listening items tagged `PENDING_TTS` — audio not yet generated
- Listen and Repeat items have audio generated but need verification

### 🟢 Landing Page
- New student landing page built and live at `/`
- Shows live item counts from audit API
- CTAs link to demo and full test routes
