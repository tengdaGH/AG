#!/usr/bin/env python3
"""
extract_with_pymupdf.py
========================
Phase 1 of the IELTS Reading reprocessing pipeline.

Extracts all passages from 雅思阅读new最全题库.pdf using PyMuPDF (fitz).
The PDF has 3,291 pages and 651 IELTS reading passages, each with:
  - A reading passage (titled, optionally with paragraph labels A-H)
  - 2-3 question groups (13 questions total per passage)
  - A Solution section with answer keys

Output: One JSON per passage in IELTS/extracted/ with separated passage text,
        question text, and answer keys.

Location : /Users/tengda/Antigravity/IELTS/scripts/
Venv     : source /Users/tengda/Antigravity/toefl-2026/backend/venv/bin/activate
Run      : python /Users/tengda/Antigravity/IELTS/scripts/extract_with_pymupdf.py
Self-destruct: NO — permanent pipeline artifact
"""

import os
import sys
import json
import re
import fitz  # pymupdf
from datetime import datetime


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PDF_PATH = "/Users/tengda/Antigravity/IELTS/雅思阅读new最全题库.pdf"
OUTPUT_DIR = "/Users/tengda/Antigravity/IELTS/extracted"


def get_passages_from_toc(doc):
    """
    Parse the PDF's table of contents to extract passage boundaries.
    
    TOC structure per passage:
      L1: slug (e.g., 'a-brief-history-of-tea')
      L2: 'Reading Practice'
      L3: Title (e.g., 'A Brief History of Tea')
      L4: Question ranges (e.g., 'Questions 1-7')
      L4: 'Solution:'
    
    Returns a list of dicts with passage metadata and page ranges.
    """
    toc = doc.get_toc()
    l1_entries = [(i, e) for i, e in enumerate(toc) if e[0] == 1]
    
    passages = []
    for idx, (toc_idx, entry) in enumerate(l1_entries):
        slug = entry[1]
        start_page = entry[2]  # 1-indexed
        
        # End page is the start of the next L1 entry
        if idx + 1 < len(l1_entries):
            end_page = l1_entries[idx + 1][1][2] - 1
        else:
            end_page = doc.page_count
        
        # Find sub-entries for this passage
        if idx + 1 < len(l1_entries):
            next_toc_idx = l1_entries[idx + 1][0]
        else:
            next_toc_idx = len(toc)
        
        sub_entries = toc[toc_idx + 1:next_toc_idx]
        
        # Extract title from L3 entry
        title = None
        for se in sub_entries:
            if se[0] == 3 and se[1].strip():
                title = se[1].strip()
                break
        
        # Find Solution page
        solution_page = None
        for se in sub_entries:
            if 'Solution' in se[1]:
                solution_page = se[2]  # 1-indexed
                break
        
        # Find question range entries
        question_sections = []
        for se in sub_entries:
            if se[0] == 4 and 'Question' in se[1]:
                question_sections.append({
                    'label': se[1].strip(),
                    'page': se[2]
                })
        
        passages.append({
            'slug': slug,
            'title': title or slug,
            'start_page': start_page,
            'end_page': end_page,
            'solution_page': solution_page,
            'question_sections': question_sections,
        })
    
    return passages


def extract_page_text(doc, page_num_1indexed, sort=False):
    """Extract text from a 1-indexed page number."""
    if page_num_1indexed < 1 or page_num_1indexed > doc.page_count:
        return ""
    return doc[page_num_1indexed - 1].get_text(sort=sort)


def extract_passage_and_questions(doc, passage_info):
    """
    Extract the full text and attempt to split passage from questions based on pages.
    """
    start = passage_info['start_page']
    end = passage_info['end_page']
    sol_page = passage_info.get('solution_page')
    
    if sol_page:
        end = sol_page - 1
        
    q_sections = passage_info['question_sections']
    if q_sections:
        # Questions typically start on the page of the first question section
        first_q_page = min(qs['page'] for qs in q_sections)
    else:
        # If no explicit question sections, assume passage is whole thing
        first_q_page = end + 1
        
    passage_text = ""
    questions_text = ""
    
    for p in range(start, end + 1):
        text = extract_page_text(doc, p)
        if p < first_q_page:
            passage_text += text + "\n"
        else:
            questions_text += text + "\n"
            
    # If passage text and questions are on the same page, we just pass
    # everything as passage_text for now and let the LLM sort it out,
    # or if we have questions_text, we keep it separate.
    return passage_text.strip(), questions_text.strip()




