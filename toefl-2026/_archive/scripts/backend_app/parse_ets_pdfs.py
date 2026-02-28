#!/usr/bin/env python3
"""
parse_ets_pdfs.py - Extracts items from 7 ETS official practice test PDFs.
Output matches the JSON format expected by import_itembank.py.
"""

import os
import json
import re
import argparse
from pathlib import Path
import fitz

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "ets-official-2026"

FILE_MAPPING = {
    "student-practice-test-1.pdf": "ETS-S1",
    "student-practice-test-2.pdf": "ETS-S2",
    "teacher-practice-test-1.pdf": "ETS-T1",
    "teacher-practice-test-2.pdf": "ETS-T2",
    "teacher-practice-test-3.pdf": "ETS-T3",
    "teacher-practice-test-4.pdf": "ETS-T4",
    "teacher-practice-test-5.pdf": "ETS-T5",
}

def clean_text(text: str) -> str:
    lines = []
    for line in text.split('\n'):
        if "TOEFL iBT" in line and "Practice Test" in line:
            continue
        if re.match(r'^\s*\d+\s*$', line):
            continue
        lines.append(line)
    return '\n'.join(lines).strip()

def parse_question_block(text: str) -> dict:
    text = text.strip()
    parts = re.split(r"^\s*\([A-D]\)\s+", text, flags=re.MULTILINE)
    if len(parts) < 2:
        return {"text": text, "options": []}
    return {
        "text": parts[0].strip(),
        "options": [p.strip() for p in parts[1:]]
    }

def segment_pdf(doc) -> dict:
    sections = {
        "reading_m1": "", "reading_m2": "",
        "reading_key_m1": "", "reading_key_m2": "",
        "listening_m1": "", "listening_m2": "",
        "listening_key_m1": "", "listening_key_m2": "",
        "writing": "", "writing_key": "", "speaking": ""
    }
    current_section = None
    for i in range(doc.page_count):
        page_text = doc[i].get_text().strip()
        
        if "Reading Section, Module 1" in page_text and "Answer Key" in page_text:
            current_section = "reading_key_m1"
        elif "Reading Section, Module 2" in page_text and "Answer Key" in page_text:
            current_section = "reading_key_m2"
        elif "Reading Section, Module 1" in page_text:
            current_section = "reading_m1"
        elif "Reading Section, Module 2" in page_text:
            current_section = "reading_m2"
        elif "Listening Section, Module 1" in page_text and "Answer Key" in page_text:
            current_section = "listening_key_m1"
        elif "Listening Section, Module 2" in page_text and "Answer Key" in page_text:
            current_section = "listening_key_m2"
        elif "Listening Section, Module 1" in page_text:
            current_section = "listening_m1"
        elif "Listening Section, Module 2" in page_text:
            current_section = "listening_m2"
        elif "Writing Section" in page_text and "Answer Key" in page_text:
            current_section = "writing_key"
        elif "Writing Section" in page_text:
            current_section = "writing"
        elif "Speaking Section" in page_text:
            current_section = "speaking"
            
        if current_section:
            sections[current_section] += "\n" + clean_text(page_text)
            
    return sections

def _parse_answer_keys(text: str) -> dict:
    # Extremely basic parse: just grab the A, B, C, D letters as a list
    # or the missing letters text. Not perfect but provides raw data.
    text = text.replace('\r\n', '\n')
    lines = [L.strip() for L in text.split('\n') if L.strip()]
    answers = []
    started_keys = False
    for L in lines:
        if "Question" in L or "Answer" in L:
            started_keys = True
            continue
        
        # In Teacher keys, answers are usually alone on lines, e.g. "B" or "ey"
        # Often "1 B", "2 C", or just "B", "C"
        # Let's extract words/letters
        parts = L.split()
        if not parts: continue
        
        ans = parts[-1]
        
        if started_keys and len(ans) > 0:
            answers.append(L)
            
    return {"raw_keys": answers}

