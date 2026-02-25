# Backend API Map

> Last updated: 2026-02-25

## Item Endpoints

| Method | Path | Purpose | Status |
|--------|------|---------|--------|
| `GET` | `/api/items` | Fetch all items | ✅ Live |
| `GET` | `/api/items/audit` | Item counts by section/task_type | ✅ Live |
| `GET` | `/api/items?section=READING` | Filter items by section | ✅ Live |
| `GET` | `/api/items?section=READING&task_type=COMPLETE_THE_WORDS` | Filter by section + task type | ✅ Live |
| `POST` | `/api/items` | Create new item | ✅ Live |
| `PUT` | `/api/items/{id}` | Update item | ✅ Live |
| `DELETE` | `/api/items/{id}` | Delete item | ✅ Live |

## Session Endpoints

| Method | Path | Purpose | Status |
|--------|------|---------|--------|
| `POST` | `/api/sessions` | Create new test session | ✅ Live |
| `GET` | `/api/sessions/{id}` | Get session state | ✅ Live |
| `PUT` | `/api/sessions/{id}` | Update session (sync responses) | ✅ Live |

## Missing/Needed Endpoints

| Method | Path | Purpose | Priority |
|--------|------|---------|----------|
| `GET` | `/api/items/stage?section=READING&stage=router` | Get items for a specific MST stage | 🔴 High |
| `GET` | `/api/items/random?section=READING&task_type=X&count=N` | Random item selection for test assembly | 🔴 High |
| `POST` | `/api/scoring/writing` | AI scoring for writing responses | 🟡 Medium |
| `POST` | `/api/scoring/speaking` | AI scoring for speaking responses | 🟡 Medium |

## Database Schema Notes

- Items stored in SQLite via SQLAlchemy
- Current item fields: `id`, `section`, `task_type`, `content` (JSON), `created_at`
- **Missing fields**: `difficulty_level`, `cefr_level`, `stage` (for MST routing)
- Backend runs on FastAPI with uvicorn

## Infrastructure

| Service | URL | Notes |
|---------|-----|-------|
| Backend (local) | `http://localhost:8000` | FastAPI |
| Frontend (local) | `http://localhost:3000` | Next.js |
| Tunnel (public) | `https://mean-groups-vanish.loca.lt` | localtunnel → port 8000 |
