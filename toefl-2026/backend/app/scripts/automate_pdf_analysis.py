#!/usr/bin/env python3
"""
automate_pdf_analysis.py - Batch processes the TOEFL PDF using Gemini Vision.
Slices the PDF into sections, renders pages, and generates markdown reports.
"""
import sys
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Optional: if you have the new SDK it's usually `google-genai` pip package
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Please install google-genai: pip install google-genai")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parents[3]
PDF_PATH = BASE_DIR / "2026新托福Pack-6.pdf"
RENDER_SCRIPT = BASE_DIR / "backend" / "app" / "scripts" / "render_pdf_pages.py"
OUT_DIR = BASE_DIR / "pdf_pages"
LOG_DIR = BASE_DIR / "logs"

# Ensure the .env file is loaded (assuming it's in the backend directory)
load_dotenv(BASE_DIR / "backend" / ".env")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in environment.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

BATCHES = {
    "Reading": {"start": 1, "end": 20},
    "Listening": {"start": 21, "end": 70},
    "Writing": {"start": 71, "end": 91},
    "Speaking": {"start": 92, "end": 109}
}

PROMPT_TEMPLATE = """
You are an expert UX/UI designer and educational testing consultant.
Analyze the following sequential screenshots from the TOEFL 2026 {section} section.

Please provide a detailed Markdown report covering:
1. **Visual UI DNA**: Color palettes, typography, layout structures (split-screen vs single-screen).
2. **Interaction Mechanics**: What components are visible (radio buttons, text areas, timers, progress bars)? How do users interact with them?
3. **Test Flow**: Document the step-by-step journey the user takes from page to page. Include any instruction screens, question types, and transitions.

Be as precise as possible, noting the specific phrasing of buttons (e.g., "Begin >", "Next", "Back") and their locations.
"""

def render_batch(start: int, end: int):
    """Uses render_pdf_pages.py to render the required pages."""
    print(f"  Rendering pages {start} to {end}...")
    subprocess.run([sys.executable, str(RENDER_SCRIPT), str(PDF_PATH), str(start), str(end)], check=True)

def analyze_batch(section: str, start: int, end: int):
    """Sends the rendered images to Gemini and saves the results."""
    print(f"\n[{section}] Starting analysis (Pages {start}-{end})...")
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"{section.lower()}_analysis.md"
    
    # 1. Ensure images exist
    render_batch(start, end)
    
    # 2. Collect images
    image_paths = []
    for i in range(start, end + 1):
        p = OUT_DIR / f"2026新托福Pack-6_p{i:03d}.png"
        if p.exists():
            image_paths.append(p)
            
    if not image_paths:
        print(f"  Error: No images found for {section}.")
        return

    print(f"  Uploading {len(image_paths)} images to Gemini...")
    
    # Upload files using the GenAI client
    import shutil
    uploaded_files = []
    for path in image_paths:
        # Workaround for SDK Unicode bug in headers
        safe_path = OUT_DIR / f"temp_{str(path.name)[-7:]}"
        shutil.copy(path, safe_path)
        f = client.files.upload(file=str(safe_path))
        uploaded_files.append(f)
        safe_path.unlink()
        
    print(f"  Images uploaded. Generating analysis...")
    
    prompt = PROMPT_TEMPLATE.format(section=section)
    contents = [prompt] + uploaded_files
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=contents,
        )
        
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(response.text)
            
        print(f"  [SUCCESS] Analysis saved to {log_file}")
            
    except Exception as e:
        print(f"  [ERROR] Gemini API call failed: {e}")
    finally:
        # Cleanup uploaded files from the server
        for f in uploaded_files:
            client.files.delete(name=f.name)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Automate TOEFL PDF Analysis")
    parser.add_argument("--section", type=str, choices=list(BATCHES.keys()) + ["All"], default="All", help="Specific section to run")
    args = parser.parse_args()
    
    if args.section == "All":
        sections_to_run = BATCHES
    else:
        sections_to_run = {args.section: BATCHES[args.section]}
        
    for section, bounds in sections_to_run.items():
        analyze_batch(section, bounds["start"], bounds["end"])
        
    print("\nBatch analysis complete!")

if __name__ == "__main__":
    main()
