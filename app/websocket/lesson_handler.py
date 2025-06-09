from fastapi import WebSocket, WebSocketDisconnect
import json
import uuid
import logging
import time
from typing import Any, Dict
from app.websocket.connection_manager import ConnectionManager
from app.services.audio_service import AudioService
from app.services.session_service import SessionService
from app.services.conversation_service import ConversationService
from app.services.tts_service import TTSService, TTSError

logger = logging.getLogger(__name__)

# Global instances
manager = ConnectionManager()
audio_service = AudioService()
session_service = SessionService()
conversation_service = ConversationService()
tts_service = TTSService()

async def generate_audio_response(
    session_id: str, 
    text_response: str, 
    session_data: dict = None
) -> dict:
    """Generate audio response using TTS service"""
    try:
        # Get session audio preferences
        audio_enabled = True
        preferred_voice = "alloy"
        speech_rate = 1.0
        audio_format = "mp3"
        
        if session_data:
            audio_enabled = session_data.get("audio_enabled", True)
            preferred_voice = session_data.get("preferred_voice", "alloy")
            speech_rate = session_data.get("speech_rate", 1.0)
            audio_format = session_data.get("audio_format", "mp3")
        
        if not audio_enabled:
            return {
                "has_audio": False,
                "audio_data": None,
                "audio_format": None,
                "duration_estimate": 0
            }
        
        # Generate TTS audio
        audio_base64 = await tts_service.generate_speech_base64(
            text=text_response,
            voice=preferred_voice,
            speed=speech_rate,
            response_format=audio_format
        )
        
        # Estimate duration
        duration_estimate = tts_service.estimate_audio_duration(text_response, speech_rate)
        
        return {
            "has_audio": True,
            "audio_data": audio_base64,
            "audio_format": audio_format,
            "voice": preferred_voice,
            "speech_rate": speech_rate,
            "duration_estimate": duration_estimate
        }
        
    except TTSError as e:
        logger.error(f"TTS generation failed for session {session_id}: {e}")
        return {
            "has_audio": False,
            "audio_data": None,
            "audio_format": None,
            "tts_error": str(e),
            "duration_estimate": 0
        }
    except Exception as e:
        logger.error(f"Unexpected error generating audio for session {session_id}: {e}")
        return {
            "has_audio": False,
            "audio_data": None,
            "audio_format": None,
            "error": str(e),
            "duration_estimate": 0
        }

async def lesson_websocket_endpoint(
    websocket: WebSocket, 
    session_id: str
):
    """Main WebSocket endpoint for lesson interactions"""
    client_id = str(uuid.uuid4())
    
    try:
        # Accept connection
        await manager.connect(websocket, session_id, client_id)
        
        # Initialize session if it doesn't exist
        session_data = await session_service.get_session(session_id)
        if not session_data:
            session_data = await session_service.create_session(
                session_id=session_id,
                user_id="test_user",  # TODO: Get from authentication
                lesson_id="default_lesson"  # TODO: Get from request
            )
            
        # Initialize conversation
        conversation_result = await conversation_service.start_conversation(
            session_id=session_id,
            user_id="test_user", 
            lesson_id="default_lesson"
        )
            
        # Send connection confirmation with conversation greeting
        greeting_message = conversation_result.get("message", "Connected to AI Tutor")
        await manager.send_personal_message(client_id, {
            "type": "connection_established",
            "session_id": session_id,
            "client_id": client_id,
            "message": greeting_message,
            "conversation_status": conversation_result.get("status", "started"),
            "engagement_level": conversation_result.get("engagement_level", "medium"),
            "learning_mode": conversation_result.get("learning_mode", "exploratory")
        })
        
        # Initialize Whisper API if not already ready
        if not audio_service.model_ready:
            await manager.send_personal_message(client_id, {
                "type": "status",
                "message": "Initializing AI transcription..."
            })
            await audio_service.initialize_whisper()
            
            if audio_service.model_ready:
                await manager.send_personal_message(client_id, {
                    "type": "status", 
                    "message": "AI transcription ready!"
                })
            else:
                await manager.send_personal_message(client_id, {
                    "type": "status", 
                    "message": "AI transcription unavailable (missing API key). Text mode only."
                })
        
        # Main message loop
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await handle_message(session_id, client_id, message)
            
    except WebSocketDisconnect:
        manager.disconnect(session_id, client_id)
        audio_service.clear_buffer(session_id)
        
        # Update session status if no more connections
        if not manager.is_session_active(session_id):
            await session_service.update_session(session_id, {"status": "paused"})
            
        logger.info(f"Client {client_id} disconnected from session {session_id}")
        
    except Exception as e:
        logger.error(f"Error in WebSocket connection {client_id}: {e}")
        await manager.send_personal_message(client_id, {
            "type": "error",
            "message": f"Connection error: {str(e)}"
        })

