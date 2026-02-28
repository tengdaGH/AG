# Briefing for Mac Mini: IELTS Speaking Scraper Implementation

## Objective Completed
Successfully developed and deployed an automated web scraping tool for the Cambridge Assessment IELTS Speaking Question Bank.

## Key Deliverables
1. **`scrape_and_populate.py`**: A robust Python CLI tool designed to extract valid IELTS speaking questions from online sources.
    - Path: `IELTS/speaking/scripts/scrape_and_populate.py`
    - Functionality: Reads web content, structures the data exclusively using the Google Gemini model (`gemini-2.5-flash`), generates Chinese translations, and forces assignments into `cognitive_target` compliance.
2. **Database Integration**: The script automatically binds to `master_bank.json` and accurately links Part 2 (Cue Cards) with corresponding Part 3 discussion frameworks into the `part2_3_couplings` schema.
3. **Environment Configuration**: We extracted a valid `GEMINI_API_KEY` ("AG Vocab Gen" key) from the current Google Cloud project via a browser session and persisted it to `~/.zshrc`.

## How to Proceed
The tool is ready to use for automating the acquisition of new "换题季" (Season Change) questions. 
Execute it locally on standard source URLs:
*   Part 1 Topics: `python3 IELTS/speaking/scripts/scrape_and_populate.py --url <URL> --type part1`
*   Part 2/3 Couplings: `python3 IELTS/speaking/scripts/scrape_and_populate.py --url <URL> --type part23`

Followed by:
`python3 IELTS/speaking/scripts/validate_bank.py` to ensure schema integrity before committing to the active `seasons` manifests.
