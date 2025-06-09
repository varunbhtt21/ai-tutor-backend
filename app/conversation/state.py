from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class LearningMode(Enum):
    """Different learning modes for the tutoring session"""
    EXPLORATORY = "exploratory"  # Free-form learning, following student interest
    FOCUSED = "focused"          # Structured lesson on specific topic
    REVIEW = "review"            # Reviewing previously learned concepts
    ASSESSMENT = "assessment"    # Testing understanding

class EngagementLevel(Enum):
    """Student engagement levels"""
    HIGH = "high"               # Active, asking questions, engaged
    MEDIUM = "medium"           # Normal participation
    LOW = "low"                 # Minimal responses, short answers
    DISENGAGED = "disengaged"   # Not responding or showing confusion

@dataclass
class ConversationState:
    """Core conversation state for AI Tutor sessions"""
    
    # Session Information
    session_id: str
    user_id: str
    lesson_id: str
    
    # Current Context
    current_topic: Optional[str] = None
    learning_mode: LearningMode = LearningMode.EXPLORATORY
    engagement_level: EngagementLevel = EngagementLevel.MEDIUM
    difficulty_level: float = 0.5  # 0.0 = easy, 1.0 = hard
    
    # Conversation Flow
    conversation_turns: int = 0
    last_user_input: Optional[str] = None
    last_ai_response: Optional[str] = None
    response_time_avg: float = 0.0
    
    # Learning Progress
    concepts_discussed: List[str] = field(default_factory=list)
    questions_asked: int = 0
    correct_answers: int = 0
    misconceptions: List[str] = field(default_factory=list)
    
    # Context Memory
    short_term_memory: List[Dict[str, Any]] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    session_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    session_start: datetime = field(default_factory=datetime.utcnow)
    last_interaction: datetime = field(default_factory=datetime.utcnow)
    
    def update_engagement(self, response_time: float, message_length: int):
        """Update engagement level based on interaction patterns"""
        # Quick responses with longer messages = high engagement
        if response_time < 5.0 and message_length > 20:
            self.engagement_level = EngagementLevel.HIGH
        # Very slow responses or very short messages = low engagement
        elif response_time > 30.0 or message_length < 5:
            self.engagement_level = EngagementLevel.LOW
        # Single word responses or "yes/no" = disengaged
        elif message_length < 3:
            self.engagement_level = EngagementLevel.DISENGAGED
        else:
            self.engagement_level = EngagementLevel.MEDIUM
            
        logger.info(f"Updated engagement for session {self.session_id}: {self.engagement_level.value}")
    
    def add_concept(self, concept: str, understood: bool):
        """Track concept learning progress"""
        if concept not in self.concepts_discussed:
            self.concepts_discussed.append(concept)
            
        if not understood and concept not in self.misconceptions:
            self.misconceptions.append(concept)
            
        logger.info(f"Added concept '{concept}' to session {self.session_id}, understood: {understood}")
    
    def update_difficulty(self, performance_score: float):
        """Adjust difficulty based on performance (0.0 = all wrong, 1.0 = all right)"""
        if performance_score > 0.8:
            # Increase difficulty if doing well
            self.difficulty_level = min(1.0, self.difficulty_level + 0.1)
        elif performance_score < 0.3:
            # Decrease difficulty if struggling
            self.difficulty_level = max(0.0, self.difficulty_level - 0.1)
            
        logger.info(f"Updated difficulty for session {self.session_id}: {self.difficulty_level}")
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Return condensed context for LLM prompting"""
        return {
            "current_topic": self.current_topic,
            "learning_mode": self.learning_mode.value,
            "engagement_level": self.engagement_level.value,
            "difficulty_level": self.difficulty_level,
            "conversation_turns": self.conversation_turns,
            "concepts_discussed": self.concepts_discussed[-5:],  # Last 5 concepts
            "recent_misconceptions": self.misconceptions[-3:],   # Last 3 misconceptions
            "session_duration_minutes": (self.last_interaction - self.session_start).seconds / 60
        }

class ConversationStateManager:
    """Manages conversation states across sessions"""
    
    def __init__(self):
        self.active_states: Dict[str, ConversationState] = {}
    
    async def get_or_create_state(self, session_id: str, user_id: str, lesson_id: str) -> ConversationState:
        """Load existing state or create new one"""
        if session_id in self.active_states:
            return self.active_states[session_id]
            
        # Create new conversation state
        state = ConversationState(
            session_id=session_id,
            user_id=user_id,
            lesson_id=lesson_id
        )
        
        # TODO: Load user preferences from database
        state.user_preferences = await self._load_user_preferences(user_id)
        
        # TODO: Load any existing conversation context from database
        
        self.active_states[session_id] = state
        logger.info(f"Created new conversation state for session {session_id}")
        
        return state
    
    async def get_state(self, session_id: str) -> Optional[ConversationState]:
        """Get existing conversation state"""
        return self.active_states.get(session_id)
    
    async def update_state(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update conversation state with new data"""
        if session_id not in self.active_states:
            return False
            
        state = self.active_states[session_id]
        
        # Update specific fields
        for key, value in updates.items():
            if hasattr(state, key):
                setattr(state, key, value)
                
        state.last_interaction = datetime.utcnow()
        logger.info(f"Updated conversation state for session {session_id}")
        return True
    
    async def persist_state(self, session_id: str):
        """Save conversation state to database"""
        if session_id not in self.active_states:
            return False
            
        state = self.active_states[session_id]
        
        # TODO: Save state to database
        # This will be implemented when we add database models
        logger.info(f"Persisted conversation state for session {session_id}")
        return True
    
    async def cleanup_inactive_states(self, max_age_hours: int = 2):
        """Clean up old/inactive conversation states"""
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_id, state in self.active_states.items():
            age = (now - state.last_interaction).total_seconds() / 3600
            if age > max_age_hours:
                expired_sessions.append(session_id)
                
        for session_id in expired_sessions:
            await self.persist_state(session_id)  # Save before cleanup
            del self.active_states[session_id]
            logger.info(f"Cleaned up expired session {session_id}")
            
        return len(expired_sessions)
    
    async def _load_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Load user preferences from database"""
        # TODO: Implement database loading
        # For now, return default preferences
        return {
            "learning_style": "visual",  # visual, auditory, kinesthetic
            "explanation_detail": "medium",  # brief, medium, detailed
            "preferred_examples": "real_world",  # abstract, real_world, mathematical
            "pace": "normal"  # slow, normal, fast
        } 