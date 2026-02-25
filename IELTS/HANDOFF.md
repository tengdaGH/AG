# IELTS Ingestion Pipeline: Agent Handoff Document

## 1. Project Context
We are currently executing **Phase 2** of the IELTS Reading batch processing pipeline. The goal is to ingest 651 raw PDF-extracted JSON files from `extracted/`, use the Minimax API to structure the reading passages and questions, merge them with the `answer_key.json`, and output pristine structured payloads into `parsed_v2/`.

## 2. The Core Blocker & Discovery
Previously, the `structure_v2.py` batch script was failing to complete because Python threads would silently hang on network requests to `api.minimaxi.chat` with 0% CPU usage. 
- **The Cause:** A deep macOS networking issue involving a local proxy (like Surge/Clash) intercepting Python socket requests to a fake-IP tunnel and dropping them into a black hole without returning TCP `FIN` or `RST` packets. Standard timeouts (`requests.post(timeout=60)`, `httpx.Timeout(60.0)`, and the OpenAI Client timeouts) were completely ignored because the stall happened *before* the HTTP timer could start (during DNS/TLS handshake).

## 3. The Current Solution
We abandoned Python's native HTTP libraries (`requests`, `httpx`, `openai`) for the core Minimax API call. 
- **The Fix:** We rewrote `call_minimax_structured` in `scripts/structure_v2.py` to use a raw OS-level `subprocess.run(["curl", "-m", "60", ...])`. 
- **Why it works:** `libcurl` gracefully handles the macOS network extensions, and the OS-level `-m 60` flag creates a hard mathematical execution wall that guarantees the thread will never hang infinitely, allowing our retry logic to catch `Exit Code 28` (Timeout) and loop gracefully.

## 4. Current State
- `structure_v2.py` has been modified to use the `curl` subprocess.
- To isolate the network bugs, the `ThreadPoolExecutor` inside `structure_v2.py` (around Line 286) is currently **commented out**, and the script is executing a slow, sequential `for` loop.
- A test run of `ielts-r-0001.json` successfully processed through both Stage 1 and Stage 2 without hanging.

## 5. Next Steps for the Incoming Agent
1. **Re-enable Concurrency**: Go into `/scripts/structure_v2.py`, remove the sequential `for` loop at the bottom, and restore the `ThreadPoolExecutor`. Set `max_workers=5` (to be safe with Minimax ratelimits, though you can experiment with up to `10`).
2. **Execute the Batch Job**: Run `python scripts/structure_v2.py` to chew through the remaining ~650 files in `extracted/`. 
3. **Monitor Progress**: You can run `python scripts/monitor_progress.py` in a separate terminal to watch the exact success/failure ratios in real time.
4. **Phase 3 Validation**: Once the `parsed_v2/` directory is fully populated, execute `python scripts/validate_and_verify.py`. We recently updated the validation definitions in `implementation_plan.md` to be extremely strict (e.g., exact question bounds, paragraph length maps). Ensure all files pass this QA gating check.
