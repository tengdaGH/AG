# Agent Routing Protocol: Subscription vs. API

## 1. Core Reasoning & Writing (NATIVE SUBSCRIPTION)
- **Scope**: All text-based reasoning, code analysis, logic, planning, and co-writing.
- **Protocol**: You MUST use the native models associated with my Google AI Ultra subscription (e.g., Gemini 3.1 Pro High, Claude 4.6 Thinking). 
- **Constraint**: Do NOT consume API tokens for these reasoning tasks. Rely on the model quotas displayed in the 'Models' settings.

## 2. Image & Voice Generation (API KEY)
- **Scope**: All requests involving generating images (Nano Banana Pro) or synthesizing voice/audio (Lyria).
- **Protocol**: For these tasks ONLY, use the external Google Cloud API key (`GEMINI_API_KEY`). 
- **Failover Logic**: If the native image tool returns a 503 capacity error, immediately switch to using the API script/endpoint.
- **Specific Tooling**: Use the 'AG Audio Gen' project context for all audio generation to ensure costs are applied to the $100 monthly Cloud credit.

## 3. Feedback Loop
- If you are unsure which provider to use, default reasoning to the subscription and media to the API.
- Do not ask for the API key again; it is stored in the environment.
