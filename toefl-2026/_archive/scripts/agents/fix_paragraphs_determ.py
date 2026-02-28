# ============================================================
# Purpose:       Apply deterministic paragraph fixes to IELTS parsed JSON files based on paragraph_issues.json report.
# Usage:         python agents/scripts/fix_paragraphs_determ.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import json
import re

PARSED_DIR = "/Users/tengda/Antigravity/IELTS/parsed"

def fix_paragraphs_deterministically():
    try:
        with open("/Users/tengda/Antigravity/toefl-2026/agents/scripts/paragraph_issues.json", "r") as f:
            issues = json.load(f)
    except FileNotFoundError:
        print("paragraph_issues.json not found.")
        return

    fixed_count = 0
    
    for issue in issues:
        filename = issue['file']
        filepath = os.path.join(PARSED_DIR, filename)
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            paragraphs = data.get('passage', {}).get('paragraphs', [])
            new_paragraphs = []
            
            for p in paragraphs:
                text = p.get('text', '')
                # Split by \n\n or \n if that's what separates them
                # Sometimes it's "\n\n", sometimes "\n" depending on PDF extraction.
                parts = re.split(r'\n{1,}', text)
                
                for part in parts:
                    part = part.strip()
                    if part:
                        # Reconstruct the paragraph object
                        new_paragraphs.append({
                            "label": p.get("label", ""),
                            "text": part
                        })
            
            # Update the data
            data['passage']['paragraphs'] = new_paragraphs
            
            # Save it back
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            print(f"Fixed {filename}: changed from {len(paragraphs)} to {len(new_paragraphs)} paragraphs.")
            fixed_count += 1
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print(f"Successfully processed {fixed_count} files deterministically.")

if __name__ == '__main__':
    fix_paragraphs_deterministically()
