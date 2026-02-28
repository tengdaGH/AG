# ============================================================
# Purpose:       Remove all WRITE_ACADEMIC_DISCUSSION task_type items and related source files from the SQLite item bank.
# Usage:         python agents/scripts/remove_academic_discussion.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import sqlite3
import os

db_path = '/Users/tengda/Antigravity/toefl-2026/backend/item_bank.db'

def remove_academic_discussion_items():
    if not os.path.exists(db_path):
        print("Database not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Define the task type to remove
    target_type = 'WRITE_ACADEMIC_DISCUSSION'

    # Check how many items exist before removal
    cursor.execute("SELECT COUNT(*) FROM test_items WHERE task_type = ?", (target_type,))
    count_to_remove = cursor.fetchone()[0]

    if count_to_remove == 0:
        print(f"No items with task_type '{target_type}' found.")
        conn.close()
        return

    print(f"Removing {count_to_remove} items of type '{target_type}'...")

    # Perform deletion
    cursor.execute("DELETE FROM test_items WHERE task_type = ?", (target_type,))
    
    conn.commit()
    print(f"Purge complete. {count_to_remove} items removed from database.")

    # Also check for any items that might have been uncategorized but came from known discussion files
    discussion_files = ['writing-academic-discussion-prompts.json', 'toefl-2026-academic-discussion.json']
    for file in discussion_files:
        cursor.execute("DELETE FROM test_items WHERE source_file = ?", (file,))
        removed = cursor.rowcount
        if removed > 0:
            print(f"Removed additional {removed} items linked to source file: {file}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    remove_academic_discussion_items()
