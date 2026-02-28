# ============================================================
# Purpose:       Deterministically fix paragraph splits in IELTS batch 2 JSON files (ielts-r-007, 016, 046, 012, 030).
# Usage:         python agents/scripts/fix_batch_2.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import json

PARSED_DIR = "/Users/tengda/Antigravity/IELTS/parsed"

splits_map = {
    "ielts-r-007.json": {
        "Based on her examination of ancient pieces of pottery, Ms Perry concludes": ["Based on her examination of ancient pieces of pottery, Ms Perry concludes"],
        "Other researchers, such as Jennifer Billing and Paul Sherman": ["Other researchers, such as Jennifer Billing and Paul Sherman"],
        "Joshua Tewksbury, an ecologist at the University of Washington": ["Joshua Tewksbury, an ecologist at the University of Washington"],
        "Even so, Tewksbury didn’t believe that deterring rodents": ["Even so, Tewksbury didn’t believe that deterring rodents"],
        "‘Capsaicin demonstrates the incredible elegance of evolution,’ says Tewksbury.": ["‘Capsaicin demonstrates the incredible elegance of evolution,’ says Tewksbury."]
    },
    "ielts-r-016.json": {
        "However, by 1834 the company had lost its trading monopolies": ["However, by 1834 the company had lost its trading monopolies"],
        "But now that tea could be traded freely, a few smart sailors": ["But now that tea could be traded freely, a few smart sailors"],
        "British merchants resolved to build their own clippers": ["British merchants resolved to build their own clippers"],
        "Then in 1851 a British shipowner, Richard Green": ["Then in 1851 a British shipowner, Richard Green"]
    },
    "ielts-r-046.json": {
        "The purpose of this initial ascent is to build up": ["The purpose of this initial ascent is to build up"],
        "As the train starts coasting down the hill": ["As the train starts coasting down the hill"],
        "At its most basic level, this is all a roller coaster is": ["At its most basic level, this is all a roller coaster is"]
    },
    "ielts-r-012.json": {
        "Antonio de Herrera y Tordesillas describes a ritual game": ["Antonio de Herrera y Tordesillas describes a ritual game"],
        "The first description of latex (liquid rubber) extraction": ["The first description of latex (liquid rubber) extraction"],
        "However, no real interest in rubber was shown by any European": ["However, no real interest in rubber was shown by any European"],
        "In 1747 the first description of the rubber tree": ["In 1747 the first description of the rubber tree"]
    },
    "ielts-r-030.json": {
        "It’s not clear why Lucy left the safety of the trees.": ["It’s not clear why Lucy left the safety of the trees."],
        "In line with this idea, recent evidence suggests": ["In line with this idea, recent evidence suggests"],
        "Fossilised crocodile and turtle eggs were found": ["Fossilised crocodile and turtle eggs were found"],
        "How did early humans process all these new foods?": ["How did early humans process all these new foods?"]
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
