import os
import asyncio
import httpx
import base64
from typing import Optional

INWORLD_KEY = os.getenv("INWORLD_KEY")
INWORLD_SECRET = os.getenv("INWORLD_SECRET")
INWORLD_API_KEY = os.getenv("INWORLD_API_KEY")

async def generate_audio_with_inworld(text: str, voice_id: str = "Brian", output_path: Optional[str] = None) -> dict:
    """
    Generates audio for a given text using Inworld's API.
    """
    if not INWORLD_KEY or not INWORLD_SECRET:
        return {
            "status": "error",
            "message": "Inworld API credentials not fully configured (KEY or SECRET missing)",
            "provider": "Inworld-Mock"
        }

    url = "https://api.inworld.ai/tts/v1/voice"
    payload = {
        "text": text,
        "voiceId": voice_id,
        "modelId": "inworld-tts-1.5-max",
        "applyTextNormalization": "ON",
        "textType": "TEXT"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, 
                auth=(INWORLD_KEY, INWORLD_SECRET), 
                json=payload,
                timeout=30.0
            )
            
            if resp.status_code == 200:
                data = resp.json()
                audio_content_b64 = data.get("audioContent")
                if not audio_content_b64:
                    return {
                        "status": "error",
                        "message": "No audioContent in response",
                        "provider": "Inworld"
                    }
                
                audio_content = base64.b64decode(audio_content_b64)
                
                # We save it to a temporary location to pad it with ffmpeg
                import tempfile
                import subprocess
                import uuid
                import os
                
                temp_filename = os.path.join(tempfile.gettempdir(), f"inworld_{uuid.uuid4().hex}.mp3")
                padded_filename = os.path.join(tempfile.gettempdir(), f"inworld_{uuid.uuid4().hex}_padded.mp3")
                
                with open(temp_filename, 'wb') as f:
                    f.write(audio_content)
                
                try:
                    subprocess.run([
                        "ffmpeg", "-y", "-i", temp_filename, "-af", "adelay=500|500", padded_filename
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    
                    with open(padded_filename, 'rb') as f:
                        padded_content = f.read()
                        
                    if output_path:
                        out_dir = os.path.dirname(output_path)
                        if out_dir:
                            os.makedirs(out_dir, exist_ok=True)
                        with open(output_path, 'wb') as f:
                            f.write(padded_content)
                        result = {
                            "status": "success",
                            "path": output_path,
                            "provider": "Inworld"
                        }
                    else:
                        result = {
                            "status": "success",
                            "content": padded_content,
                            "provider": "Inworld"
                        }
                finally:
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)
                    if os.path.exists(padded_filename):
                        os.remove(padded_filename)
                        
                return result
            else:
                return {
                    "status": "error",
                    "message": f"Inworld API Error: {resp.status_code} - {resp.text}",
                    "provider": "Inworld"
                }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Exception during Inworld API call: {str(e)}",
            "provider": "Inworld"
        }
    
    return {
        "status": "error",
        "message": "Unknown error in audio generation",
        "provider": "Inworld"
    }
