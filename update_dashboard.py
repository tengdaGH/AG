#!/usr/bin/env python3
import os
import subprocess
import json
import re
from datetime import datetime
from dotenv import load_dotenv

# --- Configuration ---
WORKSPACE_DIR = "/Users/tengda/Antigravity"
OUTPUT_FILE = os.path.join(WORKSPACE_DIR, "docs", "dashboard.html")
BACKLOG_FILE = os.path.join(WORKSPACE_DIR, "BACKLOG.md")

# Load environment variables for API key
load_dotenv(os.path.join(WORKSPACE_DIR, "IELTS", ".env"))
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY")

# Project definitions for tracking git activity
PROJECTS = {
    "toefl-2026": {"name": "TOEFL 2026 平台", "icon": "🎓", "category": "教育产品", "status": "运行中", "color": "green", "paths": ["toefl-2026/"]},
    "IELTS": {"name": "雅思机考题库", "icon": "📖", "category": "教育产品", "status": "批处理中", "color": "terracotta", "paths": ["IELTS/"]},
    "audio": {"name": "TTS 音频合成工具链", "icon": "🎙️", "category": "教育产品", "status": "基本完成", "color": "green", "paths": ["toefl-2026/audio/", "toefl-2026/agents/scripts/generate_ets_audio.py"]},
    "calendar_integration": {"name": "教务自动日历排表", "icon": "📅", "category": "运维工具链", "status": "维护中", "color": "mid-gray", "paths": ["calendar_integration/"]},
    "Notion Pal": {"name": "学生及成绩管家", "icon": "🤖", "category": "运维工具链", "status": "就绪", "color": "blue", "paths": ["Notion Pal/"]},
    "themes-and-designs": {"name": "产品视效标准提取", "icon": "🎨", "category": "基础规范研究", "status": "参考库", "color": "blue", "paths": ["themes-and-designs/"]}
}

# --- Data Collection ---

