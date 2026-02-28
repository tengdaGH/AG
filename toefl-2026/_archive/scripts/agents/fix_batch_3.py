# ============================================================
# Purpose:       Deterministically fix paragraph splits in IELTS batch 3 JSON files (ielts-r-019, 028).
# Usage:         python agents/scripts/fix_batch_3.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import json

PARSED_DIR = "/Users/tengda/Antigravity/IELTS/parsed"

splits_map = {
    "ielts-r-019.json": {
        "Whereas most of their neighbours regarded the potato with suspicion": ["Whereas most of their neighbours regarded the potato with suspicion"]
    },
    "ielts-r-028.json": {
        "For these and many other reasons, we should not be so upset by the spectacle": ["For these and many other reasons, we should not be so upset by the spectacle"],
        "This is a disaster because nothing is more inefficient than a suburb": ["This is a disaster because nothing is more inefficient than a suburb"]
    }
}

def apply_splits():
    for filename, split_markers in splits_map.items():
        filepath = os.path.join(PARSED_DIR, filename)
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            paragraphs = data.get('passage', {}).get('paragraphs', [])
            new_paragraphs = []
            
            for p in paragraphs:
                text = p.get('text', '')
                
                # Replace markers with a special delimiter
                for marker in split_markers.keys():
                    if marker in text:
                        text = text.replace(marker, f"|||SPLIT|||{marker}")
                
                parts = text.split("|||SPLIT|||")
                for part in parts:
                    part = part.strip()
                    if part:
                        new_paragraphs.append({
                            "label": p.get("label", ""),
                            "text": part
                        })
            
            data['passage']['paragraphs'] = new_paragraphs
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            print(f"Fixed {filename}: now has {len(new_paragraphs)} paragraphs.")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

if __name__ == '__main__':
    apply_splits()
