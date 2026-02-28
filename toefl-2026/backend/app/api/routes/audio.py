from fastapi import APIRouter, File, Form, UploadFile, HTTPException
import os
from pathlib import Path

router = APIRouter()

# Define the directory where audio files will be saved
AUDIO_STORAGE_DIR = Path(__file__).parent.parent.parent.parent / "audio_uploads"
os.makedirs(AUDIO_STORAGE_DIR, exist_ok=True)

@router.post("/audio/upload")
async def upload_audio_chunk(
    audioFile: UploadFile = File(...),
    questionId: str = Form(...),
    sessionId: str = Form(...),
    chunkIndex: int = Form(...)
):
    try:
        # Create a folder for this specific session/question
        session_dir = AUDIO_STORAGE_DIR / sessionId / questionId
        os.makedirs(session_dir, exist_ok=True)
        
        file_path = session_dir / f"chunk_{chunkIndex}.webm"
        
        # Write the uploaded chunk to disk
        contents = await audioFile.read()
        with open(file_path, "wb") as f:
            f.write(contents)
            
        return {"status": "success", "chunkIndex": chunkIndex, "sessionId": sessionId, "questionId": questionId, "path": str(file_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save audio chunk: {str(e)}")
