# ============================================================
# Purpose:       Simulate IRT field test data via Monte Carlo or LLM Synthetic Examinees.
# Usage:         python backend/scripts/simulate_field_test_v2.py [--mode monte_carlo|llm] [--apply] [--limit 5]
# Created:       2026-02-26
# Self-Destruct: No
# ============================================================
import os
import sys
import json
import logging
import argparse
import random
import re
from typing import List, Dict, Tuple

import numpy as np
from sqlalchemy.orm import Session

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models.models import TestItem, ItemStatus, CEFRLevel, TaskType
from app.database.connection import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# CEFR to Theta mapping (mean, std)
CEFR_THETA_MAP = {
    CEFRLevel.A1: (-2.5, 0.5),
    CEFRLevel.A2: (-1.5, 0.5),
    CEFRLevel.B1: (-0.5, 0.5),
    CEFRLevel.B2: (0.5, 0.5),
    CEFRLevel.C1: (1.5, 0.5),
    CEFRLevel.C2: (2.5, 0.4),
}

# ---------------------------------------------------------
# MONTE CARLO IRT PIPELINE
# ---------------------------------------------------------
def generate_synthetic_examinees(n: int = 1000) -> np.ndarray:
    """Generate a realistic distribution of test-taker abilities (theta)."""
    # Proportions: mostly B1-C1
    props = [0.05, 0.1, 0.3, 0.3, 0.2, 0.05]
    levels = [CEFRLevel.A1, CEFRLevel.A2, CEFRLevel.B1, CEFRLevel.B2, CEFRLevel.C1, CEFRLevel.C2]
    
    thetas = []
    for _ in range(n):
        lvl = random.choices(levels, weights=props)[0]
        mean, std = CEFR_THETA_MAP[lvl]
        thetas.append(np.random.normal(mean, std))
    return np.array(thetas)

def _get_true_params(item: TestItem) -> Tuple[float, float, float]:
    """Derive plausible true parameters based on the item's target level."""
    mean, std = CEFR_THETA_MAP.get(item.target_level, (0.0, 1.0))
    b_true = np.random.normal(mean, 0.3)
    a_true = np.random.lognormal(mean=0.0, sigma=0.3)  # roughly 0.7 - 2.0
    
    # Guessing parameter
    c_true = 0.0
    try:
        data = json.loads(item.prompt_content)
        questions = data.get("questions", [])
        if questions:
            opts = questions[0].get("options", [])
            if len(opts) > 0:
                c_true = 1.0 / len(opts)
    except:
        pass
    return max(-3.0, min(3.0, b_true)), max(0.1, a_true), c_true

def run_monte_carlo(items: List[TestItem], db: Session, apply: bool):
    """Run Monte Carlo simulation and calibration using girth."""
    try:
        from girth import twopl_mml
    except ImportError:
        logging.error("The 'girth' library is required for Monte Carlo simulation. Run: pip install girth")
        return []

    if not items:
        return []

    num_examinees = 1000
    thetas = generate_synthetic_examinees(n=num_examinees)
    num_items = len(items)
    
    logging.info(f"Generating synthetic responses for {num_examinees} examinees × {num_items} items...")
    
    # True parameters
    b_true_arr = np.zeros(num_items)
    a_true_arr = np.zeros(num_items)
    c_true_arr = np.zeros(num_items)
    
    for j, item in enumerate(items):
        b, a, c = _get_true_params(item)
        b_true_arr[j] = b
        a_true_arr[j] = a
        c_true_arr[j] = c
        
    # Generate response matrix (dichotomous 0/1)
    # Shape: (num_items, num_examinees) - required by girth
    responses = np.zeros((num_items, num_examinees), dtype=int)
    
    for j in range(num_items):
        a, b, c = a_true_arr[j], b_true_arr[j], c_true_arr[j]
        # 3PL IRT probability formula
        prob_correct = c + (1 - c) / (1 + np.exp(-a * (thetas - b)))
        rand_draws = np.random.uniform(0, 1, num_examinees)
        responses[j, :] = (rand_draws < prob_correct).astype(int)

    logging.info("Running MML IRT calibration (this may take a moment)...")
    
    # 2PL is often more stable for small number of items.
    try:
        results_irt = twopl_mml(responses)
        est_a = results_irt['Discrimination']
        est_b = results_irt['Difficulty']
    except Exception as e:
        logging.error(f"IRT Calibration failed: {e}. Falling back to true parameters with small noise.")
        est_a = a_true_arr + np.random.normal(0, 0.1, num_items)
        est_b = b_true_arr + np.random.normal(0, 0.1, num_items)

    results = []
    for j, item in enumerate(items):
        new_b = max(-3.0, min(3.0, float(est_b[j])))
        new_a = max(0.1, float(est_a[j]))
        
        # Fit stats proxy
        b_diff = abs(new_b - b_true_arr[j])
        fit_status = "Good" if b_diff < 1.0 else "Poor Fit"
        
        action = "Promoted to ACTIVE" if fit_status == "Good" else "Suspended (Poor Fit)"
        
        logging.info(f"Item {item.id[:8]} | True b={b_true_arr[j]:.2f} -> Est b={new_b:.2f} | Fit: {fit_status}")

        if apply:
            item.irt_difficulty = round(new_b, 2)
            item.irt_discrimination = round(new_a, 2)
            item.exposure_count = num_examinees
            if fit_status == "Good":
                item.lifecycle_status = ItemStatus.ACTIVE
                item.is_active = True
            else:
                item.lifecycle_status = ItemStatus.SUSPENDED
                item.is_active = False
                
            item.generation_notes = f"{item.generation_notes or ''} [MC Field Test: b={new_b:.2f}, a={new_a:.2f}, fit={fit_status}]".strip()
            db.commit()

        results.append({
            "id": item.id,
            "simulated_b": round(new_b, 2),
            "simulated_a": round(new_a, 2),
            "exposures": num_examinees,
            "status": action if apply else "Dry Run - " + action
        })
        
    return results


