---
name: minimax_vpn_workaround
description: Crucial rules for calling the Minimax API (api.minimaxi.chat) while the system TUN-mode proxy is active. Prevents silent hangs and connection drops.
---

# Minimax API Network Strategy (OppaVPN TUN mode)

## Overview
The host machine runs a VPN (OppaVPN) in TUN mode which intercepts all network traffic layer-by-layer.
When making API calls to `api.minimaxi.chat`:
1. The API often takes **40-60+ seconds** to respond to large LLM context requests.
2. The VPN proxy node proactively kills long-polling connections or connections that cause excessive concurrency, causing TCP timeouts (`code 28`).
3. Standard Python HTTP libraries (like `requests` and `openai`) fail to detect these drops smoothly, leading to the Python script **silently hanging forever**.

## Golden Rules for Minimax API calls

Whenever you write or modify a script that talks to Minimax on this machine, you MUST follow these three rules:

### 1. Hard Cap on Concurrency
Do not flood the VPN tunnel with parallel API requests.
- **Rule:** If using `concurrent.futures.ThreadPoolExecutor` or similar async batching, you MUST NOT exceed `max_workers=5`.
- A safer baseline for batch jobs is `workers=2` or `workers=3`.

### 2. Explicit and Aggressive Timeouts (No Defaults!)
Python's default HTTP handlers will hang indefinitely if the TUN proxy drops the connection without sending a TCP RST packet. You must explicitly configure timeouts that are longer than the Minimax processing time (e.g. 120s), but explicitly terminate the socket if the data stops.
- **Rule (requests):** `requests.post(url, timeout=(10, 120))` (10s connect, 120s read).
- **Rule (httpx):** `httpx.Client(timeout=httpx.Timeout(120.0, connect=10.0))`
- **Rule (openai client):** Set `timeout=120.0` when initializing the client if using it as a wrapper.

### 3. Consider OS-level `curl` for Batch Jobs
For multi-hour batch extraction jobs (like IELTS or TOEFL parsing), Python socket libraries still struggle with "blackhole" drops. Spinning up a raw OS-level `curl` subprocess is the most bulletproof way to guarantee the script never gets fatally stuck.
- **Rule:** Instead of heavy `requests` logic for core batch LLM processing, prefer:
  ```python
  subprocess.run(["curl", "-s", "-S", "-m", "120", "-X", "POST", ...])
  ```
  The `-m 120` argument provides a hard timeout that Python can cleanly recover from, logging the `code 28` error and retrying without blocking the main event loop.
