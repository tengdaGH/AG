import math
from typing import Dict, TypedDict

class SectionScores(TypedDict):
    reading: float
    listening: float
    speaking: float
    writing: float

class DualScore(TypedDict):
    band: float
    cefr: str
    legacy_range: str

class ScoreReport(TypedDict):
    reading: DualScore
    listening: DualScore
    speaking: DualScore
    writing: DualScore
    total: DualScore

class ScoreCalculationEngine:
    
    @staticmethod
    def _get_legacy_range(band: float) -> str:
        """Map individual section band to legacy 0-30 range"""
        if band >= 6.0: return "29-30"
        elif band >= 5.5: return "27-28"
        elif band >= 5.0: return "24-26"
        elif band >= 4.5: return "21-23"
        elif band >= 4.0: return "18-20"
        elif band >= 3.5: return "15-17"
        elif band >= 3.0: return "12-14"
        else: return "0-11"

    @staticmethod
    def _get_cefr_level(band: float) -> str:
        if band >= 6.0: return "C2"
        elif band >= 5.0: return "C1"
        elif band >= 4.0: return "B2"
        elif band >= 3.0: return "B1"
        elif band >= 2.0: return "A2"
        else: return "A1"
        
    @staticmethod
    def _get_total_legacy_range(band: float) -> str:
        """Map total averaged band to legacy 0-120 range"""
        if band >= 6.0: return "114-120"
        elif band >= 5.5: return "107-113"
        elif band >= 5.0: return "95-106"
        elif band >= 4.5: return "83-94"
        elif band >= 4.0: return "72-82"
        elif band >= 3.5: return "57-71"
        elif band >= 3.0: return "43-56"
        else: return "0-42"

    @staticmethod
    def round_to_half_band(value: float) -> float:
        """Rounds a float to the nearest 0.5 increment"""
        return round(value * 2) / 2.0

    @classmethod
    def calculate_total_score(cls, scores: SectionScores) -> ScoreReport:
        """
        Calculates the finalized 2026 score report from the 4 section bands.
        The overall score is the mathematical average of the 4 bands, rounded to nearest half-band.
        """
        bands = [scores['reading'], scores['listening'], scores['speaking'], scores['writing']]
        
        # 1. Average the four bands
        average_band = sum(bands) / len(bands)
        
        # 2. Round to nearest 0.5
        final_total_band = cls.round_to_half_band(average_band)
        
        report: ScoreReport = {
            "reading": {
                "band": scores['reading'],
                "cefr": cls._get_cefr_level(scores['reading']),
                "legacy_range": cls._get_legacy_range(scores['reading'])
            },
            "listening": {
                "band": scores['listening'],
                "cefr": cls._get_cefr_level(scores['listening']),
                "legacy_range": cls._get_legacy_range(scores['listening'])
            },
            "speaking": {
                "band": scores['speaking'],
                "cefr": cls._get_cefr_level(scores['speaking']),
                "legacy_range": cls._get_legacy_range(scores['speaking'])
            },
            "writing": {
                "band": scores['writing'],
                "cefr": cls._get_cefr_level(scores['writing']),
                "legacy_range": cls._get_legacy_range(scores['writing'])
            },
            "total": {
                "band": final_total_band,
                "cefr": cls._get_cefr_level(final_total_band),
                "legacy_range": cls._get_total_legacy_range(final_total_band)
            }
        }
        
        return report