async def handle_message(session_id: str, client_id: str, message: Dict[str, Any]):
    """Handle incoming WebSocket messages"""
    message_type = message.get("type")
    
    try:
        if message_type == "audio":
            await handle_audio_message(session_id, client_id, message)
            
        elif message_type == "text":
            await handle_text_message(session_id, client_id, message)
            
        elif message_type == "control":
            await handle_control_message(session_id, client_id, message)
            
        else:
            await manager.send_personal_message(client_id, {
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            })
            
    except Exception as e:
        logger.error(f"Error handling message type {message_type}: {e}")
        await manager.send_personal_message(client_id, {
            "type": "error",
            "message": f"Error processing message: {str(e)}"
        })

async def handle_audio_message(session_id: str, client_id: str, message: Dict[str, Any]):
    """Handle audio data from client"""
    audio_data = message.get("data")
    if not audio_data:
        return
        
    start_time = time.time()
    
    # Get session data for audio preferences
    session_data = await session_service.get_session(session_id)
    
    # Process audio through Whisper
    transcribed_text = await audio_service.process_base64_audio(session_id, audio_data)
    
    if transcribed_text:
        processing_time = (time.time() - start_time) * 1000  # milliseconds
        
        # Process through conversation engine
        conversation_result = await conversation_service.process_message(
            session_id=session_id,
            message=transcribed_text,
            message_type="audio",
            metadata={"response_time": processing_time / 1000}
        )
        
        if conversation_result.get("status") == "success":
            ai_response = conversation_result["message"]
            
            # Generate audio response
            audio_response = await generate_audio_response(
                session_id=session_id,
                text_response=ai_response,
                session_data=session_data
            )
            
            # Log the interaction
            await session_service.log_interaction(
                session_id=session_id,
                user_input=transcribed_text,
                ai_response=ai_response,
                response_latency=processing_time,
                confidence_score=conversation_result.get("confidence", 0.8)
            )
            
            # Send intelligent response with audio back to client
            response_message = {
                "type": "audio_response",
                "user_input": transcribed_text,
                "ai_response": ai_response,
                "processing_time_ms": processing_time,
                "conversation_processing_time_ms": conversation_result.get("processing_time_ms", 0),
                "confidence": conversation_result.get("confidence", 0.8),
                "response_type": conversation_result.get("response_type", "tutorial"),
                "engagement_level": conversation_result.get("engagement_level", "medium"),
                "learning_progress": conversation_result.get("learning_progress", {}),
                "suggestions": conversation_result.get("suggestions", []),
                "buffer_info": audio_service.get_buffer_info(session_id),
                **audio_response  # Include audio data
            }
            
            await manager.send_personal_message(client_id, response_message)
        else:
            # Fallback to simple echo if conversation engine fails
            echo_response = f"I heard: {transcribed_text}"
            
            # Generate audio for fallback response
            audio_response = await generate_audio_response(
                session_id=session_id,
                text_response=echo_response,
                session_data=session_data
            )
            
            fallback_message = {
                "type": "audio_response",
                "user_input": transcribed_text,
                "ai_response": echo_response,
                "processing_time_ms": processing_time,
                "error": conversation_result.get("error", "Conversation processing failed"),
                "buffer_info": audio_service.get_buffer_info(session_id),
                **audio_response  # Include audio data
            }
            
            await manager.send_personal_message(client_id, fallback_message)
        
        logger.info(f"Processed audio for session {session_id}: '{transcribed_text}' in {processing_time:.1f}ms")

