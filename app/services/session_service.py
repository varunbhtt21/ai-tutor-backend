import json
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.models.session import LearningSession, ConversationLog
from app.database import get_db

logger = logging.getLogger(__name__)

class SessionService:
    """Service for managing learning sessions"""
    
    def __init__(self):
        # In-memory session store for now (will add Redis later)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_ttl = 3600  # 1 hour
        
    async def create_session(self, session_id: str, user_id: str, lesson_id: str) -> Dict[str, Any]:
        """Create a new learning session"""
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "lesson_id": lesson_id,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": [],
            "current_node": None,
            "metadata": {}
        }
        
        self.sessions[session_id] = session_data
        
        # TODO: Store in database
        # try:
        #     db_session = LearningSession(
        #         session_id=session_id,
        #         user_id=user_id,
        #         lesson_id=lesson_id,
        #         status="active"
        #     )
        #     db.add(db_session)
        #     db.commit()
        # except Exception as e:
        #     logger.error(f"Error storing session in database: {e}")
        
        logger.info(f"Created session {session_id} for user {user_id}")
        return session_data
        
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return self.sessions.get(session_id)
        
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        if session_id not in self.sessions:
            return False
            
        self.sessions[session_id].update(updates)
        self.sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Updated session {session_id}")
        return True
        
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session {session_id}")
            return True
        return False
        
    async def add_message_to_history(self, session_id: str, message: Dict[str, Any]):
        """Add message to conversation history"""
        if session_id not in self.sessions:
            return False
            
        conversation = self.sessions[session_id].get("conversation_history", [])
        conversation.append({
            **message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 50 messages
        if len(conversation) > 50:
            conversation = conversation[-50:]
            
        self.sessions[session_id]["conversation_history"] = conversation
        
        logger.info(f"Added message to session {session_id} history")
        return True
        
    async def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for session"""
        if session_id not in self.sessions:
            return []
            
        return self.sessions[session_id].get("conversation_history", [])
        
    async def log_interaction(self, session_id: str, user_input: str, ai_response: str, 
                            audio_duration: Optional[float] = None, 
                            response_latency: Optional[float] = None,
                            confidence_score: Optional[float] = None):
        """Log interaction for metrics and analysis"""
        
        # Add to conversation history
        await self.add_message_to_history(session_id, {
            "type": "interaction",
            "user_input": user_input,
            "ai_response": ai_response,
            "audio_duration": audio_duration,
            "response_latency": response_latency,
            "confidence_score": confidence_score
        })
        
        # TODO: Store in database
        # try:
        #     log_entry = ConversationLog(
        #         session_id=session_id,
        #         user_input=user_input,
        #         ai_response=ai_response,
        #         audio_duration=audio_duration,
        #         response_latency=response_latency,
        #         confidence_score=confidence_score
        #     )
        #     db.add(log_entry)
        #     db.commit()
        # except Exception as e:
        #     logger.error(f"Error logging interaction to database: {e}")
        
        logger.info(f"Logged interaction for session {session_id}")
        
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return list(self.sessions.keys())
        
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions"""
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": [sid for sid, data in self.sessions.items() 
                              if data.get("status") == "active"]
        } 