---
description: Deploy TOEFL 2026 to Tencent Cloud — push to GitHub then trigger cloud pull & rebuild
---

# /deploy — One-Command Deployment Workflow

Deploys the local codebase to production on Tencent Cloud (101.32.187.39).
Always run Alfred first to verify the platform is healthy before deploying.

## Prerequisites

- Local backend is running clean (no `frontend/.env.local`)
- All changes are saved
- You are in the `toefl-2026/` directory or the repo root

---

## Step 1 — Pre-deploy sanity checks

// turbo
```bash
# Verify no .env.local (would break cloud connectivity if accidentally committed)
[ -f /Users/tengda/Documents/Antigravity/toefl-2026/frontend/.env.local ] && echo "❌ STOP: .env.local exists — delete it before deploying" && exit 1 || echo "✅ .env.local absent"
# Show what will be committed/pushed
cd /Users/tengda/Documents/Antigravity && git status --short && git log origin/main..HEAD --oneline
```

Review the output. If there are unexpected files staged (e.g. `*.db`, secrets), stop and fix before proceeding.

---

## Step 2 — Commit & push to GitHub

```bash
cd /Users/tengda/Documents/Antigravity
git add -A
git status
```

Review what is staged. Then commit and push:

```bash
git commit -m "deploy: <brief description of what changed>"
git push origin main
```

Confirm: `git log --oneline -3` should show your commit at the top.

---

## Step 3 — Trigger cloud pull & rebuild

SSH into Tencent Cloud and run the update:

```bash
ssh root@101.32.187.39 "cd /root/AG && git pull origin main && cd toefl-2026 && sudo docker-compose up -d --build 2>&1 | tail -20"
```

This will:
1. Pull the latest code from GitHub
2. Rebuild the Docker image (includes baking in the new `item_bank.db`)
3. Restart the containers

Expected output ends with `toefl_backend ... done` and `toefl_frontend ... done`.

---

## Step 4 — Verify deployment

// turbo
```bash
# Hit the cloud health endpoint — expect HTTP 200
curl -s -o /dev/null -w "%{http_code}" http://101.32.187.39:8000/docs && echo " ✅ Backend live" || echo " ❌ Backend not responding"
```

If it fails:
```bash
ssh root@101.32.187.39 "docker ps && docker logs toefl_backend --tail 30"
```

---

## Step 5 — Post-deploy Alfred check

Run Alfred immediately after deploying to confirm the cloud is healthy and git is synced:

```bash
cd /Users/tengda/Documents/Antigravity/toefl-2026 && source backend/venv/bin/activate && python3 agents/scripts/alfred_daily_review.py 2>&1 | tail -20
```

Alfred should show:
- ✅ Cloud API responding
- ✅ Git: local HEAD matches remote

---

## Quick Reference — Common Issues

| Symptom | Fix |
|---------|-----|
| `Permission denied (publickey)` | Check SSH key: `ssh-add ~/.ssh/id_rsa` |
| `docker-compose: command not found` | Use `sudo /usr/local/bin/docker-compose` |
| Backend 502 after deploy | `docker logs toefl_backend --tail 50` — usually a missing env var |
| Rebuild takes >5 min | Normal on first deploy after `item_bank.db` change (baking ~50MB) |
| Git pull conflicts on server | `ssh root@101.32.187.39 "cd /root/AG && git reset --hard origin/main"` |

---

## Notes

- The `item_bank.db` is **baked into the Docker image** at build time. Every `item_bank.db` change requires a full `--build`.
- The `user_data.db` lives on a **persistent Docker volume** (`toefl_db_data`) — it is NEVER rebuilt, never overwritten.
- Never commit `user_data.db` to GitHub — student data stays on the server only.
- The frontend hits the cloud API directly — no frontend rebuild needed for backend-only changes unless env vars changed.
