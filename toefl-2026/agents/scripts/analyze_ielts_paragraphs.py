# ============================================================
# Purpose:       Analyze parsed IELTS JSON files for paragraph-level structural issues (e.g. missing splits, oversized paragraphs).
# Usage:         python agents/scripts/analyze_ielts_paragraphs.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import json

PARSED_DIR = "/Users/tengda/Antigravity/IELTS/parsed"

def analyze():
    files = [f for f in os.listdir(PARSED_DIR) if f.endswith('.json')]
    output_issues = []
    
    for file in files:
        filepath = os.path.join(PARSED_DIR, file)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            passage = data.get('passage', {})
            paragraphs = passage.get('paragraphs', [])
            
            num_paragraphs = len(paragraphs)
            max_words = 0
            total_words = 0
            
            for p in paragraphs:
                text = p.get('text', '')
                word_count = len(text.split())
                total_words += word_count
                if word_count > max_words:
                    max_words = word_count
                    
            # A typical IELTS paragraph is 50-150 words.
            # If max_words > 200 or there are very few paragraphs, flag it.
            if max_words > 200 or num_paragraphs <= 3:
                output_issues.append({
                    'file': file,
                    'num_paragraphs': num_paragraphs,
                    'max_words': max_words,
                    'total_words': total_words,
                    'id': data.get('id', file)
                })
        except Exception as e:
            print(f"Error reading {file}: {e}")

    output_issues.sort(key=lambda x: x['max_words'], reverse=True)
    
    print(f"Found {len(output_issues)} files with potential paragraph issues:")
    for issue in output_issues:
        print(f"{issue['file']}: {issue['num_paragraphs']} paragraphs, Max Words: {issue['max_words']}, Total Words: {issue['total_words']}")

    # Save to a json list for easier batch processing
    with open('paragraph_issues.json', 'w') as f:
        json.dump(output_issues, f, indent=2)

if __name__ == '__main__':
    analyze()
