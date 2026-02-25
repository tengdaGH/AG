# ============================================================
# Purpose:       Simulate IRT field test data for FIELD_TEST items and promote them to ACTIVE status.
# Usage:         python backend/scripts/simulate_field_test.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import sys
import logging
import random
from sqlalchemy.orm import Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models.models import TestItem, ItemStatus
from app.database.connection import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def simulate_irt_data(b_param: float) -> tuple[float, float, int]:
    """
    Simulates test data for a single item.
    Returns: newly calculated (difficulty, discrimination, exposures)
    """
    # Number of simulated test takers
    exposures = random.randint(300, 800)
    
    # In a real IRT calibration, b_param might shift slightly based on sample
    new_b = b_param + random.uniform(-0.2, 0.2)
    new_b = max(-3.0, min(3.0, new_b)) # Bound between -3 and 3
    
    # Simulate a discrimination parameter (a-parameter), typically 0.5 to 2.5
    # A good item has discrimination > 1.0
    new_a = random.uniform(0.8, 2.0)
    
    return round(new_b, 2), round(new_a, 2), exposures

def run_simulation(limit: int = 5):
    """
    Pulls items in FIELD_TEST status, simulates administration data, 
    and promotes them to ACTIVE status if successful.
    """
    db = SessionLocal()
    items = db.query(TestItem).filter(TestItem.lifecycle_status == ItemStatus.FIELD_TEST).limit(limit).all()
    
    if not items:
        logging.info("No items in FIELD_TEST status to simulate.")
        db.close()
        return []

    logging.info(f"Simulating IRT data for {len(items)} items in FIELD_TEST status...")
    results = []
    
    for item in items:
        logging.info(f"Simulating Item ID: {item.id}")
        
        # Simulate the calibration
        new_b, new_a, exposures = simulate_irt_data(float(item.irt_difficulty))
        
        # Update the item
        item.irt_difficulty = new_b
        item.irt_discrimination = new_a
        item.exposure_count = exposures
        item.lifecycle_status = ItemStatus.ACTIVE
        item.is_active = True
        item.generation_notes = f"{item.generation_notes or ''} [Simulated Field Test: b={new_b}, a={new_a}, n={exposures}]".strip()
        
        db.commit()
        
        results.append({
            "id": item.id,
            "simulated_b": new_b,
            "simulated_a": new_a,
            "exposures": exposures,
            "status": "Promoted to ACTIVE"
        })
        logging.info(f"Item {item.id} calibrated and promoted to ACTIVE.")
        
    db.close()
    return results

if __name__ == "__main__":
    run_simulation()
