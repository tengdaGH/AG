# ============================================================
# Purpose:       Debug utility to inspect folder structure of Writing for Academic Discussion source images.
# Usage:         python backend/scripts/wad_ingestion/investigate_folders.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import sys

def check_folders():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Writing for academic discussions"))
    
    # Check "Requiring Volunteer Work for Graduation" as an example flagged item
    folder_path = os.path.join(base_dir, "Requiring Volunteer Work for Graduation")
    print(f"Checking {folder_path}...")
    
    if os.path.exists(folder_path):
        files = os.listdir(folder_path)
        print("Files:")
        for f in files:
            print("  -", f)
    else:
        print("Folder not found.")

if __name__ == "__main__":
    check_folders()