async def handle_text_message(session_id: str, client_id: str, message: Dict[str, Any]):
    """Handle text input from client"""
    text_input = message.get("text", "")
    
    if text_input:
        start_time = time.time()
        
        # Get session data for audio preferences
        session_data = await session_service.get_session(session_id)
        
        # Process through conversation engine
        conversation_result = await conversation_service.process_message(
            session_id=session_id,
            message=text_input,
            message_type="text",
            metadata={}
        )
        
        if conversation_result.get("status") == "success":
            ai_response = conversation_result["message"]
            processing_time = (time.time() - start_time) * 1000  # milliseconds
            
            # Generate audio response
            audio_response = await generate_audio_response(
                session_id=session_id,
                text_response=ai_response,
                session_data=session_data
            )
            
            # Log the interaction
            await session_service.log_interaction(
                session_id=session_id,
                user_input=text_input,
                ai_response=ai_response,
                response_latency=processing_time,
                confidence_score=conversation_result.get("confidence", 0.8)
            )
            
            # Send intelligent response with audio back to client
            response_message = {
                "type": "text_response",
                "user_input": text_input,
                "ai_response": ai_response,
                "processing_time_ms": processing_time,
                "confidence": conversation_result.get("confidence", 0.8),
                "response_type": conversation_result.get("response_type", "tutorial"),
                "engagement_level": conversation_result.get("engagement_level", "medium"),
                "learning_progress": conversation_result.get("learning_progress", {}),
                "suggestions": conversation_result.get("suggestions", []),
                "recommendations": conversation_result.get("recommendations", []),
                "curriculum_guidance": conversation_result.get("curriculum_guidance", []),
                "emotional_state": conversation_result.get("emotional_state", {}),
                **audio_response  # Include audio data
            }
            
            await manager.send_personal_message(client_id, response_message)
        else:
            # Send error response
            await manager.send_personal_message(client_id, {
                "type": "error",
                "message": f"Error processing text: {conversation_result.get('error', 'Unknown error')}"
            })
        
        logger.info(f"Processed text for session {session_id}: '{text_input}' in {(time.time() - start_time) * 1000:.1f}ms")

async def handle_control_message(session_id: str, client_id: str, message: Dict[str, Any]):
    """Handle control messages (start, stop, reset, etc.)"""
    command = message.get("command")
    
    if command == "clear_audio_buffer":
        audio_service.clear_buffer(session_id)
        await manager.send_personal_message(client_id, {
            "type": "status",
            "message": "Audio buffer cleared"
        })
        
    elif command == "get_session_info":
        session_data = await session_service.get_session(session_id)
        await manager.send_personal_message(client_id, {
            "type": "session_info",
            "session": session_data,
            "buffer_info": audio_service.get_buffer_info(session_id)
        })
        
    elif command == "ping":
        await manager.send_personal_message(client_id, {
            "type": "pong",
            "timestamp": time.time()
        })
        
    elif command == "get_conversation_summary":
        summary_result = await conversation_service.get_conversation_summary(session_id)
        await manager.send_personal_message(client_id, {
            "type": "conversation_summary",
            "summary": summary_result
        })
        
    elif command == "end_conversation":
        end_result = await conversation_service.end_conversation(session_id)
        await manager.send_personal_message(client_id, {
            "type": "conversation_ended",
            "result": end_result
        })
        
    else:
        await manager.send_personal_message(client_id, {
            "type": "error",
            "message": f"Unknown command: {command}"
        }) 