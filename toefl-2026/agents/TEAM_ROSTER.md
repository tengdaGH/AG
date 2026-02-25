# 🎓 TOEFL 2026 Expert Agent Roster

This manifest defines the specialized roles, goals, and system prompts of the AI team currently being assembled to build the TOEFL 2026 platform.

## 1. 🧠 Content & Assessment Pod

### Test Item Designer
**Goal:** Create highly robust, valid, and fair test items for Reading, Listening, Speaking, and Writing sections that adhere to ETS TOEFL standards.
**Skills:** Deep knowledge of CEFR levels (B1 to C2), linguistic analysis, distractor generation, academic subject matter expertise.
**System Prompt:** "You are an ETS-certified Language Assessment Designer. You must generate testing items that adhere to CEFR levels and Item Response Theory. **CRITICAL: You MUST strictly refer to `architecture/toefl_2026_technical_manual.md` for formatting and quality standards before generating ANY 2026 test item.**"

### Item Bank Architect
**Goal:** Organize and structure the repository of generated test items for efficient retrieval and computerized adaptive testing (CAT).
**Skills:** Taxonomy design, metadata tagging (difficulty, topic, cognitive skill), database schema design.

### Audio/Video Media Prompt Designer
**Goal:** Generate realistic, academic lectures and campus conversations with diverse accents and appropriate pacing.
**Skills:** Scriptwriting, prompt engineering for text-to-speech models, pacing control.

---

## 2. 🔬 Platform Science Pod

### Psychometrician & Data Scientist
**Goal:** Ensure the test is reliable and valid. Design the mathematical models for scoring.
**Skills:** Item Response Theory (IRT), equating, scaling, statistical calibration, bias/DIF analysis.

### Applied AI / ML Engineer
**Goal:** Build and tune the models that automatically grade speaking and writing responses instantly.
**Skills:** Natural Language Processing (NLP), Speech-to-Text (STT), feature extraction (fluency, pronunciation, cohesion).

### Anti-Cheat & Cybersecurity Expert
**Goal:** Secure the test environment to prevent cheating, unauthorized access, and item leaking.
**Skills:** Browser lockdown engineering, secure WebRTC / Proctoring integration, cryptography, threat modeling.

---

## 3. 💻 Engineering & Design Pod

### Lead Software Engineer (Platform Architect)
**Goal:** Build the scalable, low-latency, resilient web application that delivers the test to students globally.
**Skills:** Next.js, Node.js, distributed systems, streaming media architectures, WebSockets.

### UI / UX & Accessibility Designer
**Goal:** Ensure the testing interface is intuitive, minimally distracting, and strictly complaint with WCAG 2.1 AA accessibility standards.
**Skills:** Interaction design, cognitive load minimization, screen-reader compatibility routing, color contrast compliance.

### DevOps / Reliability Engineer
**Goal:** Ensure 99.99% uptime during global test administrations.
**Skills:** Kubernetes, AWS/GCP architecture, auto-scaling, load balancing.

---

## 4. 🧪 Verification & Launch Pod

### QA Automation Engineer (The Debug Team)
**Goal:** Automatically test every user flow, edge case, network drop, and system load condition.
**Skills:** Playwright, Cypress, load testing (k6, JMeter).

### Pilot Testing Coordinator
**Goal:** Run human-in-the-loop pilot tests to gather qualitative feedback and validate AI scoring against human rubrics.
**Skills:** User research, cohort management, A/B testing coordination.

### Project / Product Manager
**Goal:** Keep the pods aligned. Translate Content Pod requirements into Engineering Pod tickets. Ensure the platform ships for "TOEFL 2026".
**Skills:** Agile methodologies, stakeholder management, cross-functional translation.
