# ============================================================
# Purpose:       Import legacy TOEFL listening items (HTML format) from 5 source files into the new SQLite item bank.
# Usage:         python agents/scripts/import_legacy_items.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import json
import sqlite3
import os
import re
import uuid

LEGACY_PATH = "/Users/tengda/Documents/Cursor Code"
DB_PATH = "/Users/tengda/Antigravity/toefl-2026/backend/item_bank.db"

SOURCE_FILES = [
    "toefl-listen-repeat-practice.html",
    "toefl-listening-choose-response-practice.html",
    "toefl-listening-academic-talk-practice.html",
    "toefl-listening-announcement-practice.html",
    "toefl-listening-conversation-practice.html"
]

def purge_legacy(cursor):
    for f in SOURCE_FILES:
        cursor.execute("DELETE FROM test_items WHERE source_file = ?", (f,))
    print(f"Purged items from {len(SOURCE_FILES)} source files.")

def get_bracket_content(content, start_idx):
    bracket_count = 0
    in_string = False
    string_char = ""
    for i in range(start_idx, len(content)):
        char = content[i]
        if not in_string:
            if char == "{" : bracket_count += 1
            elif char == "}":
                bracket_count -= 1
                if bracket_count == 0: return content[start_idx:i+1]
            elif char in ["'", '"']:
                in_string = True
                string_char = char
        else:
            if char == string_char and content[i-1] != "\\":
                in_string = False
    return None

def extract_field(pattern, text):
    match = re.search(pattern, text, re.DOTALL)
    if not match: return ""
    val = match.group(1)
    val = val.replace("\\'", "'").replace('\\"', '"')
    return val

def import_listen_and_repeat(cursor):
    path = os.path.join(LEGACY_PATH, "toefl-listen-repeat-practice.html")
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()
    
    set_ids = re.findall(r"(\w+):\s*{\s*label:", content)
    count = 0
    for sid in set_ids:
        start_idx = content.find(f"{sid}:")
        obj_text = get_bracket_content(content, content.find("{", start_idx))
        if not obj_text: continue
        
        label = extract_field(r"label:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        audio_file = extract_field(r"audioFile:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        
        sentences_match = re.search(r"sentences:\s*parseSentences\(\s*\[(.*?)\s*\]\s*\)", obj_text, re.DOTALL)
        if not sentences_match: continue
        sentences_raw = sentences_match.group(1)
        
        sentence_matches = re.finditer(r"{\s*text:\s*\"([^\"]+)\",\s*start:\s*\"([^\"]+)\",\s*end:\s*\"([^\"]+)\"\s*}", sentences_raw)
        sentences = [{"text": sm.group(1), "start": sm.group(2), "end": sm.group(3)} for sm in sentence_matches]
        
        prompt_content = {"title": label, "topic": label.split(" — ")[1] if " — " in label else label, "audio_file": audio_file, "sentences": sentences}
        cursor.execute("""
            INSERT INTO test_items (id, section, task_type, target_level, irt_difficulty, irt_discrimination, prompt_content, source_file, source_id, is_active, version, exposure_count, generated_by_model, media_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), "SPEAKING", "LISTEN_AND_REPEAT", "B1", 0.0, 1.0, json.dumps(prompt_content), "toefl-listen-repeat-practice.html", sid, True, 1, 0, 'Legacy', audio_file))
        count += 1
    print(f"Imported {count} LISTEN_AND_REPEAT sets.")

def import_listen_choose_response(cursor):
    path = os.path.join(LEGACY_PATH, "toefl-listening-choose-response-practice.html")
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()
    
    ids = re.findall(r"id:\s*'([A-Z0-9-]+)'", content)
    count = 0
    ids = sorted(list(set([i for i in ids if "-" in i])))
    
    for sid in ids:
        start_idx = content.find(f"id: '{sid}'")
        if start_idx == -1: continue
        obj_start = content.rfind("{", 0, start_idx)
        obj_text = get_bracket_content(content, obj_start)
        if not obj_text: continue
        
        topic = extract_field(r"topic:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        diff_code = extract_field(r"difficulty:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        audio = extract_field(r"audioFile:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        q_text = extract_field(r"question:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        correct = extract_field(r"correct:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        expl = extract_field(r"explanation:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        
        s1 = extract_field(r"speaker1:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        s2 = extract_field(r"speaker2:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        
        opts_match = re.search(r"options:\s*\[(.*?)\]", obj_text, re.DOTALL)
        opts = []
        if opts_match:
            opts_raw = opts_match.group(1)
            opts = [om.group(1).replace("\\'", "'") for om in re.finditer(r"text:\s*'((?:[^'\\]|\\.)*)'", opts_raw)]
        
        prompt_content = {
            "title": f"Response: {topic} ({sid})",
            "topic": topic,
            "dialogue": [s1, s2],
            "audio_url": audio,
            "questions": [{
                "question": q_text,
                "options": opts,
                "correct_answer": ord(correct) - ord('A'),
                "explanation": expl
            }]
        }
        
        level_map = {"E": "A2", "M": "B2", "H": "C1"}
        cursor.execute("""
            INSERT INTO test_items (id, section, task_type, target_level, irt_difficulty, irt_discrimination, prompt_content, source_file, source_id, is_active, version, exposure_count, generated_by_model, media_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), "LISTENING", "LISTEN_CHOOSE_RESPONSE", level_map.get(diff_code, "B2"), 0.0, 1.0, json.dumps(prompt_content), "toefl-listening-choose-response-practice.html", sid, True, 1, 0, 'Legacy', audio))
        count += 1
    print(f"Imported {count} LISTEN_CHOOSE_RESPONSE items.")

