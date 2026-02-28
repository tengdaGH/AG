import json
import asyncio
from typing import Dict, TypedDict

from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from app.models.models import TestItemQuestion, TestItem, TaskType
from app.services.gemini_service import evaluate_essay_with_gemini, evaluate_speech_with_gemini

class SelectedResponseResult(TypedDict):
    item_id: str
    is_correct: bool
    correct_answer: str
    student_response: str
    is_constructed_response: bool

class ConstructedResponseResult(TypedDict):
    item_id: str
    student_response: str
    max_score: int
    rubric_score: int
    cefr_level: str
    feedback: Dict[str, str]
    is_constructed_response: bool
    model_used: str

class ScoringEngine:
    
    @staticmethod
    def _normalize_string(val) -> str:
        """Helper to normalize strings for comparison (lowercase, strip trailing grammar)."""
        if val is None:
            return ""
        if isinstance(val, (list, tuple)):
            # Special case for BUILD_A_SENTENCE where answer is JSON array
            val = " ".join([str(v) for v in val])
        return str(val).strip().lower()

    @classmethod
    def score_selected_responses(cls, db: Session, student_responses: Dict[str, str]) -> Dict[str, SelectedResponseResult]:
        """
        Phase 1: Selected Response (SR) Scoring Algorithm.
        Takes a dictionary of { "question_uuid": "student_response_string" } and 
        returns a dictionary of evaluation results.
        """
        
        # 1. Fetch all requested question templates from the database in one query
        question_ids = list(student_responses.keys())
        if not question_ids:
            return {}
            
        questions = db.query(TestItemQuestion).filter(TestItemQuestion.id.in_(question_ids)).all()
        
        results: Dict[str, SelectedResponseResult] = {}
        
        for q in questions:
            # Skip constructed responses for Phase 1
            if q.is_constructed_response:
                results[q.id] = {
                    "item_id": q.test_item_id,
                    "is_correct": False,
                    "correct_answer": "Needs CR Rubric Grading",
                    "student_response": str(student_responses.get(q.id, "")),
                    "is_constructed_response": True
                }
                continue
            
            # 2. Extract and Normalize Responses
            expected_raw = q.correct_answer
            student_raw = student_responses.get(q.id)
            
            # Check if expected answer is actually a stringified JSON array (BUILD_A_SENTENCE)
            try:
                if expected_raw.startswith("[") and expected_raw.endswith("]"):
                    expected_raw = json.loads(expected_raw)
            except:
                pass
                
            expected = cls._normalize_string(expected_raw)
            student = cls._normalize_string(student_raw)
            
            # BUILD_A_SENTENCE edge case from frontend format returning array
            try:
                if student_raw and isinstance(student_raw, (list, tuple)):
                    student = " ".join([str(v) for v in student_raw]).strip().lower()
                elif student_raw and isinstance(student_raw, str) and student_raw.startswith("["):
                    parsed = json.loads(student_raw)
                    if isinstance(parsed, list):
                        student = " ".join([str(v) for v in parsed]).strip().lower()
            except:
                pass
            
            # 3. Deterministic Match
            is_correct = (expected == student) and (student != "")
            
            # C-Test partial matching heuristic placeholder if needed:
            # For now, exact normalized match required.

            results[q.id] = {
                "item_id": q.test_item_id,
                "is_correct": is_correct,
                "correct_answer": expected,
                "student_response": student,
                "is_constructed_response": False
            }
            
        return results

    @classmethod
    async def score_constructed_responses(cls, db: Session, student_responses: Dict[str, str]) -> Dict[str, ConstructedResponseResult]:
        """
        Phase 2: Constructed Response (CR) Scoring Algorithm.
        Takes a dictionary of { "question_uuid": "student_response_string_or_audio_transcript" } and 
        uses the LLM to grade them against the max_score rubric.
        """
        question_ids = list(student_responses.keys())
        if not question_ids:
            return {}
            
        # Eager load the TestItem so we can check the TaskType (Writing vs Speaking)
        questions = db.query(TestItemQuestion).options(joinedload(TestItemQuestion.test_item)).filter(TestItemQuestion.id.in_(question_ids)).all()
        
        results: Dict[str, ConstructedResponseResult] = {}
        pending_evals = []

        # We will dispatch all LLM requests concurrently using asyncio
        async def evaluate_single(q: TestItemQuestion, resp_text: str):
            task_type = q.test_item.task_type
            max_score = q.max_score or 5
            
            # Decide which LLM agent to invoke based on Speaking vs Writing
            if task_type in [TaskType.LISTEN_AND_REPEAT, TaskType.TAKE_AN_INTERVIEW]:
                eval_data = await evaluate_speech_with_gemini(resp_text)
            else:
                # Default to Writing 
                # Grab word count target if available
                target_words = 150
                try:
                    pc = json.loads(q.test_item.prompt_content)
                    target_str = pc.get("wordTarget", "150") # e.g. "65-90"
                    if isinstance(target_str, str) and "-" in target_str:
                        target_words = int(target_str.split("-")[1])
                    elif str(target_str).isdigit():
                        target_words = int(target_str)
                except:
                    pass
                eval_data = await evaluate_essay_with_gemini(resp_text, target_words)
            
            # Cap raw score to the item's max_score
            actual_score = min(eval_data.get("rawScore", 0), max_score)
            
            results[q.id] = {
                "item_id": q.test_item_id,
                "student_response": str(resp_text),
                "max_score": max_score,
                "rubric_score": actual_score,
                "cefr_level": eval_data.get("cefrLevel", "B1"),
                "feedback": eval_data.get("detailedFeedback", {}),
                "is_constructed_response": True,
                "model_used": eval_data.get("model_used", "Unknown")
            }

        for q in questions:
            if not q.is_constructed_response:
                continue
                
            student_raw = student_responses.get(q.id, "")
            pending_evals.append(evaluate_single(q, str(student_raw)))
            
        # Execute all LLM calls concurrently
        if pending_evals:
            await asyncio.gather(*pending_evals)
            
        return results
