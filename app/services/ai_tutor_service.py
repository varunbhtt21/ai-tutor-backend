"""
AI Tutor Service - Intelligent tutoring with OpenAI integration
Provides personalized learning assistance and adaptive responses
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import OpenAI
from sqlmodel import Session

from app.core.config import settings
from app.models.session import BubbleNode, StudentState
from app.models.analytics import EventLog, EventType
from app.schemas.ai_tutor import (
    TutorRequest, TutorResponse, HintRequest, HintResponse,
    CodeFeedbackRequest, CodeFeedbackResponse, LearningPathSuggestion
)

logger = logging.getLogger(__name__)


class AITutorService:
    """AI-powered tutoring service using OpenAI"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        try:
            if hasattr(settings, 'openai_api_key') and settings.openai_api_key and settings.openai_api_key != "your-openai-api-key-here":
                self.client = OpenAI(api_key=settings.openai_api_key)
                self.model = "gpt-4o-mini"  # Use more cost-effective model
                logger.info("AI Tutor Service initialized successfully")
            else:
                self.client = None
                logger.warning("OpenAI API key not configured - AI features will be disabled")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.client is not None
    
    async def get_personalized_response(
        self,
        request: TutorRequest,
        student_context: Dict[str, Any],
        db: Session
    ) -> TutorResponse:
        """Get personalized AI response based on student context"""
        
        if not self.is_available():
            return self._get_fallback_response(request)
        
        try:
            # Build context for AI
            context = self._build_student_context(request, student_context, db)
            
            # Create system prompt
            system_prompt = self._create_system_prompt(request.bubble_type, context)
            
            # Create user message
            user_message = self._create_user_message(request, context)
            
            # Call OpenAI
            response = await self._call_openai(system_prompt, user_message)
            
            # Parse and structure response
            tutor_response = self._parse_ai_response(response, request)
            
            # Log interaction
            self._log_tutor_interaction(request, tutor_response, student_context, db)
            
            return tutor_response
            
        except Exception as e:
            logger.error(f"Error in AI tutor response: {e}")
            return self._get_fallback_response(request)
    
    async def get_contextual_hint(
        self,
        request: HintRequest,
        student_context: Dict[str, Any],
        db: Session
    ) -> HintResponse:
        """Provide contextual hints based on student progress"""
        
        if not self.is_available():
            return self._get_fallback_hint(request)
        
        try:
            # Determine hint level and cost
            hint_cost = self._calculate_hint_cost(request.hint_level)
            
            # Build context
            context = self._build_hint_context(request, student_context, db)
            
            # Create hint prompt
            system_prompt = self._create_hint_prompt(request.hint_level, context)
            user_message = f"Student is struggling with: {request.question}\nCurrent attempt: {request.current_attempt or 'No attempt yet'}"
            
            # Get AI hint
            response = await self._call_openai(system_prompt, user_message)
            hint_text = self._extract_hint_from_response(response, request.hint_level)
            
            return HintResponse(
                hint=hint_text,
                hint_level=request.hint_level,
                cost_coins=hint_cost
            )
            
        except Exception as e:
            logger.error(f"Error generating hint: {e}")
            return self._get_fallback_hint(request)
    
    async def provide_code_feedback(
        self,
        request: CodeFeedbackRequest,
        student_context: Dict[str, Any],
        db: Session
    ) -> CodeFeedbackResponse:
        """Provide detailed feedback on student code"""
        
        if not self.is_available():
            return self._get_fallback_code_feedback(request)
        
        try:
            # Analyze code
            context = self._build_code_context(request, student_context, db)
            
            # Create code review prompt
            system_prompt = self._create_code_review_prompt(request.language, context)
            user_message = self._create_code_review_message(request)
            
            # Get AI feedback
            response = await self._call_openai(system_prompt, user_message)
            feedback_data = self._parse_code_feedback(response)
            
            return CodeFeedbackResponse(
                feedback=feedback_data["feedback"],
                is_correct=feedback_data["is_correct"],
                suggestions=feedback_data["suggestions"],
                explanation=feedback_data["explanation"],
                corrected_code=feedback_data.get("corrected_code")
            )
            
        except Exception as e:
            logger.error(f"Error in code feedback: {e}")
            return self._get_fallback_code_feedback(request)
    
    async def suggest_learning_path(
        self,
        student_context: Dict[str, Any],
        db: Session
    ) -> List[LearningPathSuggestion]:
        """Suggest personalized learning path based on student progress"""
        
        if not self.is_available():
            return self._get_fallback_learning_path()
        
        try:
            # Analyze student performance
            context = self._build_learning_context(student_context, db)
            
            # Create learning path prompt
            system_prompt = self._create_learning_path_prompt()
            user_message = self._create_learning_path_message(context)
            
            # Get AI suggestions
            response = await self._call_openai(system_prompt, user_message)
            suggestions = self._parse_learning_suggestions(response)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error in learning path suggestion: {e}")
            return self._get_fallback_learning_path()
    
    # Private helper methods
    
    def _build_student_context(
        self,
        request: TutorRequest,
        student_context: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Build comprehensive student context for AI"""
        
        # Get recent performance
        student_id = student_context.get("student_id", 1)
        recent_events = self._get_recent_events(student_id, db)
        
        # Calculate performance metrics
        success_rate = self._calculate_success_rate(recent_events)
        common_mistakes = self._identify_common_mistakes(recent_events)
        learning_style = self._infer_learning_style(recent_events)
        
        return {
            "student_level": student_context.get("level", "beginner"),
            "current_bubble": request.bubble_id,
            "bubble_type": request.bubble_type,
            "recent_performance": success_rate,
            "common_mistakes": common_mistakes,
            "learning_style": learning_style,
            "session_progress": student_context.get("completion_percentage", 0),
            "time_spent": student_context.get("time_spent", 0),
            "coins_earned": student_context.get("coins", 0)
        }
    
    def _create_system_prompt(self, bubble_type: str, context: Dict[str, Any]) -> str:
        """Create system prompt for AI tutor"""
        
        base_prompt = """You are an expert AI tutor specializing in personalized education. 
        Your role is to provide supportive, encouraging, and pedagogically sound guidance."""
        
        if bubble_type == "concept":
            specific_prompt = """Focus on clear explanations, use analogies, and build understanding gradually.
            Ask guiding questions to ensure comprehension."""
        elif bubble_type == "task":
            specific_prompt = """Provide step-by-step guidance without giving away answers.
            Encourage problem-solving thinking and celebrate progress."""
        elif bubble_type == "quiz":
            specific_prompt = """Give constructive feedback on answers.
            Explain why answers are correct or incorrect with clear reasoning."""
        else:
            specific_prompt = "Adapt your teaching style to the specific learning objective."
        
        context_prompt = f"""
        Student Context:
        - Level: {context.get('student_level', 'unknown')}
        - Recent Performance: {context.get('recent_performance', 0):.1%}
        - Learning Style: {context.get('learning_style', 'mixed')}
        - Session Progress: {context.get('session_progress', 0):.1%}
        """
        
        return f"{base_prompt}\n\n{specific_prompt}\n\n{context_prompt}"
    
    def _create_user_message(self, request: TutorRequest, context: Dict[str, Any]) -> str:
        """Create user message for AI"""
        
        message = f"Student question: {request.question}\n"
        
        if request.current_attempt:
            message += f"Current attempt: {request.current_attempt}\n"
        
        if context.get("common_mistakes"):
            message += f"Common student mistakes in this area: {', '.join(context['common_mistakes'][:3])}\n"
        
        message += f"Please provide helpful guidance appropriate for a {context.get('student_level', 'beginner')} level student."
        
        return message
    
    async def _call_openai(self, system_prompt: str, user_message: str) -> str:
        """Make API call to OpenAI"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def _parse_ai_response(self, response: str, request: TutorRequest) -> TutorResponse:
        """Parse AI response into structured format"""
        
        # Simple parsing - in production, you might want more sophisticated parsing
        lines = response.strip().split('\n')
        
        main_response = lines[0] if lines else response
        suggestions = []
        next_steps = []
        
        # Extract suggestions and next steps if present
        for line in lines[1:]:
            line = line.strip()
            if line.startswith("Suggestion:") or line.startswith("- "):
                suggestions.append(line.replace("Suggestion:", "").replace("- ", "").strip())
            elif line.startswith("Next:") or line.startswith("Next step:"):
                next_steps.append(line.replace("Next:", "").replace("Next step:", "").strip())
        
        return TutorResponse(
            response=main_response,
            confidence=0.8,  # Default confidence
            suggestions=suggestions[:3],  # Limit to 3 suggestions
            next_steps=next_steps[:3]  # Limit to 3 next steps
        )
    
    def _calculate_hint_cost(self, hint_level: int) -> int:
        """Calculate coin cost for hints based on level"""
        base_cost = 5
        return base_cost * hint_level
    
    def _get_recent_events(self, student_id: int, db: Session) -> List[EventLog]:
        """Get recent student events for analysis"""
        from sqlmodel import select
        
        try:
            stmt = (select(EventLog)
                    .where(EventLog.student_id == student_id)
                    .order_by(EventLog.timestamp.desc())
                    .limit(20))
            
            return db.exec(stmt).all()
        except Exception as e:
            logger.error(f"Error fetching recent events: {e}")
            return []
    
    def _calculate_success_rate(self, events: List[EventLog]) -> float:
        """Calculate student success rate from recent events"""
        if not events:
            return 0.5  # Default neutral rate
        
        success_events = [e for e in events if e.event_type == EventType.BUBBLE_SUCCESS]
        total_attempts = [e for e in events if e.event_type in [EventType.BUBBLE_SUCCESS, EventType.BUBBLE_FAIL]]
        
        if not total_attempts:
            return 0.5
        
        return len(success_events) / len(total_attempts)
    
    def _identify_common_mistakes(self, events: List[EventLog]) -> List[str]:
        """Identify common mistakes from event logs"""
        # Simplified implementation - in production, analyze failure patterns
        failures = [e for e in events if e.event_type == EventType.BUBBLE_FAIL]
        
        mistakes = []
        for event in failures[:3]:  # Last 3 failures
            if event.payload and isinstance(event.payload, dict) and "error" in event.payload:
                mistakes.append(event.payload["error"])
        
        return mistakes
    
    def _infer_learning_style(self, events: List[EventLog]) -> str:
        """Infer student learning style from behavior"""
        # Simplified implementation
        if not events:
            return "balanced"
        
        hint_requests = len([e for e in events if e.event_type == EventType.HINT_REQUESTED])
        total_events = len(events)
        
        if hint_requests / max(total_events, 1) > 0.3:
            return "guided"
        else:
            return "independent"
    
    def _log_tutor_interaction(
        self,
        request: TutorRequest,
        response: TutorResponse,
        student_context: Dict[str, Any],
        db: Session
    ):
        """Log AI tutor interaction for analytics"""
        
        try:
            event = EventLog(
                event_type=EventType.TUTOR_INTERACTION,
                student_id=student_context.get("student_id", 1),
                session_id=student_context.get("session_id"),
                node_id=request.bubble_id,
                payload={
                    "question": request.question[:100],  # Limit length
                    "response_length": len(response.response),
                    "confidence": response.confidence,
                    "suggestions_count": len(response.suggestions)
                },
                timestamp=datetime.utcnow()
            )
            
            db.add(event)
            db.commit()
        except Exception as e:
            logger.error(f"Error logging tutor interaction: {e}")
    
    # Fallback methods for when AI is not available
    
    def _get_fallback_response(self, request: TutorRequest) -> TutorResponse:
        """Provide fallback response when AI is unavailable"""
        
        fallback_responses = {
            "concept": "Let me help you understand this concept. Try breaking it down into smaller parts and think about how it relates to what you already know.",
            "task": "Great question! Let's approach this step by step. What do you think the first step should be?",
            "quiz": "Take your time to think through this. Consider what you've learned so far and apply those principles.",
        }
        
        response = fallback_responses.get(request.bubble_type, "I'm here to help! Let's work through this together.")
        
        return TutorResponse(
            response=response,
            confidence=0.6,
            suggestions=["Take your time", "Review the material", "Try a different approach"],
            next_steps=["Practice similar problems", "Ask for clarification if needed"]
        )
    
    def _get_fallback_hint(self, request: HintRequest) -> HintResponse:
        """Provide fallback hint when AI is unavailable"""
        
        hints_by_level = {
            1: "Think about the key concepts involved in this problem.",
            2: "Consider breaking this down into smaller steps. What's the first thing you need to figure out?",
            3: "Look at the structure of the problem. What patterns or formulas might apply here?"
        }
        
        hint = hints_by_level.get(request.hint_level, "Try approaching this from a different angle.")
        
        return HintResponse(
            hint=hint,
            hint_level=request.hint_level,
            cost_coins=self._calculate_hint_cost(request.hint_level)
        )
    
    def _get_fallback_code_feedback(self, request: CodeFeedbackRequest) -> CodeFeedbackResponse:
        """Provide fallback code feedback when AI is unavailable"""
        
        return CodeFeedbackResponse(
            feedback="Your code structure looks good. Consider testing it with different inputs to verify it works correctly.",
            is_correct=True,  # Optimistic default
            suggestions=["Test with edge cases", "Check variable names", "Review logic flow"],
            explanation="Code feedback is currently limited. Please verify your solution manually."
        )
    
    def _get_fallback_learning_path(self) -> List[LearningPathSuggestion]:
        """Provide fallback learning suggestions when AI is unavailable"""
        
        return [
            LearningPathSuggestion(
                title="Review Fundamentals",
                description="Strengthen your understanding of basic concepts",
                priority="high",
                estimated_time=20,
                prerequisites=[],
                resources=["Course materials", "Practice exercises"]
            ),
            LearningPathSuggestion(
                title="Practice Problem Solving",
                description="Work on applying concepts to solve problems",
                priority="medium",
                estimated_time=30,
                prerequisites=["Basic understanding"],
                resources=["Problem sets", "Examples"]
            )
        ]
    
    # Helper methods for specific AI features
    
    def _build_hint_context(self, request: HintRequest, student_context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Build context for hint generation"""
        return {
            "bubble_id": request.bubble_id,
            "hint_level": request.hint_level,
            "previous_hints": request.previous_hints,
            "student_level": student_context.get("level", "beginner")
        }
    
    def _create_hint_prompt(self, hint_level: int, context: Dict[str, Any]) -> str:
        """Create system prompt for hint generation"""
        
        if hint_level == 1:
            guidance = "Provide a subtle nudge in the right direction without revealing the answer."
        elif hint_level == 2:
            guidance = "Give a clearer hint that helps identify the approach or method."
        else:
            guidance = "Provide a more direct hint that guides toward the solution."
        
        return f"""You are providing learning hints to a student. {guidance}
        Keep hints encouraging and educational. Student level: {context.get('student_level', 'beginner')}
        Respond with just the hint, no extra formatting."""
    
    def _extract_hint_from_response(self, response: str, hint_level: int) -> str:
        """Extract clean hint from AI response"""
        # Clean up response and ensure appropriate length
        hint = response.strip()
        if len(hint) > 200:
            hint = hint[:200] + "..."
        return hint
    
    def _build_code_context(self, request: CodeFeedbackRequest, student_context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Build context for code feedback"""
        return {
            "language": request.language,
            "expected_output": request.expected_output,
            "test_cases": request.test_cases,
            "student_level": student_context.get("level", "beginner")
        }
    
    def _create_code_review_prompt(self, language: str, context: Dict[str, Any]) -> str:
        """Create system prompt for code review"""
        return f"""You are a code mentor reviewing {language} code. 
        Provide constructive feedback focusing on correctness, best practices, and learning.
        Be encouraging and educational. Student level: {context.get('student_level', 'beginner')}
        Format your response as: Overall feedback first, then specific suggestions."""
    
    def _create_code_review_message(self, request: CodeFeedbackRequest) -> str:
        """Create user message for code review"""
        message = f"Please review this {request.language} code:\n\n{request.code}\n\n"
        
        if request.expected_output:
            message += f"Expected output: {request.expected_output}\n"
        
        if request.test_cases:
            message += f"Test cases to consider: {request.test_cases}\n"
        
        return message
    
    def _parse_code_feedback(self, response: str) -> Dict[str, Any]:
        """Parse code feedback from AI response"""
        # Simplified parsing - in production, use structured output
        lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
        
        feedback = lines[0] if lines else response
        is_correct = "correct" in response.lower() and "incorrect" not in response.lower()
        
        suggestions = []
        explanation_parts = []
        
        for line in lines[1:]:
            if line.startswith("-") or line.startswith("•") or line.startswith("*"):
                suggestions.append(line.lstrip("-•*").strip())
            else:
                explanation_parts.append(line)
        
        explanation = "\n".join(explanation_parts) if explanation_parts else feedback
        
        return {
            "feedback": feedback,
            "is_correct": is_correct,
            "suggestions": suggestions[:3],  # Limit to 3 suggestions
            "explanation": explanation
        }
    
    def _build_learning_context(self, student_context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Build context for learning path suggestions"""
        return {
            "current_progress": student_context.get("completion_percentage", 0),
            "strengths": student_context.get("strengths", []),
            "weaknesses": student_context.get("weaknesses", []),
            "preferences": student_context.get("preferences", {}),
            "level": student_context.get("level", "beginner")
        }
    
    def _create_learning_path_prompt(self) -> str:
        """Create system prompt for learning path suggestions"""
        return """You are an educational advisor. Suggest personalized learning paths 
        based on student performance and preferences. Focus on addressing weaknesses 
        while building on strengths. Provide 3-5 specific, actionable suggestions.
        Format each suggestion as a numbered list item."""
    
    def _create_learning_path_message(self, context: Dict[str, Any]) -> str:
        """Create user message for learning path suggestions"""
        return f"""Student context:
        Progress: {context.get('current_progress', 0):.1%}
        Level: {context.get('level', 'beginner')}
        Strengths: {', '.join(context.get('strengths', ['Quick learner']))}
        Areas for improvement: {', '.join(context.get('weaknesses', ['Practice needed']))}
        
        Please suggest 3-5 specific next learning steps."""
    
    def _parse_learning_suggestions(self, response: str) -> List[LearningPathSuggestion]:
        """Parse learning path suggestions from AI response"""
        suggestions = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '•', '*'))):
                # Extract suggestion text
                text = line.lstrip('12345.-•*').strip()
                if text and len(text) > 5:  # Ensure meaningful content
                    # Extract title (first part before period or colon)
                    title_parts = text.split(':')
                    title = title_parts[0][:50] if title_parts else text[:50]
                    
                    suggestions.append(LearningPathSuggestion(
                        title=title,
                        description=text,
                        priority="medium",
                        estimated_time=20,  # Default 20 minutes
                        prerequisites=[],
                        resources=[]
                    ))
        
        return suggestions[:5]  # Limit to 5 suggestions 