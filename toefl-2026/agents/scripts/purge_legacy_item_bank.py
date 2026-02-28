# ============================================================
# Purpose:       Purge all legacy (non-toefl-2026-prefixed) items from the SQLite item bank to clean the database.
# Usage:         python agents/scripts/purge_legacy_item_bank.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import sqlite3
import os

db_path = '/Users/tengda/Antigravity/toefl-2026/backend/item_bank.db'

def purge_legacy_items():
    if not os.path.exists(db_path):
        print("Database not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get counts before
    cursor.execute("SELECT COUNT(*) FROM test_items")
    initial_count = cursor.fetchone()[0]

    # Identify sources
    cursor.execute("SELECT DISTINCT source_file FROM test_items")
    sources = [row[0] for row in cursor.fetchall()]

    legacy_sources = []
    keep_sources = []

    for s in sources:
        if not s or not s.startswith('toefl-2026-'):
            legacy_sources.append(s)
        else:
            keep_sources.append(s)

    print(f"Kept sources: {keep_sources}")
    print(f"Legacy sources to purge: {legacy_sources}")

    total_removed = 0
    for s in legacy_sources:
        if s is None:
            cursor.execute("DELETE FROM test_items WHERE source_file IS NULL")
        elif s == '':
             cursor.execute("DELETE FROM test_items WHERE source_file = ''")
        else:
            cursor.execute("DELETE FROM test_items WHERE source_file = ?", (s,))
        
        total_removed += cursor.rowcount

    conn.commit()
    
    # Final count
    cursor.execute("SELECT COUNT(*) FROM test_items")
    final_count = cursor.fetchone()[0]
    
    conn.close()

    print(f"\nPurge complete.")
    print(f"Initial items: {initial_count}")
    print(f"Items removed: {total_removed}")
    print(f"Remaining items: {final_count}")

if __name__ == "__main__":
    purge_legacy_items()
