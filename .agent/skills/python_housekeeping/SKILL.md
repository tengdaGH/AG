---
name: python_housekeeping
description: Rules and conventions for writing, organizing, and cleaning up Python scripts to keep the workspace tidy. Covers script placement, mandatory header commentary, and self-destruct after successful execution.
---

# Python Housekeeping Skill

This skill defines the conventions all agents must follow when writing and executing Python scripts. The goal is to keep the workspace clean, intentional, and self-documenting.

---

## Rule 1: Script Placement

**Never save Python scripts in the root project directory.**

All Python scripts written to perform a task must be saved in one of the designated staging directories:

- **`/scripts/`** — for scripts that may need to be reused or referenced later (e.g., data migrations, seeding utilities, export scripts).
- **`/temp/`** — for purely one-off, throwaway scripts (e.g., quick data inspection, ad-hoc fixes).

> **How to decide:** If you might run this again, use `/scripts/`. If it's a single-use utility, use `/temp/`.

If the target directory does not exist, create it before saving the script:
```bash
mkdir -p /path/to/project/scripts
# or
mkdir -p /path/to/project/temp
```

---

## Rule 2: Mandatory Header Comment

Every Python script you write **must** begin with a standard header block. This makes the script self-documenting, so anyone (including the original author, three days later) knows exactly what it does without reading the code.

Use this exact format at the very top of every file:

```python
# ============================================================
# Purpose:    [One-sentence description of what this script does]
# Usage:      [How to run it, e.g. `python scripts/export_users.py`]
# Created:    [Date, e.g. 2026-02-25]
# Self-Destruct: [Yes / No — will this file be deleted after use?]
# ============================================================
```

**Example:**

```python
# ============================================================
# Purpose:    Exports all active user records to a CSV file for the Q1 audit.
# Usage:      python scripts/export_users.py
# Created:    2026-02-25
# Self-Destruct: Yes
# ============================================================

import csv
# ... rest of the script
```

---

## Rule 3: Self-Destruct After Successful Execution

If a script is purely task-specific and should not persist after completing its job, the agent must **delete the script file after it has been successfully executed.**

**When to self-destruct:** Any script whose `Self-Destruct` header field is `Yes`.

**How to do it:** After confirming the script ran successfully (verify the expected output/side-effect first), delete the file using the `run_command` tool:

```bash
rm /path/to/project/temp/my_script.py
```

> [!CAUTION]
> Never delete the script before confirming success. Always verify the intended outcome first (e.g., check that a file was exported, a record was updated, or the expected output was printed). Only then issue the delete command.

**Workflow for a self-destructing script:**
1. Write the script with `Self-Destruct: Yes` in the header.
2. Run the script and verify success.
3. Delete the script file.
4. Report to the user that the task is complete and the script has been cleaned up.

---

## Rule 4: Database Naming — Mandatory

This project has exactly **two** operational databases. Always use the correct filename. Using the wrong one is a critical error.

| Database | Filename | Purpose |
|----------|----------|---------|
| **Item Bank** | `backend/item_bank.db` | All test items — questions, passages, IRT parameters |
| **Student Data** | `backend/user_data.db` | Student sessions, responses, scores, event logs |

**When writing any script that opens a database:**

```python
# ✅ Correct — item bank
DB = os.path.join(os.path.dirname(__file__), '../item_bank.db')

# ✅ Correct — student data
USER_DB = os.path.join(os.path.dirname(__file__), '../user_data.db')

# ❌ These names no longer exist — never use them:
# toefl_2026.db  |  toefl_item_bank.db  |  toefl_user_data.db
```

> [!CAUTION]
> Never run item bank audit scripts against `user_data.db` and vice versa. The two databases have completely different schemas. See `specs/database_guide.md` for the full architecture reference.

---

## Summary Checklist

Before writing any Python script, confirm:

- [ ] The script will be saved in `/scripts/` or `/temp/`, **not** the project root.
- [ ] The file starts with the mandatory 4-line header block.
- [ ] The `Self-Destruct` field is set to `Yes` or `No`.
- [ ] If `Yes`, a plan exists to delete the file after successful execution.
- [ ] If the script accesses a database, it uses **`item_bank.db`** (items) or **`user_data.db`** (students) — never an old name.
