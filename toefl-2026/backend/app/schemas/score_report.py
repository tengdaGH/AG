from typing import Optional, Dict
from pydantic import BaseModel, HttpUrl

class CandidateInfo(BaseModel):
    ets_id: str
    full_name: str
    photo_url: Optional[HttpUrl]
    test_date: str
    appointment_number: str

class DualScore(BaseModel):
    band: float
    cefr: str
    legacy_range: str

class SectionScores(BaseModel):
    reading: DualScore
    listening: DualScore
    speaking: DualScore
    writing: DualScore
    total: DualScore

class MyBestScoreInstance(BaseModel):
    band: float
    date: str

class MyBestAggregation(BaseModel):
    reading: MyBestScoreInstance
    listening: MyBestScoreInstance
    speaking: MyBestScoreInstance
    writing: MyBestScoreInstance
    total_superscore: DualScore

class ScoreScoresObject(BaseModel):
    current_administration: SectionScores
    my_best: MyBestAggregation

class PerformanceFeedback(BaseModel):
    reading: str
    writing: str

class SecurityValidation(BaseModel):
    qr_validation_url: HttpUrl
    document_hash: str

class OfficialScoreReportSchema(BaseModel):
    """
    The master schema for the official TOEFL iBT 2026 Digital Score Report
    delivered to institutions and test takers 72 hours post-assessment.
    """
    report_id: str
    candidate: CandidateInfo
    scores: ScoreScoresObject
    feedback: PerformanceFeedback
    security: SecurityValidation
