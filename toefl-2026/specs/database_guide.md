# TOEFL 2026 — Database Architecture Guide

> **Last updated:** 2026-02-28  
> **Status:** CANONICAL REFERENCE — read this before touching any database.

---

## ⚠️ Critical Rule

There are exactly **two** operational databases in this project. Every agent, script, and human developer must know which is which at all times. Confusing them can corrupt student records or corrupt the item bank.

---

## The Two Databases

### 1. `item_bank.db` — The Question & Item Bank
**Location:** `backend/item_bank.db`  
**In Docker:** `/app/item_bank.db` (baked into the image at build time)  
**Env var:** `DATABASE_URL`

| Property | Value |
|----------|-------|
| **Purpose** | Stores all test items (questions, passages, audio URLs, IRT parameters) |
| **Who writes to it** | Agents (item generation), admin dashboard, QA pipeline |
| **Who reads it** | Backend API (`GET /api/items`), test sequencer, score calculator |
| **Deployment** | Baked into Docker image — rebuild required to update on cloud |
| **Item count** | ~1,041 active items across all task types |
| **Key table** | `test_items` |
| **Schema managed by** | `backend/app/scripts/enforce_schema.py` |

**This is the gold item bank.** It is the most critical asset in the project. Never truncate or drop tables here without a backup.

---

### 2. `user_data.db` — Student Sessions & Responses
**Location:** `backend/user_data.db`  
**In Docker:** `/app/data/user_data.db` (on a persistent Docker volume — NOT in the image)  
**Env var:** `USER_DATABASE_URL`

| Property | Value |
|----------|-------|
| **Purpose** | Stores student test sessions, item responses, scores, event logs |
| **Who writes to it** | Backend API (session creation, answer submission) |
| **Who reads it** | Score report, teacher dashboard, admin analytics |
| **Deployment** | On a persistent Docker volume (`toefl_db_data`) — survives container restarts |
| **Contains** | Real student exam data — handle with care (privacy) |
| **Key tables** | `sessions`, `responses`, `event_logs` |

**This is the student data vault.** Never run bulk deletes or test scripts against it. Never include it in item bank audits.

---

## How They Connect in Code

```python
# backend/app/database/connection.py

# Item bank — read-mostly, baked into Docker
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../item_bank.db"))
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")

# Student sessions — write-heavy, on persistent volume
user_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../user_data.db"))
SQLALCHEMY_USER_DATABASE_URL = os.getenv("USER_DATABASE_URL", f"sqlite:///{user_db_path}")
```

---

## Deployment Architecture

```
LOCAL DEVELOPMENT                    TENCENT CLOUD (101.32.187.39)
─────────────────────────────────    ──────────────────────────────────────
backend/item_bank.db (14 MB)         Docker image: /app/item_bank.db
  ↑ git tracked + pushed              ↑ rebuilt with: docker-compose up --build

backend/user_data.db (60 KB)         Docker volume: /app/data/user_data.db
  ↑ local only, NOT in git            ↑ persistent across container restarts
```

> [!IMPORTANT]
> `item_bank.db` is **git-tracked** so it can be deployed by rebuilding the Docker image.  
> `user_data.db` is **NOT git-tracked** — it lives on the server volume and must never be overwritten by a deploy.

---

## Quick Reference for Scripts

When writing any Python script that accesses the databases:

```python
# ✅ Item bank (questions, passages, IRT parameters)
DB = os.path.join(os.path.dirname(__file__), '../item_bank.db')  # from backend/scripts/
# or from backend root:
DB = 'backend/item_bank.db'

# ✅ Student data (sessions, responses, scores)
USER_DB = os.path.join(os.path.dirname(__file__), '../user_data.db')
# or from backend root:
USER_DB = 'backend/user_data.db'

# ❌ Never use these old names — they no longer exist:
# toefl_2026.db
# toefl_item_bank.db
# toefl_user_data.db
```

---

## Files That Reference the Databases

| File | References | DB |
|------|-----------|-----|
| `backend/app/database/connection.py` | `DATABASE_URL`, `USER_DATABASE_URL` | Both |
| `backend/Dockerfile` | `ENV DATABASE_URL` | item_bank.db |
| `docker-compose.yml` | `DATABASE_URL`, `USER_DATABASE_URL` | Both |
| `backend/app/scripts/enforce_schema.py` | `DB_PATH` | item_bank.db |
| `backend/scripts/*.py` | `db_path` | item_bank.db |
| `agents/scripts/*.py` | `DB_PATH` | item_bank.db |

---

## History

| Date | Event |
|------|-------|
| 2026-02 (early) | `toefl_2026.db` created as item bank; `toefl_user_data.db` created for student data |
| 2026-02-28 | Renamed to `item_bank.db` and `user_data.db` for clarity. All references updated. |
| 2026-02-28 | 5 empty stub databases deleted (`database.db`, `local.db`, `test.db`, `toefl.db`, `toefl_item_bank.db`) |
