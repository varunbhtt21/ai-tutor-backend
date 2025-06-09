import openai
from typing import Dict, Any, List, Optional
import asyncio
import json
import logging
import os

from app.conversation.state import ConversationState, LearningMode, EngagementLevel

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """Generates contextual responses using LLM"""
    
    def __init__(self):
        self.client = None
        self.model = "gpt-4o"
        self.initialized = False
        
    async def initialize(self):
        """Initialize OpenAI client"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
                self.initialized = True
                logger.info("Response generator initialized with OpenAI")
            else:
                logger.warning("No OpenAI API key found. Using fallback responses.")
        except Exception as e:
            logger.error(f"Error initializing response generator: {e}")
        
    async def generate_response(self, user_input: str, state: ConversationState, 
                              context: List[Dict[str, Any]], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent response based on conversation context"""
        
        if not self.initialized:
            await self.initialize()
        
        if not self.client:
            return self._generate_fallback_response(user_input, state)
        
        # Build comprehensive prompt
        prompt = self.build_tutoring_prompt(user_input, state, context, analysis)
        system_prompt = self.get_system_prompt(state)
        
        try:
            def call_openai():
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                return response.choices[0].message.content
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(None, call_openai)
            
            # Determine response type and extract suggestions
            response_data = self._analyze_response(response_text, state)
            
            return {
                "text": response_text,
                "confidence": response_data.get("confidence", 0.85),
                "response_type": response_data.get("response_type", "tutorial"),
                "suggestions": response_data.get("suggestions", []),
                "detected_concepts": response_data.get("concepts", [])
            }
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            return self._generate_fallback_response(user_input, state)
    
    def get_system_prompt(self, state: ConversationState) -> str:
        """Get dynamic system prompt based on conversation state"""
        
        # Base system prompt
        base_prompt = """You are an AI tutor helping a student learn. Your role is to be:
- Patient and encouraging
- Adaptive to the student's learning style and pace
- Clear in explanations with appropriate examples
- Probing to check understanding
- Supportive when the student struggles

Key principles:
- Ask follow-up questions to ensure comprehension
- Use examples relevant to the student's interests
- Break down complex concepts into smaller parts
- Celebrate progress and provide constructive feedback
- If a student is confused, try different explanation approaches
- Encourage questions and curiosity"""

        # Add context-specific guidance
        context_guidance = []
        
        # Engagement level adjustments
        if state.engagement_level == EngagementLevel.LOW:
            context_guidance.append("The student seems less engaged. Try to spark interest with relatable examples or ask engaging questions.")
        elif state.engagement_level == EngagementLevel.HIGH:
            context_guidance.append("The student is highly engaged. You can introduce slightly more challenging concepts.")
        elif state.engagement_level == EngagementLevel.DISENGAGED:
            context_guidance.append("The student appears disengaged. Use simple, encouraging language and check if they need a break or different approach.")
        
        # Learning mode adjustments
        if state.learning_mode == LearningMode.FOCUSED:
            context_guidance.append("Stay focused on the current topic. Guide the conversation back if it drifts.")
        elif state.learning_mode == LearningMode.EXPLORATORY:
            context_guidance.append("Allow natural exploration of related topics. Follow the student's curiosity.")
        elif state.learning_mode == LearningMode.REVIEW:
            context_guidance.append("Focus on reinforcing previously learned concepts. Ask review questions.")
        elif state.learning_mode == LearningMode.ASSESSMENT:
            context_guidance.append("Evaluate understanding through targeted questions. Provide clear feedback.")
        
        # Difficulty level adjustments
        if state.difficulty_level < 0.3:
            context_guidance.append("Keep explanations simple and basic. Use concrete examples.")
        elif state.difficulty_level > 0.7:
            context_guidance.append("You can use more advanced concepts and abstract thinking.")
        
        # User preferences
        if state.user_preferences.get("learning_style") == "visual":
            context_guidance.append("Use visual descriptions, diagrams concepts, and spatial analogies.")
        elif state.user_preferences.get("learning_style") == "auditory":
            context_guidance.append("Use verbal explanations, sound analogies, and encourage discussion.")
        elif state.user_preferences.get("learning_style") == "kinesthetic":
            context_guidance.append("Suggest hands-on activities and physical analogies.")
        
        # Combine prompts
        if context_guidance:
            full_prompt = f"{base_prompt}\n\nCurrent session guidance:\n" + "\n".join(f"- {guidance}" for guidance in context_guidance)
        else:
            full_prompt = base_prompt
            
        return full_prompt
    
    def build_tutoring_prompt(self, user_input: str, state: ConversationState, 
                            context: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        """Build comprehensive prompt with context"""
        
        prompt_parts = []
        
        # Add session context
        context_summary = state.get_context_summary()
        prompt_parts.append("=== SESSION CONTEXT ===")
        prompt_parts.append(f"Current topic: {context_summary['current_topic'] or 'Open discussion'}")
        prompt_parts.append(f"Learning mode: {context_summary['learning_mode']}")
        prompt_parts.append(f"Student engagement: {context_summary['engagement_level']}")
        prompt_parts.append(f"Difficulty level: {context_summary['difficulty_level']:.1f}/1.0")
        prompt_parts.append(f"Conversation turns: {context_summary['conversation_turns']}")
        
        # Add user preferences
        if state.user_preferences:
            prompt_parts.append("\n=== STUDENT PREFERENCES ===")
            for key, value in state.user_preferences.items():
                prompt_parts.append(f"{key.replace('_', ' ').title()}: {value}")
        
        # Add learning progress
        if context_summary['concepts_discussed']:
            prompt_parts.append(f"\n=== RECENT CONCEPTS ===")
            prompt_parts.append(f"Discussed: {', '.join(context_summary['concepts_discussed'])}")
        
        if context_summary['recent_misconceptions']:
            prompt_parts.append(f"Recent misconceptions: {', '.join(context_summary['recent_misconceptions'])}")
        
        # Add relevant conversation history
        if context:
            prompt_parts.append("\n=== RELEVANT CONVERSATION HISTORY ===")
            for i, memory in enumerate(context, 1):
                prompt_parts.append(f"{i}. Student: {memory['user_input']}")
                prompt_parts.append(f"   Tutor: {memory['ai_response']}")
        
        # Add emotional/engagement analysis
        if analysis:
            prompt_parts.append("\n=== STUDENT ANALYSIS ===")
            for key, value in analysis.items():
                if key != "concepts":  # Skip concepts as they're handled separately
                    prompt_parts.append(f"{key.replace('_', ' ').title()}: {value}")
        
        # Add current student input
        prompt_parts.append("\n=== CURRENT STUDENT INPUT ===")
        prompt_parts.append(f'Student says: "{user_input}"')
        
        # Add response guidance
        prompt_parts.append("\n=== RESPONSE GUIDANCE ===")
        prompt_parts.append("Provide a helpful, educational response that:")
        prompt_parts.append("1. Addresses the student's input directly")
        prompt_parts.append("2. Adapts to their current engagement and understanding level")
        prompt_parts.append("3. Includes a follow-up question or suggestion to continue learning")
        prompt_parts.append("4. Uses their preferred learning style when possible")
        
        return "\n".join(prompt_parts)
    
    def _analyze_response(self, response_text: str, state: ConversationState) -> Dict[str, Any]:
        """Analyze the generated response to extract metadata"""
        
        response_data = {
            "confidence": 0.8,  # Default confidence
            "response_type": "explanation",
            "suggestions": [],
            "concepts": []
        }
        
        response_lower = response_text.lower()
        
        # Determine response type
        if "?" in response_text:
            response_data["response_type"] = "question"
        elif any(word in response_lower for word in ["great", "excellent", "correct", "well done"]):
            response_data["response_type"] = "encouragement"
        elif any(word in response_lower for word in ["example", "instance", "like", "such as"]):
            response_data["response_type"] = "example"
        elif any(word in response_lower for word in ["let's try", "practice", "exercise"]):
            response_data["response_type"] = "practice"
        
        # Extract potential follow-up suggestions
        if "try" in response_lower:
            response_data["suggestions"].append("Practice exercise available")
        if "?" in response_text:
            response_data["suggestions"].append("Question for reflection")
        if any(word in response_lower for word in ["next", "then", "after"]):
            response_data["suggestions"].append("Next topic suggested")
        
        # Try to identify concepts mentioned (simple keyword detection)
        # This is a simplified approach - could be enhanced with NLP
        concept_indicators = ["concept", "idea", "principle", "rule", "law", "theory"]
        if any(indicator in response_lower for indicator in concept_indicators):
            # Extract potential concepts (this is very basic)
            words = response_text.split()
            for i, word in enumerate(words):
                if word.lower() in concept_indicators and i > 0:
                    potential_concept = words[i-1]
                    if len(potential_concept) > 3:
                        response_data["concepts"].append(potential_concept)
        
        return response_data
    
    def _generate_fallback_response(self, user_input: str, state: ConversationState) -> Dict[str, Any]:
        """Generate a fallback response when OpenAI is not available"""
        
        user_lower = user_input.lower()
        
        # Simple pattern-based responses
        if "?" in user_input:
            if any(word in user_lower for word in ["what", "how", "why", "when", "where"]):
                response = f"That's a great question about '{user_input.replace('?', '')}'. Let me help you think through this step by step. Can you tell me what you already know about this topic?"
            else:
                response = "I can see you have a question. Let's break it down together. What specific part would you like to explore?"
        
        elif any(word in user_lower for word in ["confused", "don't understand", "help"]):
            response = "I understand you're having some difficulty. That's completely normal when learning! Let's take it one step at a time. What part is most confusing to you?"
        
        elif any(word in user_lower for word in ["yes", "understand", "got it"]):
            response = "Excellent! I'm glad that makes sense. To make sure you've really got it, can you explain it back to me in your own words?"
        
        else:
            response = f"I hear you saying '{user_input}'. That's interesting! Can you tell me more about what you're thinking, or would you like me to explain something related to this?"
        
        return {
            "text": response,
            "confidence": 0.6,
            "response_type": "fallback",
            "suggestions": ["Continue conversation"],
            "detected_concepts": []
        } 