def parse_reading_module(text: str, source_id: str, module_id: str) -> dict:
    text = text.replace('\r\n', '\n')
    
    c_test_start = text.find("Fill in the missing letters in the paragraph.")
    if c_test_start == -1:
        return {}
    c_test_text_start = text.find("\n", text.find("(Question", c_test_start)) + 1
    boundaries = list(re.finditer(r"\nRead an? (notice|email|article|advertisement|letter|announcement)\.", text))
    c_test_end = boundaries[0].start() if boundaries else len(text)
    
    c_test_passage = text[c_test_text_start:c_test_end].strip()
    
    chunks = []
    for i in range(len(boundaries)):
        start_idx = boundaries[i].end()
        end_idx = boundaries[i+1].start() if i+1 < len(boundaries) else len(text)
        chunks.append(text[start_idx:end_idx].strip())
        
    daily_life_passages = []
    academic_passage = None
    
    for i, chunk in enumerate(chunks):
        q_start_match = re.search(r"\n\d+\.", chunk)
        if not q_start_match:
            continue
            
        prompt_text = chunk[:q_start_match.start()].strip()
        rest_of_chunk = chunk[q_start_match.start():].strip()
        
        question_blocks = re.split(r"\n(?=\d+\.)", "\n" + rest_of_chunk)
        question_blocks = [q.strip() for q in question_blocks if q.strip()]
        
        daily_questions = []
        academic_text = ""
        academic_questions = []
        parsing_academic = False
        
        for qb in question_blocks:
            if parsing_academic:
                academic_questions.append(parse_question_block(qb))
                continue
                
            d_match = re.search(r"^\(D\)\s+.*$", qb, re.MULTILINE)
            if d_match:
                d_end = d_match.end()
                daily_q_text = qb[:d_end].strip()
                daily_questions.append(parse_question_block(daily_q_text))
                
                trailing = qb[d_end:].strip()
                if trailing:
                    parsing_academic = True
                    academic_text = trailing
            else:
                daily_questions.append(parse_question_block(qb))
                
        daily_life_passages.append({
            "content": prompt_text,
            "questions": daily_questions
        })
        
        if parsing_academic:
            academic_passage = {
                "text": academic_text,
                "questions": academic_questions
            }
            
    return {
        "c_test_passage": c_test_passage,
        "daily_life_passages": daily_life_passages,
        "academic_passage": academic_passage
    }

def parse_listening_module(text: str, source_id: str, module_id: str) -> dict:
    text = text.replace('\r\n', '\n')
    
    listen_to_matches = list(re.finditer(r"\nListen to.*?\.", text))
    end_of_choose_response = listen_to_matches[0].start() if listen_to_matches else len(text)
    
    cr_text = text[:end_of_choose_response].strip()
    cr_questions_raw = re.split(r"\n(?=\d+\.\s+(?:Man|Woman|Professor):|^\d+\.\s+)", "\n" + cr_text, flags=re.MULTILINE)
    cr_questions = [parse_question_block(q.strip()) for q in cr_questions_raw if q.strip() and re.match(r"^\d+\.", q.strip())]
    
    passages = []
    for i in range(len(listen_to_matches)):
        start_idx = listen_to_matches[i].start()
        end_idx = listen_to_matches[i+1].start() if i+1 < len(listen_to_matches) else len(text)
        chunk = text[start_idx:end_idx].strip()
        
        q_start_match = re.search(r"\n\d+\.", chunk)
        if q_start_match:
            transcript = chunk[:q_start_match.start()].strip()
            questions_text = chunk[q_start_match.start():].strip()
            qb = [parse_question_block(q.strip()) for q in re.split(r"\n(?=\d+\.)", "\n" + questions_text) if q.strip() and re.match(r"^\d+\.", q.strip())]
            passages.append({
                "transcript": transcript,
                "questions": qb
            })
            
    return {
        "choose_response": cr_questions,
        "passages": passages
    }

def parse_wad_text(text: str) -> tuple[str, str, str]:
    pattern = re.compile(
        r'(Why\s+or\s+why\s+not\?|Why\?|What\s+is\s+your\s+opinion\s+on\s+this\?|and\s+why\?)\s*\n+', 
        re.IGNORECASE
    )
    match = pattern.search(text)
    
    if match:
        split_idx = match.end()
        prompt = text[:split_idx].strip()
        rest = text[split_idx:].strip()
    else:
        prompt = text
        rest = ""

    lines = [l.strip() for l in rest.split("\n") if l.strip()]
    rest_str = " ".join(lines).replace("\xa0", " ")
    
    boundaries = [m.end() for m in re.finditer(r'[.?!"\']\s+(?=[A-Z])', rest_str)]
    
    if not boundaries:
        mid = len(rest_str) // 2
        student1 = rest_str[:mid].strip()
        student2 = rest_str[mid:].strip()
    else:
        mid = len(rest_str) / 2
        closest_b = min(boundaries, key=lambda b: abs(b - mid))
        student1 = rest_str[:closest_b].strip()
        student2 = rest_str[closest_b:].strip()
        
    return prompt, student1, student2

