import os
import base64
from fastapi import HTTPException
from google import genai
from google.genai import types

def generate_tts_gemini(text: str) -> bytes:
    """
    Generates Text-to-Speech using the experimental Gemini 2.0 Flash model's audio capabilities.
    Requires GEMINI_API_KEY environment variable.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    try:
        client = genai.Client(api_key=api_key)
        # Using Gemini 2.5 Flash TTS preview
        # We must instruct the model strictly to avoid generating additional text
        prompt = f"Generate audio from this precise transcript without adding or modifying anything:\n{text}"
        response = client.models.generate_content(
            model='gemini-2.5-flash-preview-tts',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Aoede"  # Example voice, others: Puck, Charon, Kore, Fenrir
                        )
                    )
                )
            )
        )
        
        # Extract audio inline data
        for part in response.candidates[0].content.parts:
            if getattr(part, "inline_data", None) and getattr(part.inline_data, "data", None):
                return part.inline_data.data
                
        raise ValueError("No audio data returned from Gemini.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini TTS generation failed: {str(e)}")

def generate_tts_google_cloud(text: str) -> bytes:
    """
    Generates Text-to-Speech using the traditional Google Cloud Text-to-Speech API.
    Requires GOOGLE_APPLICATION_CREDENTIALS environment variable to be set.
    """
    try:
        from google.cloud import texttospeech
        
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Journey-O" # A high-quality Journey voice
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return response.audio_content

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Cloud TTS generation failed: {str(e)}")
