import os
import logging
import base64
import asyncio
from typing import Optional, List, AsyncGenerator
from io import BytesIO
import httpx
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class TTSService:
    """Text-to-Speech service using OpenAI's TTS API"""
    
    def __init__(self):
        # Initialize OpenAI client with API key check
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
            self.api_available = True
        else:
            self.client = None
            self.api_available = False
            logger.warning("OpenAI API key not set - TTS functionality will be disabled")
        
        self.default_voice = "alloy"
        self.default_model = "tts-1"  # Use tts-1 for smaller files vs tts-1-hd
        self.default_format = "mp3"   # MP3 is compressed
        
        # Available voices from OpenAI TTS
        self.available_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        
        # Audio settings
        self.sample_rate = 24000  # OpenAI TTS default
        self.max_text_length = 4096  # OpenAI TTS limit
    
    async def generate_speech(
        self, 
        text: str, 
        voice: str = None,
        model: str = None,
        response_format: str = None,
        speed: float = 1.0
    ) -> bytes:
        """
        Generate speech audio from text
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            model: TTS model (tts-1 or tts-1-hd)
            response_format: Audio format (mp3, opus, aac, flac)
            speed: Speech speed (0.25 to 4.0)
            
        Returns:
            Audio data as bytes
        """
        try:
            # Check if API is available
            if not self.api_available or not self.client:
                raise TTSError("OpenAI API key not configured - TTS functionality disabled")
            
            # Validate and set defaults
            voice = voice or self.default_voice
            model = model or self.default_model
            response_format = response_format or self.default_format
            
            # Validate voice
            if voice not in self.available_voices:
                logger.warning(f"Invalid voice '{voice}', using default '{self.default_voice}'")
                voice = self.default_voice
            
            # Validate speed
            speed = max(0.25, min(4.0, speed))
            
            # Truncate text if too long
            if len(text) > self.max_text_length:
                logger.warning(f"Text too long ({len(text)} chars), truncating to {self.max_text_length}")
                text = text[:self.max_text_length] + "..."
            
            # Generate speech
            logger.info(f"Generating speech: voice={voice}, model={model}, format={response_format}")
            
            response = await self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format=response_format,
                speed=speed
            )
            
            # Return audio bytes
            audio_data = response.content
            logger.info(f"Generated {len(audio_data)} bytes of audio")
            
            return audio_data
            
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            raise TTSError(f"Failed to generate speech: {e}")
    
    async def generate_speech_base64(
        self,
        text: str,
        voice: str = None,
        **kwargs
    ) -> str:
        """
        Generate speech and return as base64 encoded string for WebSocket transmission
        
        Returns:
            Base64 encoded audio data
        """
        try:
            audio_data = await self.generate_speech(text, voice, **kwargs)
            return base64.b64encode(audio_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Base64 TTS generation failed: {e}")
            raise TTSError(f"Failed to generate base64 speech: {e}")
    
    async def stream_speech(
        self,
        text: str,
        voice: str = None,
        chunk_size: int = 4096,
        **kwargs
    ) -> AsyncGenerator[bytes, None]:
        """
        Generate speech in streaming chunks (future enhancement)
        
        Note: OpenAI TTS doesn't support streaming yet, but this provides
        the interface for when it becomes available
        """
        try:
            # For now, generate full audio and yield in chunks
            audio_data = await self.generate_speech(text, voice, **kwargs)
            
            # Yield audio in chunks
            for i in range(0, len(audio_data), chunk_size):
                yield audio_data[i:i + chunk_size]
                await asyncio.sleep(0.01)  # Small delay to prevent overwhelming
                
        except Exception as e:
            logger.error(f"Streaming TTS failed: {e}")
            raise TTSError(f"Failed to stream speech: {e}")
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        return self.available_voices.copy()
    
    def get_voice_info(self) -> dict:
        """Get information about available voices"""
        return {
            "voices": self.available_voices,
            "default": self.default_voice,
            "descriptions": {
                "alloy": "Neutral, balanced voice",
                "echo": "Male voice with clear pronunciation", 
                "fable": "British accent, articulate",
                "onyx": "Deep, authoritative male voice",
                "nova": "Young, energetic female voice",
                "shimmer": "Soft, gentle female voice"
            }
        }
    
    async def test_tts_connection(self) -> bool:
        """Test TTS service connectivity"""
        try:
            if not self.api_available:
                return False
            test_text = "Hello, this is a TTS connection test."
            audio_data = await self.generate_speech(test_text)
            return len(audio_data) > 0
        except Exception as e:
            logger.error(f"TTS connection test failed: {e}")
            return False
    
    def estimate_audio_duration(self, text: str, speed: float = 1.0) -> float:
        """
        Estimate audio duration in seconds based on text length
        
        Rough estimate: ~150 words per minute at normal speed
        """
        words = len(text.split())
        base_duration = (words / 150) * 60  # Convert to seconds
        adjusted_duration = base_duration / speed
        return round(adjusted_duration, 1)

class TTSError(Exception):
    """Custom exception for TTS-related errors"""
    pass 