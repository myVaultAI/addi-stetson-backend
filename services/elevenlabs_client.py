"""
ElevenLabs Text-to-Speech Client Service
Handles voice synthesis for Addi responses
"""

import httpx
import logging
from typing import Optional, BinaryIO
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class ElevenLabsClient:
    """Client for ElevenLabs Text-to-Speech API"""
    
    def __init__(self, api_key: str, voice_id: str, model: str = "eleven_turbo_v2"):
        """
        Initialize ElevenLabs client
        
        Args:
            api_key: ElevenLabs API key (starts with 'xi_')
            voice_id: Voice ID for Addi (e.g., '21m00Tcm4TlvDq8ikWAM')
            model: TTS model to use (default: eleven_turbo_v2 for speed)
        """
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model
        self.base_url = "https://api.elevenlabs.io/v1"
        
        logger.info(f"ElevenLabsClient initialized with voice_id: {voice_id[:8]}...")
    
    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True
    ) -> bytes:
        """
        Convert text to speech audio
        
        Args:
            text: Text to convert to speech
            voice_id: Optional voice ID (uses default if not provided)
            stability: Voice stability (0-1, default 0.5)
            similarity_boost: Voice similarity (0-1, default 0.75)
            style: Style exaggeration (0-1, default 0.0)
            use_speaker_boost: Enable speaker boost for clarity
            
        Returns:
            Audio data as bytes (MP3 format)
            
        Raises:
            httpx.HTTPStatusError: If API request fails
            Exception: For other errors
        """
        voice_id = voice_id or self.voice_id
        
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        payload = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": use_speaker_boost
            }
        }
        
        try:
            logger.info(f"Synthesizing speech: {len(text)} characters")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                audio_data = response.content
                logger.info(f"Speech synthesized: {len(audio_data)} bytes")
                
                return audio_data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"TTS error: {str(e)}")
            raise
    
    async def text_to_speech_stream(
        self,
        text: str,
        voice_id: Optional[str] = None,
        **voice_settings
    ):
        """
        Stream audio data (for real-time playback)
        
        Args:
            text: Text to convert
            voice_id: Optional voice ID
            **voice_settings: Voice settings (stability, similarity_boost, etc.)
            
        Yields:
            Audio chunks as bytes
        """
        voice_id = voice_id or self.voice_id
        
        url = f"{self.base_url}/text-to-speech/{voice_id}/stream"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        # Default voice settings
        settings = {
            "stability": voice_settings.get("stability", 0.5),
            "similarity_boost": voice_settings.get("similarity_boost", 0.75),
            "style": voice_settings.get("style", 0.0),
            "use_speaker_boost": voice_settings.get("use_speaker_boost", True)
        }
        
        payload = {
            "text": text,
            "model_id": self.model,
            "voice_settings": settings
        }
        
        try:
            logger.info(f"Streaming speech: {len(text)} characters")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    
                    async for chunk in response.aiter_bytes(chunk_size=4096):
                        yield chunk
                        
        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs streaming error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"TTS streaming error: {str(e)}")
            raise
    
    async def get_voices(self):
        """
        Get list of available voices
        
        Returns:
            List of voices with their IDs and details
        """
        url = f"{self.base_url}/voices"
        
        headers = {
            "Accept": "application/json",
            "xi-api-key": self.api_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                voices = data.get("voices", [])
                
                logger.info(f"Retrieved {len(voices)} voices from ElevenLabs")
                return voices
                
        except Exception as e:
            logger.error(f"Failed to get voices: {str(e)}")
            raise
    
    async def get_user_info(self):
        """
        Get user account information and quota
        
        Returns:
            User info including character usage and limits
        """
        url = f"{self.base_url}/user"
        
        headers = {
            "Accept": "application/json",
            "xi-api-key": self.api_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                user_info = response.json()
                logger.info(f"User: {user_info.get('subscription', {}).get('tier', 'unknown')}")
                
                return user_info
                
        except Exception as e:
            logger.error(f"Failed to get user info: {str(e)}")
            raise
    
    def save_audio_to_file(self, audio_data: bytes, output_path: str):
        """
        Save audio data to MP3 file
        
        Args:
            audio_data: Audio bytes
            output_path: Path to save file
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"Audio saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save audio: {str(e)}")
            raise


# Singleton instance (will be initialized when config is available)
_elevenlabs_client: Optional[ElevenLabsClient] = None


def get_elevenlabs_client() -> ElevenLabsClient:
    """
    Get or create ElevenLabs client singleton
    
    Returns:
        ElevenLabsClient instance
        
    Raises:
        ValueError: If ElevenLabs is not configured
    """
    global _elevenlabs_client
    
    if _elevenlabs_client is None:
        # Import here to avoid circular imports
        from config import settings
        
        if not settings.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY not configured in environment")
        
        if not settings.ELEVENLABS_VOICE_ID:
            raise ValueError("ELEVENLABS_VOICE_ID not configured in environment")
        
        _elevenlabs_client = ElevenLabsClient(
            api_key=settings.ELEVENLABS_API_KEY,
            voice_id=settings.ELEVENLABS_VOICE_ID,
            model=settings.ELEVENLABS_MODEL
        )
        
        logger.info("ElevenLabs client initialized")
    
    return _elevenlabs_client


async def synthesize_speech(text: str, **voice_settings) -> bytes:
    """
    Convenience function to synthesize speech
    
    Args:
        text: Text to convert
        **voice_settings: Optional voice settings
        
    Returns:
        Audio data as bytes
    """
    client = get_elevenlabs_client()
    return await client.text_to_speech(text, **voice_settings)

