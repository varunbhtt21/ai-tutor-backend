from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime, timedelta
import re

from app.conversation.state import ConversationState

logger = logging.getLogger(__name__)

class ContextManager:
    """Manages conversation context and memory"""
    
    def __init__(self, max_short_term_memory: int = 20):
        self.max_short_term_memory = max_short_term_memory
    
    def add_to_memory(self, state: ConversationState, interaction: Dict[str, Any]):
        """Add interaction to short-term memory"""
        memory_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_input": interaction.get("user_input", ""),
            "ai_response": interaction.get("ai_response", ""),
            "interaction_type": interaction.get("type", "text"),
            "concepts": interaction.get("concepts", []),
            "sentiment": interaction.get("sentiment", "neutral"),
            "relevance_score": 1.0  # Start with max relevance, decays over time
        }
        
        state.short_term_memory.append(memory_entry)
        
        # Prune old memories if over limit
        if len(state.short_term_memory) > self.max_short_term_memory:
            state.short_term_memory = state.short_term_memory[-self.max_short_term_memory:]
            
        logger.info(f"Added interaction to memory for session {state.session_id}")
    
    def get_relevant_context(self, state: ConversationState, query: str, max_entries: int = 5) -> List[Dict[str, Any]]:
        """Get relevant context for current query using simple keyword matching"""
        if not state.short_term_memory:
            return []
            
        # Extract keywords from query
        query_keywords = self._extract_keywords(query.lower())
        
        # Score each memory entry for relevance
        scored_memories = []
        for memory in state.short_term_memory:
            score = self._calculate_relevance_score(memory, query_keywords)
            if score > 0:
                scored_memories.append((score, memory))
        
        # Sort by relevance and return top entries
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        relevant_memories = [memory for _, memory in scored_memories[:max_entries]]
        
        logger.info(f"Found {len(relevant_memories)} relevant memories for query in session {state.session_id}")
        return relevant_memories
    
    def build_prompt_context(self, state: ConversationState, current_input: str) -> str:
        """Build context string for LLM prompt"""
        context_parts = []
        
        # Add session context
        context_summary = state.get_context_summary()
        context_parts.append(f"Session Context:")
        context_parts.append(f"- Current topic: {context_summary['current_topic'] or 'Not set'}")
        context_parts.append(f"- Learning mode: {context_summary['learning_mode']}")
        context_parts.append(f"- Engagement level: {context_summary['engagement_level']}")
        context_parts.append(f"- Difficulty level: {context_summary['difficulty_level']:.1f}/1.0")
        context_parts.append(f"- Conversation turns: {context_summary['conversation_turns']}")
        
        # Add user preferences
        if state.user_preferences:
            context_parts.append(f"\nUser Preferences:")
            for key, value in state.user_preferences.items():
                context_parts.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        # Add recent concepts
        if context_summary['concepts_discussed']:
            context_parts.append(f"\nRecent concepts discussed: {', '.join(context_summary['concepts_discussed'])}")
        
        # Add misconceptions
        if context_summary['recent_misconceptions']:
            context_parts.append(f"Recent misconceptions: {', '.join(context_summary['recent_misconceptions'])}")
        
        # Add relevant conversation history
        relevant_history = self.get_relevant_context(state, current_input, max_entries=3)
        if relevant_history:
            context_parts.append(f"\nRelevant conversation history:")
            for i, memory in enumerate(relevant_history, 1):
                user_input = memory['user_input'][:100] + "..." if len(memory['user_input']) > 100 else memory['user_input']
                ai_response = memory['ai_response'][:100] + "..." if len(memory['ai_response']) > 100 else memory['ai_response']
                context_parts.append(f"{i}. User: {user_input}")
                context_parts.append(f"   AI: {ai_response}")
        
        return "\n".join(context_parts)
    
    def analyze_learning_patterns(self, state: ConversationState) -> Dict[str, Any]:
        """Analyze user learning patterns from conversation history"""
        if not state.short_term_memory:
            return {"pattern": "insufficient_data"}
        
        patterns = {
            "response_frequency": len(state.short_term_memory),
            "avg_response_length": 0,
            "question_frequency": 0,
            "confusion_indicators": 0,
            "engagement_trend": "stable"
        }
        
        # Analyze response patterns
        total_length = 0
        question_count = 0
        confusion_words = ["confused", "don't understand", "what", "how", "help", "unclear"]
        
        for memory in state.short_term_memory:
            user_input = memory.get('user_input', '').lower()
            total_length += len(user_input)
            
            # Count questions
            if '?' in user_input:
                question_count += 1
                
            # Count confusion indicators
            for word in confusion_words:
                if word in user_input:
                    patterns["confusion_indicators"] += 1
                    break
        
        if state.short_term_memory:
            patterns["avg_response_length"] = total_length / len(state.short_term_memory)
            patterns["question_frequency"] = question_count / len(state.short_term_memory)
        
        # Determine engagement trend (simplified)
        if patterns["question_frequency"] > 0.3 and patterns["avg_response_length"] > 20:
            patterns["engagement_trend"] = "increasing"
        elif patterns["confusion_indicators"] > 2 or patterns["avg_response_length"] < 10:
            patterns["engagement_trend"] = "decreasing"
        
        logger.info(f"Analyzed learning patterns for session {state.session_id}: {patterns}")
        return patterns
    
    def detect_emotional_state(self, user_input: str, response_time: float) -> Dict[str, Any]:
        """Detect user emotional state from input patterns"""
        emotional_state = {
            "sentiment": "neutral",
            "confidence": "medium",
            "frustration_level": "low",
            "excitement_level": "medium"
        }
        
        user_input_lower = user_input.lower()
        
        # Detect frustration
        frustration_indicators = ["frustrated", "annoyed", "difficult", "hard", "don't get it", "stupid"]
        if any(word in user_input_lower for word in frustration_indicators):
            emotional_state["frustration_level"] = "high"
            emotional_state["sentiment"] = "negative"
        
        # Detect excitement/enthusiasm
        excitement_indicators = ["cool", "awesome", "great", "love", "amazing", "wow", "interesting"]
        if any(word in user_input_lower for word in excitement_indicators):
            emotional_state["excitement_level"] = "high"
            emotional_state["sentiment"] = "positive"
        
        # Detect confidence based on response patterns
        if "?" in user_input or any(word in user_input_lower for word in ["maybe", "think", "not sure"]):
            emotional_state["confidence"] = "low"
        elif any(word in user_input_lower for word in ["yes", "definitely", "sure", "understand"]):
            emotional_state["confidence"] = "high"
        
        # Factor in response time
        if response_time > 30:
            emotional_state["confidence"] = "low"
        elif response_time < 3:
            emotional_state["confidence"] = "high"
        
        return emotional_state
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove common stop words and extract meaningful terms
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "can", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "her", "its", "our", "their"}
        
        # Clean text and split into words
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _calculate_relevance_score(self, memory: Dict[str, Any], query_keywords: List[str]) -> float:
        """Calculate relevance score for a memory entry"""
        if not query_keywords:
            return 0.0
        
        # Combine text from memory entry
        memory_text = f"{memory.get('user_input', '')} {memory.get('ai_response', '')}".lower()
        memory_keywords = self._extract_keywords(memory_text)
        
        if not memory_keywords:
            return 0.0
        
        # Calculate keyword overlap
        common_keywords = set(query_keywords) & set(memory_keywords)
        keyword_score = len(common_keywords) / len(query_keywords)
        
        # Boost score for concept matches
        concepts = memory.get('concepts', [])
        concept_matches = sum(1 for concept in concepts if any(keyword in concept.lower() for keyword in query_keywords))
        concept_score = concept_matches * 0.5
        
        # Apply time decay (newer memories are more relevant)
        try:
            memory_time = datetime.fromisoformat(memory['timestamp'].replace('Z', '+00:00'))
            age_hours = (datetime.utcnow() - memory_time.replace(tzinfo=None)).total_seconds() / 3600
            time_decay = max(0.1, 1.0 - (age_hours / 24))  # Decay over 24 hours
        except:
            time_decay = 0.5  # Default if timestamp parsing fails
        
        total_score = (keyword_score + concept_score) * time_decay
        return min(1.0, total_score) 