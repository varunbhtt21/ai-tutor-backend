from typing import Dict, Any, Optional, Tuple, List
import asyncio
import logging
import time
from datetime import datetime

from app.conversation.state import ConversationState, ConversationStateManager, LearningMode, EngagementLevel
from app.conversation.context_manager import ContextManager
from app.conversation.response_generator import ResponseGenerator

logger = logging.getLogger(__name__)

class DialogueEngine:
    """Core dialogue processing engine for AI Tutor"""
    
    def __init__(self):
        self.state_manager = ConversationStateManager()
        self.context_manager = ContextManager()
        self.response_generator = ResponseGenerator()
        
    async def process_input(self, session_id: str, user_input: str, input_type: str = "text", 
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process user input and generate intelligent response"""
        
        start_time = time.time()
        
        # Get conversation state
        state = await self.state_manager.get_state(session_id)
        if not state:
            logger.error(f"No conversation state found for session {session_id}")
            return {"error": "Session not found"}
        
        try:
            # Update conversation metrics
            state.conversation_turns += 1
            state.last_user_input = user_input
            state.last_interaction = datetime.utcnow()
            
            # Analyze input and update context
            input_analysis = await self.analyze_input(user_input, state, metadata)
            
            # Get relevant context for response generation
            relevant_context = self.context_manager.get_relevant_context(state, user_input)
            
            # Generate contextual response
            response_data = await self.response_generator.generate_response(
                user_input=user_input,
                state=state,
                context=relevant_context,
                analysis=input_analysis
            )
            
            # Update conversation state based on interaction
            await self.update_conversation_state(state, user_input, response_data, input_analysis)
            
            # Add interaction to memory
            self.context_manager.add_to_memory(state, {
                "user_input": user_input,
                "ai_response": response_data["text"],
                "type": input_type,
                "concepts": response_data.get("detected_concepts", []),
                "sentiment": input_analysis.get("emotional_state", {}).get("sentiment", "neutral")
            })
            
            # Persist state changes
            await self.state_manager.persist_state(session_id)
            
            processing_time = (time.time() - start_time) * 1000  # milliseconds
            
            # Build response
            return {
                "response": response_data["text"],
                "confidence": response_data.get("confidence", 0.8),
                "response_type": response_data.get("response_type", "tutorial"),
                "processing_time_ms": processing_time,
                "engagement_level": state.engagement_level.value,
                "learning_progress": {
                    "concepts_discussed": len(state.concepts_discussed),
                    "questions_asked": state.questions_asked,
                    "difficulty_level": state.difficulty_level,
                    "session_duration_minutes": (state.last_interaction - state.session_start).seconds / 60
                },
                "suggestions": response_data.get("suggestions", []),
                "emotional_state": input_analysis.get("emotional_state", {}),
                "learning_patterns": input_analysis.get("learning_patterns", {})
            }
            
        except Exception as e:
            logger.error(f"Error processing input for session {session_id}: {e}")
            return {"error": "Failed to process input", "details": str(e)}
    
    async def analyze_input(self, user_input: str, state: ConversationState, 
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze user input for intent, emotion, learning signals"""
        
        analysis = {}
        
        # Detect emotional state
        response_time = metadata.get("response_time", 5.0) if metadata else 5.0
        emotional_state = self.context_manager.detect_emotional_state(user_input, response_time)
        analysis["emotional_state"] = emotional_state
        
        # Analyze learning patterns
        learning_patterns = self.context_manager.analyze_learning_patterns(state)
        analysis["learning_patterns"] = learning_patterns
        
        # Detect intent (simplified)
        intent = self._detect_intent(user_input)
        analysis["intent"] = intent
        
        # Detect concepts mentioned
        concepts = self._extract_concepts(user_input)
        analysis["concepts"] = concepts
        
        # Assess understanding level
        understanding = self._assess_understanding(user_input, state)
        analysis["understanding_level"] = understanding
        
        logger.info(f"Input analysis for session {state.session_id}: {analysis}")
        return analysis
    
    async def update_conversation_state(self, state: ConversationState, user_input: str, 
                                      response_data: Dict[str, Any], analysis: Dict[str, Any]):
        """Update conversation state based on interaction"""
        
        # Update engagement level based on analysis
        emotional_state = analysis.get("emotional_state", {})
        if emotional_state.get("frustration_level") == "high":
            state.engagement_level = EngagementLevel.LOW
        elif emotional_state.get("excitement_level") == "high":
            state.engagement_level = EngagementLevel.HIGH
        else:
            # Update based on response patterns
            message_length = len(user_input)
            response_time = 5.0  # Default, could be provided via metadata
            state.update_engagement(response_time, message_length)
        
        # Track concepts
        detected_concepts = response_data.get("detected_concepts", [])
        understanding_level = analysis.get("understanding_level", 0.5)
        
        for concept in detected_concepts:
            understood = understanding_level > 0.6  # Threshold for understanding
            state.add_concept(concept, understood)
        
        # Update difficulty based on performance
        if analysis.get("intent") == "question" and emotional_state.get("confidence") == "low":
            # Student asking questions with low confidence - might need easier content
            state.update_difficulty(0.2)
        elif emotional_state.get("confidence") == "high" and understanding_level > 0.8:
            # Student confident and understanding well - can increase difficulty
            state.update_difficulty(0.9)
        
        # Count questions
        if "?" in user_input:
            state.questions_asked += 1
        
        # Update topic if new topic detected
        intent = analysis.get("intent", {})
        if intent.get("type") == "topic_change" and intent.get("topic"):
            state.current_topic = intent["topic"]
            logger.info(f"Updated topic for session {state.session_id}: {state.current_topic}")
        
        # Update learning mode based on patterns
        patterns = analysis.get("learning_patterns", {})
        if patterns.get("question_frequency", 0) > 0.5:
            state.learning_mode = LearningMode.EXPLORATORY
        elif patterns.get("confusion_indicators", 0) > 2:
            state.learning_mode = LearningMode.REVIEW
    
    def _detect_intent(self, user_input: str) -> Dict[str, Any]:
        """Detect user intent from input (simplified approach)"""
        
        user_lower = user_input.lower()
        intent = {"type": "statement", "confidence": 0.5}
        
        # Question intent
        if "?" in user_input:
            question_words = ["what", "how", "why", "when", "where", "who", "which"]
            if any(word in user_lower for word in question_words):
                intent = {"type": "question", "confidence": 0.9}
            else:
                intent = {"type": "clarification", "confidence": 0.7}
        
        # Confusion/help intent
        elif any(word in user_lower for word in ["confused", "don't understand", "help", "stuck"]):
            intent = {"type": "help_request", "confidence": 0.9}
        
        # Agreement/understanding intent
        elif any(word in user_lower for word in ["yes", "ok", "understand", "got it", "makes sense"]):
            intent = {"type": "agreement", "confidence": 0.8}
        
        # Disagreement/correction intent
        elif any(word in user_lower for word in ["no", "wrong", "incorrect", "disagree"]):
            intent = {"type": "disagreement", "confidence": 0.8}
        
        # Topic change intent (very basic)
        topic_indicators = ["about", "learn", "study", "tell me", "explain"]
        if any(indicator in user_lower for indicator in topic_indicators):
            intent = {"type": "topic_change", "confidence": 0.6}
            # Try to extract potential topic (very simplified)
            words = user_input.split()
            for i, word in enumerate(words):
                if word.lower() in topic_indicators and i < len(words) - 1:
                    potential_topic = " ".join(words[i+1:i+3])  # Next 1-2 words
                    intent["topic"] = potential_topic
                    break
        
        return intent
    
    def _extract_concepts(self, user_input: str) -> List[str]:
        """Extract potential concepts from user input (simplified)"""
        
        # This is a very basic approach - in a real system, you'd use NLP
        # to identify domain-specific concepts
        
        concepts = []
        user_lower = user_input.lower()
        
        # Math concepts
        math_concepts = {
            "fraction": ["fraction", "fractions"],
            "algebra": ["algebra", "variable", "equation"],
            "geometry": ["triangle", "circle", "angle", "geometry"],
            "calculus": ["derivative", "integral", "calculus"],
            "statistics": ["average", "mean", "median", "statistics"]
        }
        
        # Science concepts
        science_concepts = {
            "physics": ["force", "energy", "momentum", "physics"],
            "chemistry": ["atom", "molecule", "reaction", "chemistry"],
            "biology": ["cell", "DNA", "evolution", "biology"]
        }
        
        # Check for concept matches
        all_concepts = {**math_concepts, **science_concepts}
        
        for concept_name, keywords in all_concepts.items():
            if any(keyword in user_lower for keyword in keywords):
                concepts.append(concept_name)
        
        return concepts
    
    def _assess_understanding(self, user_input: str, state: ConversationState) -> float:
        """Assess user's understanding level from their input (0.0 to 1.0)"""
        
        user_lower = user_input.lower()
        understanding_score = 0.5  # Default neutral
        
        # High understanding indicators
        high_understanding = ["understand", "clear", "makes sense", "got it", "yes", "correct"]
        if any(phrase in user_lower for phrase in high_understanding):
            understanding_score += 0.3
        
        # Low understanding indicators
        low_understanding = ["confused", "don't understand", "unclear", "difficult", "hard"]
        if any(phrase in user_lower for phrase in low_understanding):
            understanding_score -= 0.3
        
        # Question indicators (neutral to slightly negative)
        if "?" in user_input:
            understanding_score -= 0.1
        
        # Length and complexity of response (longer, more detailed = better understanding)
        if len(user_input) > 50:
            understanding_score += 0.1
        elif len(user_input) < 10:
            understanding_score -= 0.2
        
        # Use of domain-specific terms (indicates engagement with material)
        concepts = self._extract_concepts(user_input)
        if concepts:
            understanding_score += 0.2
        
        # Clamp between 0 and 1
        return max(0.0, min(1.0, understanding_score))
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        
        state = await self.state_manager.get_state(session_id)
        if not state:
            return {"error": "Session not found"}
        
        patterns = self.context_manager.analyze_learning_patterns(state)
        
        return {
            "session_id": session_id,
            "duration_minutes": (state.last_interaction - state.session_start).seconds / 60,
            "conversation_turns": state.conversation_turns,
            "current_topic": state.current_topic,
            "learning_mode": state.learning_mode.value,
            "engagement_level": state.engagement_level.value,
            "difficulty_level": state.difficulty_level,
            "concepts_discussed": state.concepts_discussed,
            "questions_asked": state.questions_asked,
            "misconceptions": state.misconceptions,
            "learning_patterns": patterns,
            "user_preferences": state.user_preferences
        } 