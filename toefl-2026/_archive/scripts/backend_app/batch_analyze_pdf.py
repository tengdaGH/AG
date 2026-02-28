#!/usr/bin/env python3
"""
batch_analyze_pdf.py - Helper to render and list a specific range of PDF pages.
Prevents "Agent Loading" failure by keeping context thin.
"""
import sys
import os
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
PDF_PATH = BASE_DIR / "2026新托福Pack-6.pdf"
RENDER_SCRIPT = BASE_DIR / "backend" / "app" / "scripts" / "render_pdf_pages.py"
OUT_DIR = BASE_DIR / "pdf_pages"

def main():
    if len(sys.argv) < 3:
        print("Usage: python batch_analyze_pdf.py <start_page> <end_page>")
        sys.exit(1)
        
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    
    print(f"=== Batch Analysis: Pages {start} to {end} ===")
    
    # Check if rendering is needed
    missing = []
    for i in range(start, end + 1):
        p_path = OUT_DIR / f"2026新托福Pack-6_p{i:03d}.png"
        if not p_path.exists():
            missing.append(i)
            
    if missing:
        print(f"Rendering missing pages: {missing}")
        # For simplicity, we just render the whole requested range if any are missing
        subprocess.run([sys.executable, str(RENDER_SCRIPT), str(PDF_PATH), str(start), str(end)], check=True)
    else:
        print("All pages already rendered.")
        
    print("\nAvailable images for this batch:")
    for i in range(start, end + 1):
        p_path = OUT_DIR / f"2026新托福Pack-6_p{i:03d}.png"
        if p_path.exists():
            print(f"- [Page {i}]({p_path.as_uri()})")

if __name__ == "__main__":
    main()
