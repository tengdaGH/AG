# ============================================================
# Purpose:       Remove fragmented/malformed legacy Writing Academic Discussion items from the JSON source file and SQLite database.
# Usage:         python agents/scripts/cleanup_legacy_items.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import json
import sqlite3
import os

json_path = '/Users/tengda/Antigravity/toefl-2026/data/writing-academic-discussion-prompts.json'
db_path = '/Users/tengda/Antigravity/toefl-2026/backend/toefl_2026.db'

def is_fragmented(item):
    q = item.get('question', '').strip()
    # Check if question ends with incomplete words or no punctuation
    incomplete_words = ['that', 'is', 'have', 'the', 'a', 'an', 'and', 'or', 'with', 'for', 'of', 'in', 'on', 'at', 'to', 'from', 'by', 'as', 'examining', 'driving', 'prepared', 'condition', 'condition:', 'while', 'because', 'lack', 'lack of']
    
    # Flags from user handoff
    flagged_ids = ['D37', 'D59', 'D65', 'D83', 'D84', 'D90', 'D92', 'D93']
    if item['id'] in flagged_ids:
        return True
        
    if not q:
        return True
    
    # Very short questions that look like fragments
    if len(q.split()) < 10 and not q.endswith('?'):
        return True
        
    # Questions ending mid-sentence
    if q[-1] not in '.?!':
        return True
        
    # Specific known bad snippets
    if "Besides the benefits to the environment" in q: return True
    if "residents-it will be better" in q: return True
    if "viewers first notice the celebrity" in q: return True
    if "details that are included" in q: return True
    
    # Placeholder authors
    posts = item.get('posts', [])
    for post in posts:
        if '[Author' in post.get('author', ''):
            return True
            
    return False

# 1. Update JSON
with open(json_path, 'r') as f:
    data = json.load(f)

original_count = len(data['prompts'])
cleaned_prompts = [p for p in data['prompts'] if not is_fragmented(p)]
removed_ids = [p['id'] for p in data['prompts'] if is_fragmented(p)]

data['prompts'] = cleaned_prompts

with open(json_path, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Removed {len(removed_ids)} fragmented items from JSON.")
print(f"Legacy IDs removed: {removed_ids}")

# 2. Update Database
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Items from this source file that are in the removed list
    source_filename = 'writing-academic-discussion-prompts.json'
    
    # Check what's in there
    cursor.execute("SELECT id, source_id FROM test_items WHERE source_file = ?", (source_filename,))
    db_items = cursor.fetchall()
    
    count = 0
    for db_id, source_id in db_items:
        if source_id in removed_ids:
            cursor.execute("DELETE FROM test_items WHERE id = ?", (db_id,))
            count += 1
            
    conn.commit()
    conn.close()
    print(f"Removed {count} items from database.")
else:
    print("Database not found at expected path.")