def get_git_activity():
    """Returns a dict of project keys to a list of recent commit messages and the last commit date."""
    activity = {}
    for key, proj in PROJECTS.items():
        # Get last 3 commits for the paths related to this project
        path_args = [os.path.join(WORKSPACE_DIR, p) for p in proj['paths']]
        try:
            cmd = ["git", "log", "-n", "3", "--format=%cd|%s", "--date=short", "--"] + path_args
            result = subprocess.run(cmd, cwd=WORKSPACE_DIR, capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            
            commits = []
            last_date = "N/A"
            if lines and lines[0]:
                raw_commits = []
                for line in lines:
                    if '|' in line:
                        date, msg = line.split('|', 1)
                        if last_date == "N/A":
                            last_date = date
                        raw_commits.append(msg)
                
                # Use Minimax to translate and summarize the raw commits
                commits = translate_commits(raw_commits) if raw_commits else []

            activity[key] = {
                "last_date": last_date,
                "commits": commits,
                "commit_count": len(commits)
            }
        except subprocess.CalledProcessError:
            activity[key] = {"last_date": "N/A", "commits": [], "commit_count": 0}
            
    return activity

def translate_commits(raw_commits):
    """Uses the Minimax API via curl subprocess to translate and summarize technical commits into formal English."""
    if not MINIMAX_API_KEY:
        return raw_commits # Fallback if no key

    commits_text = "\\n".join(f"- {c}" for c in raw_commits)
    prompt = f"Please translate and rewrite these technical git commit messages into clear, formal, and professional English sentences. Do not use bullet points or dashes, just give me a single short paragraph summarizing the progress (max 2 sentences):\\n\\n{commits_text}"
    
    payload = {
        "model": "MiniMax-Text-01",
        "messages": [
            {"role": "system", "content": "You are a senior project manager summarizing technical work."},
            {"role": "user", "content": prompt}
        ]
    }
    
    # Use curl via subprocess to bypass macOS proxy issues as documented in IELTS/HANDOFF.md
    cmd = [
        "curl", "-s", "-m", "15",
        "-X", "POST", "https://api.minimaxi.chat/v1/text/chatcompletion_v2",
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {MINIMAX_API_KEY}",
        "-d", json.dumps(payload)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        resp_json = json.loads(result.stdout)
        translated = resp_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        # Return as a single item list for the UI
        return [translated] if translated else raw_commits
    except Exception as e:
        print(f"LLM Translation failed: {e}")
        return raw_commits

def determine_active_focus(activity):
    """Find the project with the most recent commits (heuristic for active focus)."""
    most_recent = None
    latest_date_str = "1970-01-01"
    
    for key, data in activity.items():
        if data["last_date"] != "N/A" and data["last_date"] > latest_date_str:
            latest_date_str = data["last_date"]
            most_recent = key
            
    return most_recent

def parse_backlog():
    """Parses BACKLOG.md to extract TODO items."""
    todos = []
    if not os.path.exists(BACKLOG_FILE):
        return todos
        
    with open(BACKLOG_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('- [ ]'):
            text = line.replace('- [ ]', '').strip()
            # Remove bolding marks for cleaner display
            text = text.replace('**', '')
            todos.append({"status": "pending", "text": text})
        elif line.startswith('- [x]'):
            text = line.replace('- [x]', '').strip()
            text = text.replace('**', '')
            todos.append({"status": "done", "text": text})
            
    # Limit to top 6 items to not clutter UI
    return todos[:8]

# --- HTML Generation ---

def generate_html(activity, active_key, backlog_todos):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Static CSS based on Anthropic DNA
    css = """
        :root {
            /* Anthropic DNA Palette */
            --bg-cream: #faf9f5;
            --text-dark: #141413;
            --mid-gray: #b0aea5;
            --light-gray: #e8e6dc;
            
            /* Accents */
            --terracotta: #d97757;
            --dusty-blue: #6a9bcc;
            --sage-green: #788c5d;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Lora', Georgia, serif; /* Primary Anthropic readable font */
        }

        body {
            background-color: var(--bg-cream);
            color: var(--text-dark);
            min-height: 100vh;
            padding: 64px 24px;
            line-height: 1.6;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            width: 100%;
        }

        h1, h2, h3, .nav-brand {
            font-family: 'Poppins', Arial, sans-serif;
            font-weight: 500;
        }

        header {
            margin-bottom: 64px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .brand {
            font-size: 0.875rem;
            color: var(--mid-gray);
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 24px;
        }

        h1 {
            font-size: 3rem;
            letter-spacing: -0.03em;
            line-height: 1.1;
            color: var(--text-dark);
        }

        .subtitle {
            font-size: 1.25rem;
            color: var(--mid-gray);
            max-width: 600px;
        }
        
        .meta-info {
            font-size: 0.875rem;
            color: var(--mid-gray);
            margin-top: 16px;
            font-family: monospace;
        }

        .section-title {
            font-size: 1.5rem;
            margin: 56px 0 24px 0;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--light-gray);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
            gap: 24px;
        }

        /* Essentialist Card Design */
        .card {
            background: #ffffff;
            border: 1px solid var(--light-gray);
            border-radius: 8px;
            padding: 32px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            display: flex;
            flex-direction: column;
            gap: 16px;
            position: relative;
        }

        .card:hover {
            box-shadow: 0 12px 24px rgba(20, 20, 19, 0.04);
            transform: translateY(-2px);
        }
        
        /* Active Focus Ring (Subtle) */
        .card.active-focus {
            border-color: var(--dusty-blue);
        }
        .card.active-focus::after {
            content: 'Current Focus';
            position: absolute;
            top: 24px;
            right: 32px;
            font-family: 'Poppins', sans-serif;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--dusty-blue);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .card-icon {
            font-size: 1.5rem;
        }

        .card-title {
            font-size: 1.25rem;
            font-family: 'Poppins', sans-serif;
        }

        /* Minimal Status Tags */
        .status-tag {
            font-family: 'Poppins', sans-serif;
            font-size: 0.75rem;
            padding: 4px 10px;
            border-radius: 4px;
            background: var(--light-gray);
            color: var(--text-dark);
            display: inline-block;
            margin-bottom: 8px;
        }
        
        .status-tag.terracotta { color: var(--terracotta); background: rgba(217, 119, 87, 0.1); }
        .status-tag.green { color: var(--sage-green); background: rgba(120, 140, 93, 0.1); }
        .status-tag.blue { color: var(--dusty-blue); background: rgba(106, 155, 204, 0.1); }
        .status-tag.mid-gray { color: var(--mid-gray); background: var(--bg-cream); border: 1px solid var(--light-gray); }

        .commit-list {
            margin-top: 16px;
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .commit-item {
            font-family: monospace;
            font-size: 0.85rem;
            color: var(--mid-gray);
            display: flex;
            gap: 8px;
        }
        
        .commit-item::before {
            content: '→';
            color: var(--light-gray);
        }

        .last-updated {
            margin-top: auto;
            padding-top: 16px;
            font-size: 0.85rem;
            color: var(--mid-gray);
            border-top: 1px dashed var(--light-gray);
        }

        /* Backlog Section */
        .backlog-container {
            margin-top: 64px;
            background: #ffffff;
            border: 1px solid var(--light-gray);
            border-radius: 8px;
            padding: 40px;
        }

        .todo-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 16px;
            margin-top: 24px;
        }

        .todo-item {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            font-size: 1rem;
        }

        .todo-status {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border: 2px solid var(--light-gray);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            margin-top: 4px;
        }

        .todo-item.done .todo-status {
            border-color: var(--sage-green);
            background: var(--sage-green);
        }

        .todo-item.done .todo-status::after {
            content: '✓';
            color: white;
            font-size: 0.75rem;
            font-family: sans-serif;
        }

        .todo-item.done .todo-text {
            color: var(--mid-gray);
            text-decoration: line-through;
        }
        
        @media (max-width: 768px) {
            body { padding: 32px 16px; }
            h1 { font-size: 2.25rem; }
            .grid { grid-template-columns: 1fr; }
            .card { padding: 24px; }
        }

        /* Float Update Button */
        .update-btn {
            position: fixed;
            top: 32px;
            right: 32px;
            background: var(--text-dark);
            color: var(--bg-cream);
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-family: 'Poppins', sans-serif;
            font-size: 0.85rem;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            z-index: 100;
        }

        .update-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.15);
            background: #2a2a29;
        }

        .update-btn:active {
            transform: translateY(0);
        }

        .update-btn.loading {
            opacity: 0.7;
            pointer-events: none;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .spinner {
            width: 14px;
            height: 14px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: #fff;
            border-radius: 50%;
            display: none;
        }

        .update-btn.loading .spinner {
            display: block;
            animation: spin 1s linear infinite;
        }
    """
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Workspace DNA | Antigravity</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&family=Lora:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
    <style>{css}</style>
</head>
<body>
    <button class="update-btn" id="update-btn" onclick="triggerUpdate()">
        <span class="spinner"></span>
        <span class="btn-text">Update Latest State</span>
    </button>

    <div class="container">
        <header>
            <div class="brand">Antigravity Systems</div>
            <h1>Workspace Intelligence.</h1>
            <p class="subtitle">A continuously updating map of your current cognitive load and project states, designed for clarity.</p>
            <div class="meta-info">Last generated: {now_str} via update_dashboard.py &bull; Minimax LLM active</div>
        </header>

        <h2 class="section-title">Active Workstreams</h2>
        <div class="grid">
"""
    
    # Render Project Cards
    for key, proj in PROJECTS.items():
        act = activity.get(key, {"last_date": "N/A", "commits": []})
        is_active = "active-focus" if key == active_key else ""
        
        commits_html = ""
        if act["commits"]:
            commits_html = '<ul class="commit-list">'
            for c in act["commits"]:
                # Display full translated message (no truncation)
                commits_html += f'<li class="commit-item">{c}</li>'
            commits_html += '</ul>'
        else:
            commits_html = '<p style="font-size:0.85rem; color:var(--mid-gray); margin-top:16px;">No recent git activity detected.</p>'
            
        html += f"""
            <div class="card {is_active}">
                <div>
                    <span class="status-tag {proj['color']}">{proj['status']}</span>
                </div>
                <div class="card-header">
                    <span class="card-icon">{proj['icon']}</span>
                    <h3 class="card-title">{proj['name']}</h3>
                </div>
                {commits_html}
                <div class="last-updated">Latest node: {act['last_date']}</div>
            </div>
"""

    html += """
        </div>

        <div class="backlog-container">
            <h2 style="font-family:'Poppins', sans-serif; margin-bottom: 8px;">Pending Operations</h2>
            <p style="color:var(--mid-gray); font-size:0.9rem;">Extracted directly from BACKLOG.md</p>
            
            <ul class="todo-list">
"""

    # Render Backlog
    if not backlog_todos:
        html += '<li class="todo-item"><div class="todo-text">No active items in BACKLOG.md</div></li>'
    else:
        for todo in backlog_todos:
            status_cls = "done" if todo["status"] == "done" else "pending"
            html += f"""
                <li class="todo-item {status_cls}">
                    <div class="todo-status"></div>
                    <div class="todo-text">{todo["text"]}</div>
                </li>
"""

    html += """
            </ul>
        </div>
    </div>
    
    <script>
        function triggerUpdate() {
            const btn = document.getElementById('update-btn');
            const btnText = btn.querySelector('.btn-text');
            
            btn.classList.add('loading');
            btnText.textContent = 'Translating Logs...';
            
            fetch('http://localhost:8010/api/update', {
                method: 'POST',
            })
            .then(response => {
                if(response.ok) {
                    btnText.textContent = 'Success! Reloading...';
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    btn.classList.remove('loading');
                    btnText.textContent = 'Update Failed';
                    setTimeout(() => btnText.textContent = 'Update Latest State', 3000);
                }
            })
            .catch(error => {
                btn.classList.remove('loading');
                btnText.textContent = 'Server Offline (localhost:8010)';
                setTimeout(() => btnText.textContent = 'Update Latest State', 3000);
                console.error('Update UI error:', error);
            });
        }
    </script>
</body>
</html>
"""
    return html

def main():
    print("Gathering git activity from workspace...")
    activity = get_git_activity()
    active_key = determine_active_focus(activity)
    
    print("Parsing BACKLOG.md for current global TODOs...")
    backlog_todos = parse_backlog()
    
    print("Generating HTML payload via Anthropic Design DNA...")
    html = generate_html(activity, active_key, backlog_todos)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print(f"Success! Dashboard updated at: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
