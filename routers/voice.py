"""
Voice API Router
Endpoints for text-to-speech and voice synthesis
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from typing import Optional
from pydantic import BaseModel, Field
from services.elevenlabs_client import get_elevenlabs_client, synthesize_speech
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])


class TextToSpeechRequest(BaseModel):
    """Request model for text-to-speech"""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    voice_id: Optional[str] = Field(default=None, description="Optional voice ID (uses default if not provided)")
    stability: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Voice stability (0-1)")
    similarity_boost: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Voice similarity (0-1)")
    style: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Style exaggeration (0-1)")


class VoiceSettings(BaseModel):
    """Voice configuration settings"""
    voice_id: str
    model: str
    stability: float
    similarity: float
    style: float


@router.post("/synthesize")
async def text_to_speech(request: TextToSpeechRequest):
    """
    Convert text to speech using ElevenLabs
    
    Returns MP3 audio data
    
    Example:
        POST /api/voice/synthesize
        {
            "text": "Hello! I'm Addi, your Stetson admissions assistant.",
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    """
    try:
        # Check if ElevenLabs is configured
        if not settings.ELEVENLABS_API_KEY:
            raise HTTPException(
                status_code=503,
                detail="ElevenLabs not configured. Please set ELEVENLABS_API_KEY in environment."
            )
        
        if not settings.ELEVENLABS_VOICE_ID:
            raise HTTPException(
                status_code=503,
                detail="ElevenLabs voice not configured. Please set ELEVENLABS_VOICE_ID in environment."
            )
        
        # Prepare voice settings
        voice_settings = {}
        if request.stability is not None:
            voice_settings['stability'] = request.stability
        else:
            voice_settings['stability'] = settings.ELEVENLABS_STABILITY
        
        if request.similarity_boost is not None:
            voice_settings['similarity_boost'] = request.similarity_boost
        else:
            voice_settings['similarity_boost'] = settings.ELEVENLABS_SIMILARITY
        
        if request.style is not None:
            voice_settings['style'] = request.style
        else:
            voice_settings['style'] = settings.ELEVENLABS_STYLE
        
        # Synthesize speech
        logger.info(f"Synthesizing speech: {len(request.text)} characters")
        
        client = get_elevenlabs_client()
        audio_data = await client.text_to_speech(
            text=request.text,
            voice_id=request.voice_id,
            **voice_settings
        )
        
        # Return audio as MP3
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": 'inline; filename="speech.mp3"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to synthesize speech: {str(e)}"
        )


@router.post("/synthesize-stream")
async def text_to_speech_stream(request: TextToSpeechRequest):
    """
    Stream text-to-speech audio (for real-time playback)
    
    Returns streaming MP3 audio data
    """
    try:
        # Check configuration
        if not settings.ELEVENLABS_API_KEY:
            raise HTTPException(
                status_code=503,
                detail="ElevenLabs not configured"
            )
        
        # Prepare voice settings
        voice_settings = {
            'stability': request.stability or settings.ELEVENLABS_STABILITY,
            'similarity_boost': request.similarity_boost or settings.ELEVENLABS_SIMILARITY,
            'style': request.style or settings.ELEVENLABS_STYLE
        }
        
        client = get_elevenlabs_client()
        
        # Stream audio chunks
        async def audio_stream():
            async for chunk in client.text_to_speech_stream(
                text=request.text,
                voice_id=request.voice_id,
                **voice_settings
            ):
                yield chunk
        
        return StreamingResponse(
            audio_stream(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": 'inline; filename="speech.mp3"',
                "Transfer-Encoding": "chunked"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS streaming error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stream speech: {str(e)}"
        )


@router.get("/voices")
async def list_voices():
    """
    Get list of available ElevenLabs voices
    
    Returns list of voices with their IDs and metadata
    """
    try:
        if not settings.ELEVENLABS_API_KEY:
            raise HTTPException(
                status_code=503,
                detail="ElevenLabs not configured"
            )
        
        client = get_elevenlabs_client()
        voices = await client.get_voices()
        
        return {
            "success": True,
            "voices": voices,
            "count": len(voices)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voices: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve voices: {str(e)}"
        )


@router.get("/settings")
async def get_voice_settings():
    """
    Get current voice configuration
    
    Returns configured voice settings
    """
    try:
        if not settings.ELEVENLABS_API_KEY:
            return {
                "configured": False,
                "message": "ElevenLabs not configured. Set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in .env"
            }
        
        return {
            "configured": True,
            "voice_id": settings.ELEVENLABS_VOICE_ID or "Not set",
            "model": settings.ELEVENLABS_MODEL,
            "stability": settings.ELEVENLABS_STABILITY,
            "similarity": settings.ELEVENLABS_SIMILARITY,
            "style": settings.ELEVENLABS_STYLE,
            "api_key_set": bool(settings.ELEVENLABS_API_KEY)
        }
        
    except Exception as e:
        logger.error(f"Failed to get settings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve settings: {str(e)}"
        )


@router.get("/health")
async def voice_health():
    """
    Check ElevenLabs service health
    
    Tests API connection and returns account info
    """
    try:
        if not settings.ELEVENLABS_API_KEY:
            return {
                "status": "not_configured",
                "message": "ElevenLabs API key not set"
            }
        
        if not settings.ELEVENLABS_VOICE_ID:
            return {
                "status": "incomplete",
                "message": "ElevenLabs Voice ID not set",
                "api_key_set": True
            }
        
        # Try to get user info to verify connection
        client = get_elevenlabs_client()
        user_info = await client.get_user_info()
        
        subscription = user_info.get('subscription', {})
        
        return {
            "status": "healthy",
            "configured": True,
            "voice_id_set": True,
            "subscription_tier": subscription.get('tier', 'unknown'),
            "character_count": user_info.get('character_count', 0),
            "character_limit": user_info.get('character_limit', 0),
            "can_use_instant_voice_cloning": subscription.get('can_use_instant_voice_cloning', False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Failed to connect to ElevenLabs API"
        }


@router.post("/test")
async def test_voice():
    """
    Test voice synthesis with sample text
    
    Returns test audio to verify configuration
    """
    try:
        if not settings.ELEVENLABS_API_KEY or not settings.ELEVENLABS_VOICE_ID:
            raise HTTPException(
                status_code=503,
                detail="ElevenLabs not fully configured"
            )
        
        test_text = (
            "Hi! I'm Addi, your Stetson University admissions assistant. "
            "I'm here to help answer your questions about admissions, financial aid, and campus life. "
            "How can I help you today?"
        )
        
        client = get_elevenlabs_client()
        audio_data = await client.text_to_speech(test_text)
        
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": 'inline; filename="test_speech.mp3"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Voice test failed: {str(e)}"
        )

