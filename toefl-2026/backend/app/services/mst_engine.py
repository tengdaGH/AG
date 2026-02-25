import math
from typing import List, Dict, Tuple, Optional

class IRTItem:
    def __init__(self, item_id: str, a: float, b: float, c: float = 0.25):
        """
        a = Discrimination parameter (0.5 to 2.5)
        b = Difficulty parameter (-3.0 to +3.0)
        c = Pseudo-guessing parameter (0.25 for 4-option MCQs, 0.0 for fill-in-the-blank)
        """
        self.item_id = item_id
        self.a = a
        self.b = b
        self.c = c

class ResponseRecord:
    def __init__(self, item_id: str, is_correct: bool, time_spent_ms: int):
        self.item_id = item_id
        self.is_correct = is_correct
        self.time_spent_ms = time_spent_ms

class MSTEngine:
    D_CONSTANT = 1.702  # Scales the logistic function to a normal ogive model
    ROUTING_THRESHOLD = 0.35  # Threshold to route to Track A (Hard)
    RAPID_GUESS_THRESHOLD_MS = 3000  # Less than 3 seconds is flagged as a rapid guess

    @staticmethod
    def _probability_3pl(theta: float, item: IRTItem) -> float:
        """
        Calculates the probability of a correct response using the 3PL model.
        """
        exponent = -MSTEngine.D_CONSTANT * item.a * (theta - item.b)
        # Prevent math domain errors from extreme exponent values
        exponent = max(-500, min(500, exponent)) 
        p = item.c + (1 - item.c) / (1 + math.exp(exponent))
        return p

    @staticmethod
    def _normal_pdf(x: float, mu: float = 0, sigma: float = 1) -> float:
        """Standard Normal Prior"""
        return (1 / (sigma * math.sqrt(2 * math.pi))) * math.exp(-0.5 * ((x - mu) / sigma) ** 2)

    @staticmethod
    def calculate_eap(responses: List[ResponseRecord], item_bank: Dict[str, IRTItem]) -> float:
        """
        Expected A Posteriori (EAP) ability estimation.
        Also applies Rapid Guessing Detection (RGD) penalty.
        """
        # Step 1: Rapid Guess Detection (RGD) Check
        rapid_guesses = sum(1 for r in responses if r.time_spent_ms < MSTEngine.RAPID_GUESS_THRESHOLD_MS)
        rgd_penalty_active = len(responses) > 0 and (rapid_guesses / len(responses)) > 0.30

        # Create discrete quadratures (nodes) for numerical integration (-4.0 to 4.0 in 0.1 steps)
        nodes = [x / 10.0 for x in range(-40, 41)]
        
        numerator = 0.0
        denominator = 0.0

        for theta in nodes:
            likelihood = 1.0
            
            for r in responses:
                if r.item_id not in item_bank:
                    continue
                
                item = item_bank[r.item_id]
                
                # Apply RGD Penalty by flattening discrimination
                if rgd_penalty_active and r.time_spent_ms < MSTEngine.RAPID_GUESS_THRESHOLD_MS:
                    item.a = 0.01  # Heavily discriminates against guessing exploits
                    
                p = MSTEngine._probability_3pl(theta, item)
                if r.is_correct:
                    likelihood *= p
                else:
                    likelihood *= (1 - p)
            
            prior = MSTEngine._normal_pdf(theta)
            posterior_unnormalized = likelihood * prior
            
            numerator += theta * posterior_unnormalized
            denominator += posterior_unnormalized

        if denominator == 0:
            return 0.0 # Fallback in extreme mathematical edge cases
        
        return numerator / denominator

    @staticmethod
    def route_stage_2(theta_stage1: float) -> str:
        """
        Determines the Stage 2 Track (A or B) based on Stage 1 ability estimate.
        """
        if theta_stage1 >= MSTEngine.ROUTING_THRESHOLD:
            return "Track A"
        return "Track B"

    @staticmethod
    def get_final_score(final_theta: float, track: str) -> Dict[str, str | float]:
        """
        Maps the final theta to the new 2026 1.0 - 6.0 CEFR-Aligned Band Scale
        and the legacy 0-30 equivalent score.
        """
        
        # Enforce Track B cap (Cannot score higher than Band 4.5 / B2+)
        if track == "Track B" and final_theta > 1.09:
            final_theta = 1.09

        if final_theta >= 2.20:
            return {"band": 6.0, "cefr": "C2", "legacy": "29-30"}
        elif 1.65 <= final_theta < 2.20:
            return {"band": 5.5, "cefr": "C1+", "legacy": "27-28"}
        elif 1.10 <= final_theta < 1.65:
            return {"band": 5.0, "cefr": "C1", "legacy": "24-26"}
        elif 0.55 <= final_theta < 1.10:
            return {"band": 4.5, "cefr": "B2+", "legacy": "21-23"}
        elif 0.00 <= final_theta < 0.55:
            return {"band": 4.0, "cefr": "B2", "legacy": "18-20"}
        elif -0.55 <= final_theta < 0.00:
            return {"band": 3.5, "cefr": "B1+", "legacy": "15-17"}
        elif -1.10 <= final_theta < -0.55:
            return {"band": 3.0, "cefr": "B1", "legacy": "12-14"}
        else:
            return {"band": 2.5, "cefr": "A2/A1", "legacy": "0-11"}