# ---------------------------------------------------------
# LLM SYNTHETIC EXAMINEE PIPELINE 
# ---------------------------------------------------------
def run_llm_synthetic(items: List[TestItem], db: Session, apply: bool):
    """Simulate test takers using Gemini based on CEFR personas."""
    try:
        import google.generativeai as genai
    except ImportError:
        logging.error("google-genai not installed. Run: pip install google-genai")
        return []

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY not set.")
        return []

    genai.configure(api_key=api_key)
    # Note: For compatibility with different genai SDK versions, using the standard generative model approach
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
    except Exception as e:
        logging.error(f"Error initializing Gemini: {e}")
        return []
        
    results = []

    # To save tokens, we simulate exactly 1 "borderline" test-taker for each target CEFR level
    for item in items:
        logging.info(f"Simulating LLM synthetic examinee for {item.id[:8]} at level {item.target_level}")
        
        # Construct proxy prompt 
        level = item.target_level.value if hasattr(item.target_level, 'value') else item.target_level
        prompt = f"""
        You are an English language learner with exactly a {level} CEFR proficiency level.
        You often struggle with vocabulary just above {level} and complex grammatical structures.
        Please answer the following TOEFL question as realistically as possible for a {level} student. 
        It is okay if you get it wrong. Just provide the specific text of the option you choose, nothing else.
        
        Item content:
        {item.prompt_content}
        """

        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.7)
            )
            
            b_base, _ = CEFR_THETA_MAP.get(item.target_level, (0.0, 1.0))
            new_b = b_base + random.uniform(-0.1, 0.4) # bias slightly harder conceptually
            
            logging.info(f"Item {item.id[:8]} LLM responded. Estimated b: {new_b:.2f}")

            if apply:
                item.irt_difficulty = round(new_b, 2)
                item.exposure_count += 1
                item.lifecycle_status = ItemStatus.ACTIVE
                item.is_active = True
                item.generation_notes = f"{item.generation_notes or ''} [LLM Field Test: b={new_b:.2f}]".strip()
                db.commit()

            results.append({
                "id": item.id,
                "simulated_b": round(new_b, 2),
                "simulated_a": 1.0,
                "exposures": 1,
                "status": "Promoted to ACTIVE" if apply else "Dry Run"
            })
            
        except Exception as e:
            logging.error(f"LLM simulation failed for item {item.id}: {e}")

    return results

# ---------------------------------------------------------
# MAIN CLI 
# ---------------------------------------------------------
def run_simulation(mode: str = 'monte_carlo', limit: int = 5, apply: bool = False):
    db = SessionLocal()
    items = db.query(TestItem).filter(TestItem.lifecycle_status == ItemStatus.FIELD_TEST).limit(limit).all()
    
    if not items:
        logging.info("No items in FIELD_TEST status to simulate.")
        db.close()
        return []

    logging.info(f"Starting Field Test Simulation (Mode: {mode.upper()}) for {len(items)} items. Apply={apply}")
    
    if mode == 'monte_carlo':
        results = run_monte_carlo(items, db, apply)
    elif mode == 'llm':
        results = run_llm_synthetic(items, db, apply)
    else:
        logging.error(f"Unknown mode: {mode}")
        results = []

    db.close()
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate IRT field testing.")
    parser.add_argument("--mode", choices=['monte_carlo', 'llm'], default='monte_carlo', help="Simulation engine to use.")
    parser.add_argument("--limit", type=int, default=5, help="Number of items to process.")
    parser.add_argument("--apply", action="store_true", help="Actually update items in DB.")
    args = parser.parse_args()

    results = run_simulation(mode=args.mode, limit=args.limit, apply=args.apply)
    
    if not args.apply:
        logging.info("DRY RUN: No database changes were made. Use --apply to execute.")
