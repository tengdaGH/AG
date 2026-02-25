from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional

from app.services.tts_service import generate_tts_gemini, generate_tts_google_cloud

router = APIRouter(prefix="/tts", tags=["TTS"])

class TTSRequest(BaseModel):
    text: str
    provider: str = "gemini"  # Options: "gemini" or "google_cloud"

@router.post("/")
async def generate_tts(request: TTSRequest):
    """
    Generate audio from text using Gemini 2.0 Flash or Google Cloud TTS.
    Returns the binary audio data natively.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    if request.provider == "gemini":
        audio_bytes = generate_tts_gemini(request.text)
        media_type = "audio/wav"
    elif request.provider == "google_cloud":
        audio_bytes = generate_tts_google_cloud(request.text)
        media_type = "audio/mpeg"
    else:
        raise HTTPException(status_code=400, detail="Invalid provider. Choose 'gemini' or 'google_cloud'")
        
    return Response(content=audio_bytes, media_type=media_type)