def parse_bas_text(text: str) -> list[dict]:
    items = []
    parts = re.split(r"(?:\n|^)\d+\.\s+", text)
    for p in parts[1:]:
        lines = [line.strip() for line in p.split("\n") if line.strip()]
        if not lines:
            continue
        context = lines[0]
        
        blank_idx = -1
        for idx, line in enumerate(lines):
            if line.startswith("_____"):
                blank_idx = idx
                break
        
        if blank_idx == -1:
            end_punct = "."
            frag_line = lines[-1]
        else:
            end_punctMatch = re.search(r"([.?])$", lines[blank_idx])
            end_punct = end_punctMatch.group(1) if end_punctMatch else "."
            frag_line = lines[-1]
            if "Writing Section" in frag_line:
                if len(lines) > 1:
                    frag_line = lines[-2]
                else:
                    frag_line = ""
                
        fragments = [f.strip() for f in frag_line.split("/") if f.strip() and f.strip() != "Writing Section"]
        if fragments:
            items.append({
                "context": context,
                "endPunctuation": end_punct,
                "fragments": fragments
            })
    return items

def parse_writing_section(text: str, source_id: str) -> dict:
    text = text.replace('\r\n', '\n')
    bas_start = text.rfind("Build a Sentence")
    email_start = text.rfind("Write an Email")
    wad_start = text.rfind("Write for an Academic Discussion")
    
    if bas_start == -1 or email_start == -1 or wad_start == -1:
        return {}
        
    bas_text = text[bas_start:email_start].strip()
    email_text = text[email_start:wad_start].strip()
    wad_text = text[wad_start:].strip()
    
    bas_items = parse_bas_text(bas_text)
    wad_prompt, wad_s1, wad_s2 = parse_wad_text(wad_text)
    
    return {
        "build_a_sentence_items": bas_items,
        "email_prompt": email_text,
        "wad": {
            "professor_prompt": wad_prompt,
            "student_1_name": "Student A",
            "student_1_response": wad_s1,
            "student_2_name": "Student B",
            "student_2_response": wad_s2
        }
    }