def extract_solution_text(doc, passage_info):
    sol_page = passage_info.get('solution_page')
    if not sol_page:
        return ""
    text = extract_page_text(doc, sol_page, sort=True)
    if sol_page < passage_info['end_page']:
        next_text = extract_page_text(doc, sol_page + 1, sort=True)
        import re
        if re.search(r'^\d+\.', next_text.strip()):
            text += "\n" + next_text
    return text.strip()

def parse_answer_key(solution_text):
    if not solution_text: return {}
    import re
    sol_idx = solution_text.find('Solution:')
    if sol_idx >= 0:
        solution_text = solution_text[sol_idx + len('Solution:'):]
    text = solution_text.strip()
    lines = text.split('\n')
    tokens = [line.strip() for line in lines if line.strip()]
    flat = ' '.join(tokens)
    answers = {}
    pattern = re.compile(r'(?:^|\s)(\d{1,2})\.\s*')
    matches = list(pattern.finditer(flat))
    for i, m in enumerate(matches):
        num = int(m.group(1))
        if num < 1 or num > 40: continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(flat)
        answer = flat[start:end].strip()
        answer = re.sub(r'\s+\d{1,2}\s*$', '', answer).strip()
        if answer: answers[num] = answer
    cleaned = {}
    for num, ans in answers.items():
        ans = re.sub(r'\s+', ' ', ans).strip()
        cleaned[num] = ans
    return cleaned

def extract_single_passage(doc, passage_info, passage_idx):
    """Extract a complete passage with all components."""
    
    passage_text, questions_text = extract_passage_and_questions(doc, passage_info)
    solution_text = extract_solution_text(doc, passage_info)
    answer_key = parse_answer_key(solution_text)
    
    # Generate a zero-padded ID
    passage_id = f"ielts-r-{passage_idx + 1:04d}"
    
    result = {
        'id': passage_id,
        'slug': passage_info['slug'],
        'title': passage_info['title'],
        'page_range': [passage_info['start_page'], passage_info['end_page']],
        'passage_text': passage_text,
        'questions_text': questions_text,
        'full_text': (passage_text + "\n\n" + questions_text).strip(),
        'solution_text': solution_text,
        'answer_key': {str(k): v for k, v in answer_key.items()},
        'question_sections': passage_info['question_sections'],
        'extracted_at': datetime.now().isoformat(),
    }
    
    return result


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"Opening PDF: {PDF_PATH}")
    doc = fitz.open(PDF_PATH)
    print(f"Total pages: {doc.page_count}")
    
    passages = get_passages_from_toc(doc)
    print(f"Total passages detected from TOC: {len(passages)}")
    
    # Check for --dry-run flag
    if '--dry-run' in sys.argv:
        print("\n=== DRY RUN ===")
        for i, p in enumerate(passages):
            sol = "✅" if p['solution_page'] else "❌"
            print(f"  {i+1:4d}. {p['slug']:<60s} pages {p['start_page']}-{p['end_page']}  sol:{sol}")
        print(f"\nTotal: {len(passages)} passages")
        no_sol = sum(1 for p in passages if not p['solution_page'])
        print(f"Missing solution pages: {no_sol}")
        doc.close()
        return
    
    # Process all passages
    success = 0
    errors = 0
    skipped = 0
    
    for i, passage_info in enumerate(passages):
        passage_id = f"ielts-r-{i + 1:04d}"
        out_path = os.path.join(OUTPUT_DIR, f"{passage_id}.json")
        
        if os.path.exists(out_path) and '--force' not in sys.argv:
            skipped += 1
            continue
        
        try:
            result = extract_single_passage(doc, passage_info, i)
            
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            answer_count = len(result['answer_key'])
            success += 1
            
            if (i + 1) % 50 == 0 or i == 0:
                print(f"  [{i+1}/{len(passages)}] {passage_id}: {result['title'][:50]} ({answer_count} answers)")
                
        except Exception as e:
            errors += 1
            print(f"  ❌ [{i+1}] {passage_info['slug']}: {e}")
    
    doc.close()
    
    print(f"\n{'='*60}")
    print(f"Extraction complete!")
    print(f"  Success:  {success}")
    print(f"  Skipped:  {skipped}")
    print(f"  Errors:   {errors}")
    print(f"  Total:    {len(passages)}")
    print(f"  Output:   {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
