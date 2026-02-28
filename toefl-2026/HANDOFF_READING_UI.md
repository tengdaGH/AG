# TOEFL 2026 - Reading UI Handoff & Debug Report

## **Next Agent: You are taking over the frontend UI refinement and mechanics for the TOEFL 2026 Master Test Sequencer.**

### 🎯 Recent Accomplishments (What works beautifully now!)
The reading section UI has undergone significant improvements to authentically mimic the real ETS delivery mechanics. The `TestSequencer.tsx`, `ReadInDailyLife.tsx`, and `ReadAcademicPassage.tsx` components have been deeply refactored to achieve the following:

1. **Clean Question Stems (Numeric Strip):**
   - **The Issue:** Imported item bank json payloads often have hardcoded numbers (e.g., `"16. Which of the following..."`) inside `question_text`, which caused duplicate numbering during sequential delivery.
   - **The Fix:** We implemented a regex interceptor `.replace(/^\d+\.\s*/, '')` inside the `renderMCQs` loops. No database modifications are needed! The frontend engine automatically sanitizes question text. Question stems are now clean and rely purely on the global utility bar `Q 22/46` for progress indication.

2. **Daily Life Dynamic Content Rendering:**
   - **The Issue:** For the `READ_IN_DAILY_LIFE` component, text messages, emails, menus, and social media posts were just being dumped as generic paragraphs.
   - **The Fix:** The component now maps the full `contentObj` from the backend. 
     - **Text Messages:** Extracted out to look like actual alternating iMessage/WhatsApp bubbles (green on the right for the user, grey on the left for the other party).
     - **Emails:** Rendered with true grids resembling `From`, `To`, `Date`, and `Subject` headers.
     - **Social Media:** Generates colored circular avatar icons with initials, bold author names, and timestamps.
     - Notice texts and menus now cleanly sit in a crisp, bordered card with subtle shadow dropping.

3. **Active Vocabulary Highlighting (`ReadAcademicPassage`):**
   - **The Issue:** "Closest in meaning" vocabulary questions require the target word to be conspicuously tethered to the main reading paragraph.
   - **The Fix:** An intercept layer was added to `TestSequencer.tsx` that intelligently listens to the active question string for the regex pattern `/word\s+["“”'‘]([^"“”'‘]+)["“”'‘]\s+in the passage/i`. 
   - It plucks the vocabulary word and passes it as a `targetWord` prop down to the `ReadAcademicPassage` component.
   - The passage renderer automatically splits the raw text nodes and wraps any exact match of the target word in a bold, grey highlighted span (`backgroundColor: '#E2E8F0'`) just like the official ETS testing client.
   - *Note:* We added a sanitization layer here too to scrub rogue `(begin highlight)` and `(end highlight)` string tags that were occasionally baked into the raw payload data.

### 🐛 Known Issues & Debug Log (What you should look at next)
1. **Lint Errors in tmp scripts:** 
   - Some leftover scripts in `/tmp/check_audio.py` are throwing module not found errors (`dotenv`, `google`, `google.genai`). These are scratch scripts, not production breaking, but worth acknowledging if evaluating backend audio logic.
2. **Audio/Media Delivery Engine Validation:**
   - While the reading mechanics (Cloze paragraphs, full-width headers, daily life dynamic rendering, highlighting) are solid, the next big hurdle will be fully confirming the `LISTEN_*` components (like `ListenChooseResponse`, `ListenConversation`) have their audio streams tethered correctly. Check `TestSequencer.tsx` and ensure audio urls are valid.
3. **State Persistence on Reload:**
   - Current selected responses are preserved reasonably well in React state, but testing whether switching between questions retains checkboxes gracefully during the delivery sequence.

### 🚀 Immediate Next Steps
1. Review the UI rendering of the Listening components. Are audio files playing? Do the UI widgets correctly disable advancing before an audio finishes playing (if ETS specs demand it)?
2. Do a spot check on `COMPLETE_THE_WORDS` (Cloze tasks) to make sure layout gaps are still behaving nicely with the full-screen layout design.
3. Advance with the scoring engine integration! Tie these highly-polished frontend inputs directly back to the database backend via the API submission routes.

Happy coding!
