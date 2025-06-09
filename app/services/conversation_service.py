from typing import Dict, Any, Optional
import logging
import time

from app.conversation.dialogue_engine import DialogueEngine
from app.conversation.state import ConversationStateManager
from app.services.learning_graph_service import LearningGraphService

logger = logging.getLogger(__name__)

class ConversationService:
    """Service layer for conversation management"""
    
    def __init__(self):
        self.dialogue_engine = DialogueEngine()
        # Use the same state manager instance as the dialogue engine
        self.state_manager = self.dialogue_engine.state_manager
        # Initialize learning graph service for curriculum-driven responses
        self.learning_graph = LearningGraphService()
    
    async def start_conversation(self, session_id: str, user_id: str, lesson_id: str) -> Dict[str, Any]:
        """Initialize a new conversation"""
        try:
            # Create conversation state
            state = await self.state_manager.get_or_create_state(session_id, user_id, lesson_id)
            
            # Initialize response generator
            await self.dialogue_engine.response_generator.initialize()
            
            # Check for existing learning path or get recommendations
            learning_path = await self.learning_graph.get_learning_path(session_id, user_id)
            recommendations = await self.learning_graph.get_next_recommended_concepts(
                session_id, user_id, limit=3
            )
            
            # Generate curriculum-aware greeting
            greeting_message = await self._generate_curriculum_greeting(
                learning_path, recommendations
            )
            
            return {
                "status": "started",
                "session_id": session_id,
                "engagement_level": state.engagement_level.value,
                "learning_mode": state.learning_mode.value,
                "current_topic": state.current_topic,
                "learning_path": learning_path,
                "recommendations": recommendations,
                "message": greeting_message
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
        """Process a message through the conversation engine with curriculum guidance"""
        try:
            start_time = time.time()
            
            # Get current learning context
            user_id = "test_user"  # TODO: Get from session/auth
            learning_context = await self._get_learning_context(session_id, user_id, message)
            
            # Process through dialogue engine with learning context
            result = await self.dialogue_engine.process_input(
                session_id=session_id,
                user_input=message,
                input_type=message_type,
                metadata={**(metadata or {}), "learning_context": learning_context}
            )
            
            if "error" in result:
                return {
                    "status": "error",
                    "error": result.get("error"),
                    "message": "I'm having trouble understanding right now. Could you try rephrasing that?"
                }
            
            # Update learning progress based on interaction
            progress_updates = await self._update_learning_progress(
                session_id, user_id, message, result
            )
            
            # Get next curriculum recommendations
            recommendations = await self.learning_graph.get_next_recommended_concepts(
                session_id, user_id, limit=3
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "status": "success",
                "message": result["response"],
                "confidence": result.get("confidence", 0.8),
                "response_type": result.get("response_type", "tutorial"),
                "engagement_level": result.get("engagement_level"),
                "learning_progress": progress_updates,
                "recommendations": recommendations,
                "curriculum_guidance": learning_context.get("guidance", []),
                "suggestions": result.get("suggestions", []),
                "processing_time_ms": processing_time
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
    
    async def _generate_curriculum_greeting(
        self, 
        learning_path: Optional[Dict], 
        recommendations: list
    ) -> str:
        """Generate a curriculum-aware greeting message"""
        if learning_path:
            current_position = learning_path.get("current_position", 0)
            total_concepts = len(learning_path.get("concept_sequence", []))
            completion = learning_path.get("completion_percentage", 0)
            
            return f"Welcome back! You're {completion:.0f}% through your learning path '{learning_path['name']}'. Ready to continue where we left off?"
        
        elif recommendations:
            concepts_list = [rec["name"] for rec in recommendations[:2]]
            if len(concepts_list) == 1:
                suggestion = concepts_list[0]
            else:
                suggestion = f"{concepts_list[0]} or {concepts_list[1]}"
            
            return f"Hello! I'm your AI tutor. Based on your level, I recommend starting with {suggestion}. What would you like to learn about today?"
        
        else:
            return "Hello! I'm your AI tutor. What would you like to learn about today? I can help you with Python programming concepts."
    
    async def _get_learning_context(
        self, 
        session_id: str, 
        user_id: str, 
        message: str
    ) -> Dict[str, Any]:
        """Get learning context for curriculum-guided responses"""
        try:
            # Get current learning path and position
            learning_path = await self.learning_graph.get_learning_path(session_id, user_id)
            
            # Get recommendations for next concepts
            recommendations = await self.learning_graph.get_next_recommended_concepts(
                session_id, user_id, limit=5
            )
            
            # Detect if student is asking about a specific concept
            current_concept = await self._detect_concept_from_message(message)
            
            guidance = []
            
            if learning_path and current_concept:
                # Check if current concept fits in learning path
                sequence = learning_path.get("concept_sequence", [])
                current_pos = learning_path.get("current_position", 0)
                
                if current_concept["id"] in sequence:
                    concept_index = sequence.index(current_concept["id"])
                    if concept_index > current_pos:
                        guidance.append(f"Great question about {current_concept['name']}! That's actually coming up next in your learning path.")
                    elif concept_index == current_pos:
                        guidance.append(f"Perfect! {current_concept['name']} is exactly what we should focus on right now.")
                    else:
                        guidance.append(f"Good review question about {current_concept['name']}. Let's reinforce that concept.")
            
            return {
                "learning_path": learning_path,
                "recommendations": recommendations,
                "current_concept": current_concept,
                "guidance": guidance,
                "has_structured_path": learning_path is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting learning context: {e}")
            return {
                "learning_path": None,
                "recommendations": [],
                "current_concept": None,
                "guidance": [],
                "has_structured_path": False
            }
    
    async def _detect_concept_from_message(self, message: str) -> Optional[Dict]:
        """Detect if message is asking about a specific curriculum concept"""
        message_lower = message.lower()
        
        # Simple keyword detection - could be enhanced with NLP
        concept_keywords = {
            "variable": "variables",
            "data type": "data-types",
            "list": "lists",
            "function": "functions", 
            "if": "conditionals",
            "loop": "loops",
            "for": "loops",
            "while": "loops"
        }
        
        for keyword, slug in concept_keywords.items():
            if keyword in message_lower:
                concept = await self.learning_graph.get_concept_by_slug(slug)
                return concept
        
        return None
    
    async def _update_learning_progress(
        self, 
        session_id: str, 
        user_id: str, 
        message: str,
        response_result: Dict
    ) -> Dict[str, Any]:
        """Update learning progress based on conversation interaction"""
        try:
            # Detect concept being discussed
            current_concept = await self._detect_concept_from_message(message)
            
            if not current_concept:
                return {"message": "No specific concept detected"}
            
            # Calculate mastery delta based on interaction quality
            mastery_delta = 0.1  # Base learning increment
            
            # Adjust based on student engagement and understanding
            engagement = response_result.get("engagement_level", "medium")
            if engagement == "high":
                mastery_delta *= 1.5
            elif engagement == "low":
                mastery_delta *= 0.5
            
            # Update progress
            progress_update = await self.learning_graph.update_student_progress(
                session_id=session_id,
                user_id=user_id,
                concept_id=current_concept["id"],
                mastery_delta=mastery_delta,
                time_spent_minutes=1,  # Approximate
                confidence_level=response_result.get("confidence", 0.7)
            )
            
            # Check if learning path should advance
            advancement = await self.learning_graph.advance_learning_path(session_id, user_id)
            
            return {
                "concept_progress": progress_update,
                "path_advancement": advancement,
                "concept_name": current_concept["name"]
            }
            
        except Exception as e:
            logger.error(f"Error updating learning progress: {e}")
            return {"error": str(e)} 