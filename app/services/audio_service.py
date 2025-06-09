import openai
import io
import asyncio
import logging
from typing import Optional, Dict, Any
import base64
import wave
import tempfile
import os

logger = logging.getLogger(__name__)

class AudioService:
    """Service for processing audio with OpenAI Whisper API"""
    
    def __init__(self):
        self.client = None
        self.audio_buffers: Dict[str, bytearray] = {}  # session_id -> audio buffer
        self.buffer_thresholds = {
            "min_duration": 1.0,  # Minimum 1 second before processing
            "max_buffer_size": 1024 * 1024 * 5  # 5MB max buffer
        }
        self.model_ready = False
        
    async def initialize_whisper(self, model_size: str = "whisper-1"):
        """Initialize OpenAI Whisper API client"""
        try:
            # Check if API key is available
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY not found. Audio transcription will be disabled.")
                self.model_ready = False
                return
                
            logger.info("Initializing OpenAI Whisper API...")
            self.client = openai.OpenAI(api_key=api_key)
            
            # Test API connection with a simple call (optional)
            # We'll skip this for now to avoid unnecessary API calls
            self.model_ready = True
            logger.info("OpenAI Whisper API ready")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI API: {e}")
            self.model_ready = False
        
    async def add_audio_chunk(self, session_id: str, audio_data: bytes) -> Optional[str]:
        """
        Add audio chunk to buffer and process if ready
        Returns transcribed text if buffer is ready, None otherwise
        """
        if session_id not in self.audio_buffers:
            self.audio_buffers[session_id] = bytearray()
            
        self.audio_buffers[session_id].extend(audio_data)
        
        # Check if buffer is ready for processing
        buffer_size = len(self.audio_buffers[session_id])
        
        # Process if we have enough data or buffer is getting too large
        if (buffer_size >= 16000 * 2 * self.buffer_thresholds["min_duration"] or  # ~1 second of 16kHz 16-bit audio
            buffer_size >= self.buffer_thresholds["max_buffer_size"]):
            
            result = await self.process_buffer(session_id)
            return result
            
        return None
        
    async def process_buffer(self, session_id: str) -> str:
        """Process the audio buffer for a session"""
        if session_id not in self.audio_buffers or not self.audio_buffers[session_id]:
            return ""
            
        audio_bytes = bytes(self.audio_buffers[session_id])
        self.audio_buffers[session_id] = bytearray()  # Clear buffer
        
        try:
            result = await self.transcribe_audio(audio_bytes)
            logger.info(f"Transcribed audio for session {session_id}: {result[:50]}...")
            return result
        except Exception as e:
            logger.error(f"Error transcribing audio for session {session_id}: {e}")
            return ""
            
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio bytes using OpenAI Whisper API"""
        if not self.model_ready:
            await self.initialize_whisper()
            
        if not self.model_ready or not self.client:
            logger.warning("OpenAI Whisper not available. Returning placeholder text.")
            return "[Audio transcription not available - Please set OPENAI_API_KEY]"
            
        try:
            # Create temporary wav file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
                
                # Write audio data as WAV file
                with wave.open(temp_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(16000)  # 16kHz
                    wav_file.writeframes(audio_data)
                    
            def transcribe():
                try:
                    with open(temp_path, "rb") as audio_file:
                        response = self.client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            response_format="text"
                        )
                    return response.strip()
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        
            # Run API call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, transcribe)
            
            return text
            
        except Exception as e:
            logger.error(f"Error in transcribe_audio: {e}")
            return ""
            
    async def process_base64_audio(self, session_id: str, base64_audio: str) -> Optional[str]:
        """Process base64 encoded audio data"""
        try:
            audio_bytes = base64.b64decode(base64_audio)
            return await self.add_audio_chunk(session_id, audio_bytes)
        except Exception as e:
            logger.error(f"Error processing base64 audio: {e}")
            return None
            
    def clear_buffer(self, session_id: str):
        """Clear audio buffer for session"""
        if session_id in self.audio_buffers:
            del self.audio_buffers[session_id]
            logger.info(f"Cleared audio buffer for session {session_id}")
            
    def get_buffer_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about session's audio buffer"""
        if session_id not in self.audio_buffers:
            return {"buffer_size": 0, "duration_estimate": 0}
            
        buffer_size = len(self.audio_buffers[session_id])
        duration_estimate = buffer_size / (16000 * 2)  # 16kHz, 16-bit
        
        return {
            "buffer_size": buffer_size,
            "duration_estimate": duration_estimate
        } 