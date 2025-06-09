from typing import Dict, Any, Optional
import logging

from app.conversation.dialogue_engine import DialogueEngine
from app.conversation.state import ConversationStateManager

logger = logging.getLogger(__name__)

class ConversationService:
    """Service layer for conversation management"""
    
    def __init__(self):
        self.dialogue_engine = DialogueEngine()
        # Use the same state manager instance as the dialogue engine
        self.state_manager = self.dialogue_engine.state_manager
    
    async def start_conversation(self, session_id: str, user_id: str, lesson_id: str) -> Dict[str, Any]:
        """Initialize a new conversation"""
        try:
            # Create conversation state
            state = await self.state_manager.get_or_create_state(session_id, user_id, lesson_id)
            
            # Initialize response generator
            await self.dialogue_engine.response_generator.initialize()
            
            return {
                "status": "started",
                "session_id": session_id,
                "engagement_level": state.engagement_level.value,
                "learning_mode": state.learning_mode.value,
                "current_topic": state.current_topic,
                "message": "Hello! I'm your AI tutor. What would you like to learn about today?"
            }
            
        except Exception as e:
            logger.error(f"Error starting conversation for session {session_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Sorry, I had trouble starting our conversation. Please try again."
            }
    
    async def process_message(self, session_id: str, message: str, message_type: str = "text", 
                            metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a message through the conversation engine"""
        try:
            # Process through dialogue engine
            result = await self.dialogue_engine.process_input(
                session_id=session_id,
                user_input=message,
                input_type=message_type,
                metadata=metadata
            )
            
            if "error" in result:
                return {
                    "status": "error",
                    "error": result.get("error"),
                    "message": "I'm having trouble understanding right now. Could you try rephrasing that?"
                }
            
            return {
                "status": "success",
                "message": result["response"],
                "confidence": result.get("confidence", 0.8),
                "response_type": result.get("response_type", "tutorial"),
                "engagement_level": result.get("engagement_level"),
                "learning_progress": result.get("learning_progress", {}),
                "suggestions": result.get("suggestions", []),
                "processing_time_ms": result.get("processing_time_ms", 0)
            }
            
        except Exception as e:
            logger.error(f"Error processing message for session {session_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "I encountered an error while processing your message. Please try again."
            }
    
    async def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get conversation summary and learning progress"""
        try:
            summary = await self.dialogue_engine.get_session_summary(session_id)
            
            if "error" in summary:
                return {
                    "status": "error",
                    "error": summary["error"]
                }
            
            return {
                "status": "success",
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation summary for session {session_id}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def end_conversation(self, session_id: str) -> Dict[str, Any]:
        """End conversation and persist final state"""
        try:
            # Get final summary
            summary = await self.get_conversation_summary(session_id)
            
            # Persist final state
            await self.state_manager.persist_state(session_id)
            
            return {
                "status": "ended",
                "summary": summary.get("summary", {}),
                "message": "Thanks for learning with me today! I hope our conversation was helpful."
            }
            
        except Exception as e:
            logger.error(f"Error ending conversation for session {session_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "There was an error ending our conversation, but your progress has been saved."
            } 