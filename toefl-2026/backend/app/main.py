from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import math
from sqlalchemy.orm import Session

from app.services.gemini_service import evaluate_essay_with_gemini, evaluate_speech_with_gemini
from app.database.connection import engine, Base, get_db
from app.models import models
from app.api.routes import sessions, items, tts, ielts, audio, auth

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TOEFL 2026 AI Scoring API", version="1.0.0")

# Register routes
app.include_router(sessions.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(tts.router, prefix="/api")
app.include_router(ielts.router, prefix="/api")
app.include_router(audio.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WritingSubmission(BaseModel):
    text: str
    expected_word_count: int = 50

class SpeechSubmission(BaseModel):
    transcript: str

@app.post("/api/score/writing")
async def score_writing(submission: WritingSubmission):
    try:
        # Utilize the Gemini service to evaluate the writing Submission
        score = await evaluate_essay_with_gemini(submission.text, submission.expected_word_count)
        return score
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/score/speaking")
async def score_speaking(submission: SpeechSubmission):
    # In a real scenario, an audio file would be processed by STT first.
    # Here we assume the transcript has already been generated and is passed in.
    try:
        score = await evaluate_speech_with_gemini(submission.transcript)
        return score
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