def import_academic_talks(cursor):
    path = os.path.join(LEGACY_PATH, "toefl-listening-academic-talk-practice.html")
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()
    
    ids = re.findall(r"id:\s*'([A-Z0-9-]+)'", content)
    ids = sorted(list(set([i for i in ids if "-" in i])))
    count = 0
    for sid in ids:
        start_idx = content.find(f"id: '{sid}'")
        if start_idx == -1: continue
        obj_start = content.rfind("{", 0, start_idx)
        obj_text = get_bracket_content(content, obj_start)
        if not obj_text: continue
        
        title = extract_field(r"title:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        context = extract_field(r"context:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        audio = extract_field(r"audioFile:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        text = extract_field(r"text:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        
        questions = []
        # Find all question objects
        q_matches = re.finditer(r"{\s*id:\s*'Q", obj_text)
        for qm in q_matches:
            q_block = get_bracket_content(obj_text, qm.start())
            if not q_block: continue
            
            qtxt = extract_field(r"text:\s*'((?:[^'\\]|\\.)*)'", q_block)
            qcorr = extract_field(r"correct:\s*'((?:[^'\\]|\\.)*)'", q_block)
            qexpl = extract_field(r"explanation:\s*'((?:[^'\\]|\\.)*)'", q_block)
            
            opts_match = re.search(r"options:\s*\[(.*?)\]", q_block, re.DOTALL)
            q_opts = []
            if opts_match:
                q_opts = [om.group(1).replace("\\'", "'") for om in re.finditer(r"text:\s*'((?:[^'\\]|\\.)*)'", opts_match.group(1))]
            
            questions.append({"question": qtxt, "options": q_opts, "correct_answer": ord(qcorr) - ord('A'), "explanation": qexpl})
            
        prompt_content = {"title": title, "context": context, "text": text, "audio_url": audio, "questions": questions}
        cursor.execute("""
            INSERT INTO test_items (id, section, task_type, target_level, irt_difficulty, irt_discrimination, prompt_content, source_file, source_id, is_active, version, exposure_count, generated_by_model, media_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), "LISTENING", "LISTEN_ACADEMIC_TALK", "B2", 0.0, 1.0, json.dumps(prompt_content), "toefl-listening-academic-talk-practice.html", sid, True, 1, 0, 'Legacy', audio))
        count += 1
    print(f"Imported {count} LISTEN_ACADEMIC_TALK items.")

def import_announcements(cursor):
    path = os.path.join(LEGACY_PATH, "toefl-listening-announcement-practice.html")
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()
    
    ids = re.findall(r"id:\s*'([A-Z0-9-]+)'", content)
    ids = sorted(list(set([i for i in ids if "-" in i])))
    count = 0
    for sid in ids:
        start_idx = content.find(f"id: '{sid}'")
        if start_idx == -1: continue
        obj_start = content.rfind("{", 0, start_idx)
        obj_text = get_bracket_content(content, obj_start)
        if not obj_text: continue
        
        title = extract_field(r"title:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        context = extract_field(r"context:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        audio = extract_field(r"audioFile:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        text = extract_field(r"text:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        
        questions = []
        q_matches = re.finditer(r"{\s*id:\s*'Q", obj_text)
        for qm in q_matches:
            q_block = get_bracket_content(obj_text, qm.start())
            if not q_block: continue
            
            qtxt = extract_field(r"text:\s*'((?:[^'\\]|\\.)*)'", q_block)
            qcorr = extract_field(r"correct:\s*'((?:[^'\\]|\\.)*)'", q_block)
            qexpl = extract_field(r"explanation:\s*'((?:[^'\\]|\\.)*)'", q_block)
            
            opts_match = re.search(r"options:\s*\[(.*?)\]", q_block, re.DOTALL)
            q_opts = []
            if opts_match:
                q_opts = [om.group(1).replace("\\'", "'") for om in re.finditer(r"text:\s*'((?:[^'\\]|\\.)*)'", opts_match.group(1))]
            
            questions.append({"question": qtxt, "options": q_opts, "correct_answer": ord(qcorr) - ord('A'), "explanation": qexpl})
            
        prompt_content = {"title": title, "context": context, "text": text, "audio_url": audio, "questions": questions}
        cursor.execute("""
            INSERT INTO test_items (id, section, task_type, target_level, irt_difficulty, irt_discrimination, prompt_content, source_file, source_id, is_active, version, exposure_count, generated_by_model, media_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), "LISTENING", "LISTEN_ANNOUNCEMENT", "B2", 0.0, 1.0, json.dumps(prompt_content), "toefl-listening-announcement-practice.html", sid, True, 1, 0, 'Legacy', audio))
        count += 1
    print(f"Imported {count} LISTEN_ANNOUNCEMENT items.")

def import_conversations(cursor):
    path = os.path.join(LEGACY_PATH, "toefl-listening-conversation-practice.html")
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()
    
    ids = re.findall(r"id:\s*'([A-Z0-9-]+)'", content)
    ids = sorted(list(set([i for i in ids if "-" in i])))
    count = 0
    for sid in ids:
        start_idx = content.find(f"id: '{sid}'")
        if start_idx == -1: continue
        obj_start = content.rfind("{", 0, start_idx)
        obj_text = get_bracket_content(content, obj_start)
        if not obj_text: continue
        
        title = extract_field(r"title:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        topic = extract_field(r"topic:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        audio = extract_field(r"audioFile:\s*'((?:[^'\\]|\\.)*)'", obj_text)
        
        script_match = re.search(r"script:\s*{(.*?)}", obj_text, re.DOTALL)
        script_text = ""
        if script_match:
            script_raw = script_match.group(1)
            turns = re.findall(r"(\w+):\s*'((?:[^'\\]|\\.)*)'", script_raw)
            script_lines = []
            for speaker, text in turns:
                clean_text = text.replace("\\'", "'")
                script_lines.append(f"**{speaker.capitalize()}:** {clean_text}")
            script_text = "\n\n".join(script_lines)
        
        questions = []
        q_matches = re.finditer(r"{\s*id:\s*'Q", obj_text)
        for qm in q_matches:
            q_block = get_bracket_content(obj_text, qm.start())
            if not q_block: continue
            
            qtxt = extract_field(r"text:\s*'((?:[^'\\]|\\.)*)'", q_block)
            qcorr = extract_field(r"correct:\s*'((?:[^'\\]|\\.)*)'", q_block)
            qexpl = extract_field(r"explanation:\s*'((?:[^'\\]|\\.)*)'", q_block)
            
            opts_match = re.search(r"options:\s*\[(.*?)\]", q_block, re.DOTALL)
            q_opts = []
            if opts_match:
                q_opts = [om.group(1).replace("\\'", "'") for om in re.finditer(r"text:\s*'((?:[^'\\]|\\.)*)'", opts_match.group(1))]
            
            correct_val = [ord(c) - ord('A') for c in qcorr] if len(qcorr) > 1 else ord(qcorr) - ord('A')
            questions.append({"question": qtxt, "options": q_opts, "correct_answer": correct_val, "explanation": qexpl})
            
        prompt_content = {"title": title, "topic": topic, "text": script_text, "audio_url": audio, "questions": questions}
        cursor.execute("""
            INSERT INTO test_items (id, section, task_type, target_level, irt_difficulty, irt_discrimination, prompt_content, source_file, source_id, is_active, version, exposure_count, generated_by_model, media_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), "LISTENING", "LISTEN_CONVERSATION", "B2", 0.0, 1.0, json.dumps(prompt_content), "toefl-listening-conversation-practice.html", sid, True, 1, 0, 'Legacy', audio))
        count += 1
    print(f"Imported {count} LISTEN_CONVERSATION items.")

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    purge_legacy(cursor)
    import_listen_and_repeat(cursor)
    import_listen_choose_response(cursor)
    import_academic_talks(cursor)
    import_announcements(cursor)
    import_conversations(cursor)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
