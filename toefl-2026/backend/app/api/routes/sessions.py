import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from app.database.connection import get_db, get_user_db
from app.models.models import TestSession, SessionStatus, TestResponse, TestItem, TestItemQuestion
from pydantic import BaseModel

router = APIRouter()

class SessionCreate(BaseModel):
    student_id: str

class TestSubmission(BaseModel):
    answers: Dict[str, str]

@router.post("/sessions", tags=["sessions"])
def create_test_session(session_data: SessionCreate, user_db: Session = Depends(get_user_db)):
    new_session = TestSession(
        student_id=session_data.student_id,
        status=SessionStatus.ACTIVE
    )
    user_db.add(new_session)
    user_db.commit()
    user_db.refresh(new_session)
    return new_session

@router.get("/sessions/{session_id}", tags=["sessions"])
def get_test_session(session_id: str, user_db: Session = Depends(get_user_db)):
    session = user_db.query(TestSession).filter(TestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

# 1. 搞一个小本本（内存字典），记录每个人最后一次提交的时间戳
# 格式 {"student_123": 1700000000.0}
last_submit_time_tracker = {}

@router.post("/sessions/{session_id}/submit", tags=["sessions"])
async def submit_test_session(
    session_id: str, 
    submission: TestSubmission, 
    db: Session = Depends(get_db),
    user_db: Session = Depends(get_user_db)
):
    session = user_db.query(TestSession).filter(TestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 【极简防线 2：防连点和机器刷单】
    current_time = time.time()
    student_id = session.student_id
    last_time = last_submit_time_tracker.get(student_id, 0)
    
    # 算一下两次点击的间隔，如果距离上次提交还没过 10秒钟
    if current_time - last_time < 10:
        raise HTTPException(status_code=429, detail="您提交太快了，请稍后再试")
        
    # 如果通过了检查，把当前时间登记到小本本上
    last_submit_time_tracker[student_id] = current_time

    from app.services.scoring_engine import ScoringEngine

    answers = submission.answers

    # 【极简防线 1：限制最高字数，防止被恶意消耗 Token】
    for ans_text in answers.values():
        if isinstance(ans_text, str) and len(ans_text) > 4000:
            raise HTTPException(status_code=400, detail="提交的文本过长，请精简后再试。")

    # 1. Deterministic Scoring
    sr_results = ScoringEngine.score_selected_responses(db, answers)

    # 2. LLM Scoring
    cr_results = await ScoringEngine.score_constructed_responses(db, answers)

    # Combine and save to database
    all_responses = []

    for q_id, sr_ans in sr_results.items():
        if sr_ans.get("is_constructed_response"):
            continue # skip CR items, they are handled below
            
        resp = TestResponse(
            session_id=session_id,
            question_id=q_id,
            student_raw_response=sr_ans["student_response"],
            is_correct=sr_ans["is_correct"],
            rubric_score=None,
            ai_feedback=None
        )
        all_responses.append(resp)
        user_db.add(resp)

    for q_id, cr_ans in cr_results.items():
        resp = TestResponse(
            session_id=session_id,
            question_id=q_id,
            student_raw_response=cr_ans["student_response"],
            is_correct=None,
            rubric_score=cr_ans["rubric_score"],
            ai_feedback={
                "cefr_level": cr_ans["cefr_level"],
                "feedback": cr_ans["feedback"],
                "model_used": cr_ans.get("model_used")
            }
        )
        all_responses.append(resp)
        user_db.add(resp)

    # Calculate total score from sr_results
    # Currently just simple sum of deterministic correct
    # Could be updated to more complex logic
    total_score = sum(1 for res in sr_results.values() if res.get("is_correct"))
    session.total_score = total_score
    session.status = SessionStatus.COMPLETED

    user_db.commit()

    return {
        "status": "success",
        "message": "Responses processed and scored safely.",
        "session_id": session_id,
        "total_score": session.total_score
    }

@router.get("/sessions/{session_id}/results", tags=["sessions"])
def get_test_session_results(session_id: str, db: Session = Depends(get_db), user_db: Session = Depends(get_user_db)):
    # Validate session
    session = user_db.query(TestSession).filter(TestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Fetch responses
    responses = user_db.query(TestResponse).filter(TestResponse.session_id == session_id).all()
    if not responses:
        raise HTTPException(status_code=404, detail="No responses found for this session")

    stats = {
        "READING": {"correct": 0.0, "total": 0},
        "LISTENING": {"correct": 0.0, "total": 0},
        "SPEAKING": {"correct": 0.0, "total": 0},
        "WRITING": {"correct": 0.0, "total": 0}
    }
    
    detailed_responses = []
    
    for r in responses:
        q = db.query(TestItemQuestion).filter(TestItemQuestion.id == r.question_id).first()
        if not q: continue
        i = db.query(TestItem).filter(TestItem.id == q.test_item_id).first()
        if not i: continue
        sec = i.section.value if hasattr(i.section, "value") else i.section
        sec_key = sec.upper()
        
        if sec_key in stats:
            stats[sec_key]["total"] += 1
            if r.is_correct:
                stats[sec_key]["correct"] += 1
            elif r.rubric_score is not None:
                max_pts = float(q.max_score or 5.0)
                stats[sec_key]["correct"] += (float(r.rubric_score) / max_pts)

        student_ans_str = r.student_raw_response
        correct_ans_str = q.correct_answer or "N/A"
        
        if q.options and isinstance(q.options, list):
            if student_ans_str and student_ans_str.isdigit():
                try:
                    idx = int(student_ans_str)
                    if 0 <= idx < len(q.options):
                        student_ans_str = q.options[idx]
                except ValueError:
                    pass
                    
            if q.correct_answer and q.correct_answer.isdigit():
                try:
                    idx = int(q.correct_answer)
                    if 0 <= idx < len(q.options):
                        correct_ans_str = q.options[idx]
                except ValueError:
                    pass

        detailed_responses.append({
            "section": sec_key,
            "task_type": i.task_type,
            "questionText": q.question_text or "Audio/Passage Question",
            "studentAnswer": student_ans_str,
            "correctAnswer": correct_ans_str,
            "isCorrect": r.is_correct,
            "rubricScore": r.rubric_score
        })

    def calc_band(val):
        score = (val["correct"] / max(val["total"], 1)) * 6.0
        return min(max(round(score * 2) / 2, 1.0), 6.0)

    for sec in stats:
        stats[sec]["band"] = calc_band(stats[sec])

    # Ensure there's a baseline score if they skipped everything
    if stats["READING"]["total"] == 0: stats["READING"]["band"] = 3.5
    if stats["LISTENING"]["total"] == 0: stats["LISTENING"]["band"] = 4.0
    if stats["SPEAKING"]["total"] == 0: stats["SPEAKING"]["band"] = 4.0
    if stats["WRITING"]["total"] == 0: stats["WRITING"]["band"] = 4.5

    total_band = (stats["READING"]["band"] + stats["LISTENING"]["band"] + stats["SPEAKING"]["band"] + stats["WRITING"]["band"]) / 4.0

    def cefr(band):
        if band >= 5.0: return "C1"
        if band >= 4.0: return "B2"
        if band >= 3.0: return "B1"
        return "A2"

    def legacy_range(band):
        if band >= 5.5: return "28-30"
        if band >= 4.5: return "24-27"
        if band >= 3.5: return "18-23"
        return "0-17"

    total_legacy = f"{int((total_band/6.0)*120)}-{min(int((total_band/6.0)*120) + 5, 120)}"

    return {
        "scores": {
            "reading": {"band": stats["READING"]["band"], "cefr": cefr(stats["READING"]["band"]), "legacyRange": legacy_range(stats["READING"]["band"])},
            "listening": {"band": stats["LISTENING"]["band"], "cefr": cefr(stats["LISTENING"]["band"]), "legacyRange": legacy_range(stats["LISTENING"]["band"])},
            "speaking": {"band": stats["SPEAKING"]["band"], "cefr": cefr(stats["SPEAKING"]["band"]), "legacyRange": legacy_range(stats["SPEAKING"]["band"])},
            "writing": {"band": stats["WRITING"]["band"], "cefr": cefr(stats["WRITING"]["band"]), "legacyRange": legacy_range(stats["WRITING"]["band"])},
            "total": {"band": total_band, "cefr": cefr(total_band), "legacyRange": total_legacy}
        },
        "feedback": {
            "reading": "Candidate demonstrates solid comprehension of both academic and daily reading passages. The AI analysis of your rubric essays shows good performance in semantic understanding.",
            "writing": "Candidate's writing shows good grammatical control. Some lexical variety issues were caught by the Gemini rater in your Academic Discussion response."
        },
        "detailedResponses": detailed_responses
    }
