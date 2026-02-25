#!/usr/bin/env python3
"""
render_pdf_pages.py – Render PDF pages to PNG images for visual OCR.
Renders specified page ranges from a PDF to individual PNG files.

Usage:
    python render_pdf_pages.py <pdf_path> <start_page> <end_page> [--dpi 200]
"""
import sys
import pymupdf
from pathlib import Path

def render_pages(pdf_path: str, start: int, end: int, dpi: int = 200):
    out_dir = Path("/Users/tengda/Antigravity/toefl-2026/pdf_pages")
    out_dir.mkdir(exist_ok=True)
    
    doc = pymupdf.open(pdf_path)
    pdf_name = Path(pdf_path).stem
    
    zoom = dpi / 72  # 72 is default DPI
    mat = pymupdf.Matrix(zoom, zoom)
    
    for i in range(start - 1, min(end, doc.page_count)):
        page = doc[i]
        pix = page.get_pixmap(matrix=mat)
        out_file = out_dir / f"{pdf_name}_p{i+1:03d}.png"
        pix.save(str(out_file))
        print(f"Saved: {out_file} ({pix.width}x{pix.height})")
    
    doc.close()
    print(f"\nDone. {end - start + 1} pages rendered to {out_dir}")

if __name__ == "__main__":
    pdf = sys.argv[1]
    start = int(sys.argv[2])
    end = int(sys.argv[3])
    dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 200
    render_pages(pdf, start, end, dpi)