def parse_speaking_section(text: str, source_id: str) -> dict:
    text = text.replace('\r\n', '\n')
    lar_start = text.rfind("Listen and Repeat")
    int_start = text.rfind("Take an Interview")
    
    if lar_start == -1 or int_start == -1:
        return {}
        
    lar_text = text[lar_start:int_start].strip()
    int_text = text[int_start:].strip()
    
    return {
        "listen_and_repeat_text": lar_text,
        "interview_text": int_text
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Dry run parser")
    args = parser.parse_args()
    
    # Storage for the aggregated JSONs
    agg = {
        "reading_academic": {"meta": {}, "passages": []},
        "reading_daily_life": {"meta": {}, "sets": {"ETS": {"passages": []}}},
        "reading_ctest": {"meta": {}, "passages": []},
        "listening_cr": {"meta": {}, "items": []},
        "listening_passages": {"meta": {}, "passages": []},
        "writing_bas": {"meta": {}, "items": []},
        "writing_email": {"meta": {}, "prompts": []},
        "writing_wad": {"meta": {}, "prompts": []},
        "speaking_repeat": {"meta": {}, "items": []},
        "speaking_interview": {"meta": {}, "interviews": []},
    }
    
    for pdf_name, source_id in FILE_MAPPING.items():
        pdf_path = PDF_DIR / pdf_name
        if not pdf_path.exists():
            continue
            
        print(f"=============================")
        print(f"Processing {pdf_name} -> {source_id}")
        doc = fitz.open(str(pdf_path))
        sections = segment_pdf(doc)
        doc.close()
        
        # Keys
        r_key_m1 = _parse_answer_keys(sections["reading_key_m1"])
        r_key_m2 = _parse_answer_keys(sections["reading_key_m2"])
        l_key_m1 = _parse_answer_keys(sections["listening_key_m1"])
        l_key_m2 = _parse_answer_keys(sections["listening_key_m2"])
        w_key = _parse_answer_keys(sections["writing_key"])
        
        m1_read = parse_reading_module(sections["reading_m1"], source_id, "M1")
        m2_read = parse_reading_module(sections["reading_m2"], source_id, "M2")
        
        o_ctest = agg["reading_ctest"]["passages"]
        if m1_read.get("c_test_passage"):
            o_ctest.append({"id": f"{source_id}-R-M1-CT", "text": m1_read["c_test_passage"], "keys": r_key_m1})
        if m2_read.get("c_test_passage"):
            o_ctest.append({"id": f"{source_id}-R-M2-CT", "text": m2_read["c_test_passage"], "keys": r_key_m2})
            
        o_dl = agg["reading_daily_life"]["sets"]["ETS"]["passages"]
        for i, p in enumerate(m1_read.get("daily_life_passages", [])):
            o_dl.append({"id": f"{source_id}-R-M1-DL-{i+1}", "content": p["content"], "questions": p["questions"], "keys": r_key_m1})
        for i, p in enumerate(m2_read.get("daily_life_passages", [])):
            o_dl.append({"id": f"{source_id}-R-M2-DL-{i+1}", "content": p["content"], "questions": p["questions"], "keys": r_key_m2})
            
        o_ac = agg["reading_academic"]["passages"]
        if m1_read.get("academic_passage"):
            o_ac.append({"id": f"{source_id}-R-M1-AC", "text": m1_read["academic_passage"]["text"], "questions": m1_read["academic_passage"]["questions"], "keys": r_key_m1})
        if m2_read.get("academic_passage"):
            o_ac.append({"id": f"{source_id}-R-M2-AC", "text": m2_read["academic_passage"]["text"], "questions": m2_read["academic_passage"]["questions"], "keys": r_key_m2})
            
            
        m1_list = parse_listening_module(sections["listening_m1"], source_id, "M1")
        m2_list = parse_listening_module(sections["listening_m2"], source_id, "M2")
        
        o_lcr = agg["listening_cr"]["items"]
        for i, cr in enumerate(m1_list.get("choose_response", [])):
            o_lcr.append({"id": f"{source_id}-L-M1-CR-{i+1}", "text": cr, "keys": l_key_m1})
        for i, cr in enumerate(m2_list.get("choose_response", [])):
            o_lcr.append({"id": f"{source_id}-L-M2-CR-{i+1}", "text": cr, "keys": l_key_m2})
            
        o_lpa = agg["listening_passages"]["passages"]
        for i, p in enumerate(m1_list.get("passages", [])):
            o_lpa.append({"id": f"{source_id}-L-M1-PA-{i+1}", "transcript": p["transcript"], "questions": p["questions"], "keys": l_key_m1})
        for i, p in enumerate(m2_list.get("passages", [])):
            o_lpa.append({"id": f"{source_id}-L-M2-PA-{i+1}", "transcript": p["transcript"], "questions": p["questions"], "keys": l_key_m2})
            
            
        writing = parse_writing_section(sections["writing"], source_id)
        if writing.get("build_a_sentence_items"):
            for i, item in enumerate(writing["build_a_sentence_items"]):
                agg["writing_bas"]["items"].append({
                    "id": f"{source_id}-W-BAS-{i+1}", 
                    "context": item["context"], 
                    "endPunctuation": item["endPunctuation"],
                    "fragments": item["fragments"],
                    "keys": w_key
                })
        if writing.get("email_prompt"):
            agg["writing_email"]["prompts"].append({"id": f"{source_id}-W-EMAIL", "prompt": writing["email_prompt"]})
        if writing.get("wad"):
            wad = writing["wad"]
            agg["writing_wad"]["prompts"].append({
                "id": f"{source_id}-W-WAD", 
                "prompt": wad["professor_prompt"],
                "professor_prompt": wad["professor_prompt"],
                "student_1_name": wad["student_1_name"],
                "student_1_response": wad["student_1_response"],
                "student_2_name": wad["student_2_name"],
                "student_2_response": wad["student_2_response"],
                "keys": w_key
            })
            
        speaking = parse_speaking_section(sections["speaking"], source_id)
        if speaking.get("listen_and_repeat_text"):
            agg["speaking_repeat"]["items"].append({"id": f"{source_id}-S-LAR", "text": speaking["listen_and_repeat_text"]})
        if speaking.get("interview_text"):
            agg["speaking_interview"]["interviews"].append({"id": f"{source_id}-S-INT", "text": speaking["interview_text"]})

    if args.dry_run:
        print("\n=== DRY RUN SUMMARY ===")
        for k, v in agg.items():
            cnt = len(v.get("passages", v.get("items", v.get("prompts", v.get("interviews", [])))))
            if "sets" in v:
                cnt = len(v["sets"]["ETS"]["passages"])
            print(f"{k}: {cnt} items")
        return
        
    for k, v in agg.items():
        out_path = DATA_DIR / f"ets_official_{k}.json"
        with open(out_path, 'w') as f:
            json.dump(v, f, ensure_ascii=False, indent=2)
        print(f"Saved {out_path} ({len(v.get('passages', v.get('items', v.get('prompts', v.get('interviews', v.get('sets', {'ETS': {'passages': []}})['ETS']['passages'])))))} items)")

if __name__ == "__main__":
    main()
