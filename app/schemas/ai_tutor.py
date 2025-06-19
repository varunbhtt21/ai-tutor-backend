"""
AI Tutor Schemas - Request/Response models for intelligent tutoring
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TutorRequest(BaseModel):
    """Request for AI tutor assistance"""
    question: str = Field(..., description="Student's question or problem")
    bubble_id: str = Field(..., description="Current bubble/node ID")
    bubble_type: str = Field(..., description="Type of bubble (concept, task, quiz)")
    current_attempt: Optional[str] = Field(None, description="Student's current attempt/answer")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "How do I implement a recursive function?",
                "bubble_id": "programming_basics_recursion",
                "bubble_type": "concept",
                "current_attempt": "def factorial(n): return n * factorial(n-1)",
                "context": {"difficulty": "beginner"}
            }
        }


class TutorResponse(BaseModel):
    """AI tutor response"""
    response: str = Field(..., description="AI tutor's response")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in response (0-1)")
    suggestions: List[str] = Field(default_factory=list, description="Learning suggestions")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Great start! Your recursive function needs a base case to prevent infinite recursion. Try adding a condition like 'if n <= 1: return 1'",
                "confidence": 0.9,
                "suggestions": ["Add base case", "Test with small values"],
                "next_steps": ["Practice with different recursive problems", "Learn about tail recursion"]
            }
        }


class HintRequest(BaseModel):
    """Request for learning hints"""
    bubble_id: str = Field(..., description="Current bubble ID")
    question: str = Field(..., description="Question student needs help with")
    current_attempt: Optional[str] = Field(None, description="Student's current attempt")
    hint_level: int = Field(1, ge=1, le=3, description="Hint level (1=subtle, 3=direct)")
    previous_hints: List[str] = Field(default_factory=list, description="Previously given hints")
    
    class Config:
        json_schema_extra = {
            "example": {
                "bubble_id": "algebra_quadratic_equations",
                "question": "Solve x² - 5x + 6 = 0",
                "current_attempt": "x = 5 ± √25 - 24",
                "hint_level": 2,
                "previous_hints": ["Try using the quadratic formula"]
            }
        }


class HintResponse(BaseModel):
    """Response with learning hint"""
    hint: str = Field(..., description="The hint text")
    hint_level: int = Field(..., description="Level of hint provided")
    cost_coins: int = Field(..., description="Coin cost for this hint")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "hint": "You're on the right track! Now simplify what's under the square root and solve for both possible values.",
                "hint_level": 2,
                "cost_coins": 10
            }
        }


class CodeFeedbackRequest(BaseModel):
    """Request for code feedback"""
    code: str = Field(..., description="Student's code submission")
    language: str = Field(..., description="Programming language")
    bubble_id: str = Field(..., description="Current bubble ID")
    expected_output: Optional[str] = Field(None, description="Expected output")
    test_cases: Optional[List[Dict[str, Any]]] = Field(None, description="Test cases to validate against")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
                "language": "python",
                "bubble_id": "algorithms_fibonacci",
                "expected_output": "[0, 1, 1, 2, 3, 5, 8]",
                "test_cases": [
                    {"input": 0, "expected": 0},
                    {"input": 5, "expected": 5}
                ]
            }
        }


class CodeFeedbackResponse(BaseModel):
    """Response with code feedback"""
    feedback: str = Field(..., description="Overall feedback on the code")
    is_correct: bool = Field(..., description="Whether the code is correct")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    explanation: str = Field(..., description="Detailed explanation")
    corrected_code: Optional[str] = Field(None, description="Corrected version if applicable")
    performance_notes: Optional[str] = Field(None, description="Performance considerations")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "feedback": "Your Fibonacci implementation is correct but not optimal for larger values.",
                "is_correct": True,
                "suggestions": ["Consider using memoization", "Try iterative approach"],
                "explanation": "Recursive solution works but has exponential time complexity. Each call recalculates the same values.",
                "performance_notes": "O(2^n) time complexity - consider O(n) alternatives"
            }
        }


class LearningPathSuggestion(BaseModel):
    """Suggestion for learning path"""
    title: str = Field(..., description="Suggestion title")
    description: str = Field(..., description="Detailed description")
    priority: str = Field(..., description="Priority level (high, medium, low)")
    estimated_time: int = Field(..., description="Estimated time in minutes")
    prerequisites: List[str] = Field(default_factory=list, description="Required prerequisites")
    resources: List[str] = Field(default_factory=list, description="Recommended resources")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Master Array Algorithms",
                "description": "Focus on array manipulation and searching algorithms to strengthen your foundation",
                "priority": "high",
                "estimated_time": 45,
                "prerequisites": ["Basic loops", "Array indexing"],
                "resources": ["Array tutorial", "Practice problems"]
            }
        }


class LearningPathResponse(BaseModel):
    """Response with personalized learning path"""
    suggestions: List[LearningPathSuggestion] = Field(..., description="Learning suggestions")
    current_level: str = Field(..., description="Assessed current level")
    strengths: List[str] = Field(default_factory=list, description="Identified strengths")
    areas_for_improvement: List[str] = Field(default_factory=list, description="Areas needing work")
    motivation_message: str = Field(..., description="Encouraging message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "suggestions": [
                    {
                        "title": "Practice Problem Solving",
                        "description": "Work on algorithmic thinking with guided exercises",
                        "priority": "high",
                        "estimated_time": 30
                    }
                ],
                "current_level": "intermediate",
                "strengths": ["Quick learner", "Good with syntax"],
                "areas_for_improvement": ["Algorithm design", "Complex problem solving"],
                "motivation_message": "You're making excellent progress! Focus on problem-solving strategies next."
            }
        }


class AdaptiveQuestionRequest(BaseModel):
    """Request for adaptive question generation"""
    topic: str = Field(..., description="Topic to generate questions for")
    difficulty_level: str = Field(..., description="Target difficulty level")
    student_performance: Dict[str, Any] = Field(..., description="Student performance data")
    question_type: str = Field(..., description="Type of question (multiple_choice, coding, essay)")
    previous_questions: List[str] = Field(default_factory=list, description="Previously asked questions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Python Functions",
                "difficulty_level": "intermediate",
                "student_performance": {"success_rate": 0.75, "avg_time": 120},
                "question_type": "coding",
                "previous_questions": ["Write a function to calculate factorial"]
            }
        }


class AdaptiveQuestionResponse(BaseModel):
    """Response with generated adaptive question"""
    question: str = Field(..., description="Generated question")
    question_type: str = Field(..., description="Type of question")
    difficulty_level: str = Field(..., description="Difficulty level")
    expected_answer: str = Field(..., description="Expected answer or solution")
    grading_criteria: List[str] = Field(default_factory=list, description="Grading criteria")
    hints: List[str] = Field(default_factory=list, description="Available hints")
    estimated_time: int = Field(..., description="Estimated completion time in minutes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Write a function that takes a list of integers and returns the second largest number. Handle edge cases appropriately.",
                "question_type": "coding",
                "difficulty_level": "intermediate",
                "expected_answer": "def second_largest(nums): ...",
                "grading_criteria": ["Handles empty list", "Finds correct value", "Efficient solution"],
                "hints": ["Consider sorting", "Think about edge cases", "What if all numbers are the same?"],
                "estimated_time": 15
            }
        }


class StudentProgressAnalysis(BaseModel):
    """Analysis of student progress and learning patterns"""
    student_id: int = Field(..., description="Student identifier")
    overall_progress: float = Field(..., ge=0.0, le=1.0, description="Overall progress percentage")
    learning_velocity: float = Field(..., description="Rate of learning (topics per hour)")
    knowledge_gaps: List[str] = Field(default_factory=list, description="Identified knowledge gaps")
    mastered_topics: List[str] = Field(default_factory=list, description="Successfully mastered topics")
    learning_style_assessment: Dict[str, float] = Field(default_factory=dict, description="Learning style preferences")
    engagement_metrics: Dict[str, Any] = Field(default_factory=dict, description="Engagement statistics")
    recommended_study_schedule: Dict[str, Any] = Field(default_factory=dict, description="Suggested study plan")
    
    class Config:
        json_schema_extra = {
            "example": {
                "student_id": 123,
                "overall_progress": 0.67,
                "learning_velocity": 2.5,
                "knowledge_gaps": ["Advanced algorithms", "System design"],
                "mastered_topics": ["Variables", "Loops", "Functions"],
                "learning_style_assessment": {
                    "visual": 0.8,
                    "auditory": 0.4,
                    "kinesthetic": 0.6
                },
                "engagement_metrics": {
                    "session_frequency": 4.2,
                    "avg_session_duration": 45,
                    "help_requests": 0.3
                }
            }
        }


class TutorSessionSummary(BaseModel):
    """Summary of a tutoring session"""
    session_id: str = Field(..., description="Session identifier")
    duration_minutes: int = Field(..., description="Session duration")
    topics_covered: List[str] = Field(default_factory=list, description="Topics discussed")
    questions_asked: int = Field(..., description="Number of questions asked")
    hints_provided: int = Field(..., description="Number of hints given")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate in session")
    key_insights: List[str] = Field(default_factory=list, description="Key learning insights")
    recommended_followup: List[str] = Field(default_factory=list, description="Recommended follow-up actions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_456",
                "duration_minutes": 32,
                "topics_covered": ["Functions", "Recursion", "Base cases"],
                "questions_asked": 7,
                "hints_provided": 3,
                "success_rate": 0.71,
                "key_insights": ["Student grasps recursion concept", "Needs practice with base cases"],
                "recommended_followup": ["More recursion practice", "Review tree traversal"]
            }
        } 