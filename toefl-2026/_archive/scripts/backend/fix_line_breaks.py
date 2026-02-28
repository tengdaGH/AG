# ============================================================
# Purpose:       Remediate mid-sentence line breaks in reading passages.
# Usage:         python backend/scripts/fix_line_breaks.py [--dry-run]
# Created:       2026-02-28
# ============================================================
import os
import sys
import json
import logging
import re
import argparse

# Set up paths to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models.models import TestItem, ItemStatus
from app.database.connection import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def clean_text(text) -> tuple:
    """
    Cleans mid-sentence line breaks.
    Supports str, list, and dict types.
    """
    if not text:
        return text, False
    
    if isinstance(text, list):
        modified = False
        new_list = []
        for item in text:
            cleaned, m = clean_text(item)
            new_list.append(cleaned)
            if m: modified = True
        return new_list, modified
    
    if isinstance(text, dict):
        modified = False
        for k, v in text.items():
            cleaned, m = clean_text(v)
            text[k] = cleaned
            if m: modified = True
        return text, modified

    if not isinstance(text, str):
        return text, False
    
    original = text
    # 1. Normalize line endings
    text = text.replace('\r\n', '\n')
    
    # 2. Preserve paragraph breaks
    text = re.sub(r'\n\s*\n', '[[PARAGRAPH]]', text)
    
    # 3. Replace all remaining single newlines with a space
    text = text.replace('\n', ' ')
    
    # 4. Collapse multiple spaces
    text = re.sub(r' +', ' ', text)
    
    # 5. Restore paragraph breaks
    text = text.replace('[[PARAGRAPH]]', '\n\n')
    
    # 6. Final trim
    text = text.strip()
    
    return text, text != original.strip()

def process_db(dry_run=False):
    db = SessionLocal()
    try:
        items = db.query(TestItem).all()
        
        modified_count = 0
        for item in items:
            try:
                # Ensure prompt_content is parsed
                if isinstance(item.prompt_content, str):
                    data = json.loads(item.prompt_content)
                else:
                    data = item.prompt_content
                
                if not data or 'text' not in data:
                    continue
                
                cleaned_passage, was_modified = clean_text(data['text'])
                
                if was_modified:
                    logging.info(f"Cleaning item: {item.id} ({item.task_type})")
                    data['text'] = cleaned_passage
                    item.prompt_content = json.dumps(data)
                    modified_count += 1
                    
                    if not dry_run:
                        item.generation_notes = (item.generation_notes or "") + " [System: Fixed mid-sentence line breaks]"
            except Exception as e:
                logging.error(f"Error processing item {item.id}: {e}")
                
        if not dry_run:
            db.commit()
            logging.info(f"Committed changes for {modified_count} items in database.")
        else:
            logging.info(f"[DRY-RUN] Would have modified {modified_count} items in database.")
            
    finally:
        db.close()

def process_json_file(file_path, dry_run=False):
    if not os.path.exists(file_path):
        logging.warning(f"File not found: {file_path}")
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        modified_count = 0
        # The structure of these JSONs varies. 
        # For ets_official_reading_academic.json, it's a list of items where text is in 'text'
        if isinstance(data, list):
            for entry in data:
                if 'text' in entry:
                    cleaned, was_modified = clean_text(entry['text'])
                    if was_modified:
                        entry['text'] = cleaned
                        modified_count += 1
        elif isinstance(data, dict):
            # Check for common keys like 'passages'
            if 'passages' in data:
                for passage in data['passages']:
                    if 'text' in passage:
                        cleaned, was_modified = clean_text(passage['text'])
                        if was_modified:
                            passage['text'] = cleaned
                            modified_count += 1
            # Check top-level 'text'
            if 'text' in data:
                cleaned, was_modified = clean_text(data['text'])
                if was_modified:
                    data['text'] = cleaned
                    modified_count += 1

        if modified_count > 0:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                logging.info(f"Updated {file_path} (modified {modified_count} entries).")
            else:
                logging.info(f"[DRY-RUN] Would have updated {file_path} (modified {modified_count} entries).")
        else:
            logging.info(f"No changes needed for {file_path}.")
            
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean mid-sentence line breaks.")
    parser.add_argument("--dry-run", action="store_true", help="Don't apply changes.")
    args = parser.parse_args()
    
    logging.info("Starting line break remediation...")
    
    # 1. Process Database
    process_db(dry_run=args.dry_run)
    
    # 2. Process Known Source Files
    source_files = [
        "../../data/ets_official_reading_academic.json",
        "../../data/read-academic-passage-passages.json"
    ]
    # Use the directory of the script to find the relative paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for sf in source_files:
        full_path = os.path.normpath(os.path.join(script_dir, sf))
        process_json_file(full_path, dry_run=args.dry_run)
    
    logging.info("Remediation complete.")
