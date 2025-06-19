"""
AI Tutor API - Endpoints for intelligent tutoring features
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.ai_tutor import (
    TutorRequest, TutorResponse, HintRequest, HintResponse,
    CodeFeedbackRequest, CodeFeedbackResponse, LearningPathResponse,
    AdaptiveQuestionRequest, AdaptiveQuestionResponse, StudentProgressAnalysis,
    TutorSessionSummary, LearningPathSuggestion
)
from app.services.ai_tutor_service import AITutorService

router = APIRouter(prefix="/ai-tutor", tags=["ai-tutor"])
ai_tutor_service = AITutorService()


@router.get("/status")
async def get_ai_tutor_status():
    """Get AI tutor service status"""
    return {
        "ai_available": ai_tutor_service.is_available(),
        "model": getattr(ai_tutor_service, 'model', 'none'),
        "features": {
            "personalized_responses": True,
            "contextual_hints": True,
            "code_feedback": True,
            "learning_paths": True,
            "adaptive_questions": ai_tutor_service.is_available()
        }
    }


@router.post("/ask", response_model=TutorResponse)
async def ask_tutor(
    request: TutorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> TutorResponse:
    """
    Ask the AI tutor a question and get personalized response
    """
    try:
        # Build student context
        student_context = {
            "student_id": current_user.id,
            "level": "intermediate",  # Could be fetched from user profile
            "completion_percentage": 0.65,  # Could be calculated from progress
            "time_spent": 120,  # Minutes in current session
            "coins": 50,  # Current coin balance
            "session_id": request.context.get("session_id") if request.context else None
        }
        
        # Get AI response
        response = await ai_tutor_service.get_personalized_response(
            request, student_context, db
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting tutor response: {str(e)}"
        )


@router.post("/hint", response_model=HintResponse)
async def get_hint(
    request: HintRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> HintResponse:
    """
    Get a contextual hint for the current problem
    """
    try:
        # Check if user has enough coins for hint
        # In a real implementation, you'd fetch from user's coin balance
        required_coins = 5 * request.hint_level
        user_coins = 100  # Placeholder - fetch from user profile
        
        if user_coins < required_coins:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient coins. Need {required_coins}, have {user_coins}"
            )
        
        # Build student context
        student_context = {
            "student_id": current_user.id,
            "level": "intermediate",
            "coins": user_coins
        }
        
        # Get hint
        response = await ai_tutor_service.get_contextual_hint(
            request, student_context, db
        )
        
        # Deduct coins (in real implementation, update user's coin balance)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting hint: {str(e)}"
        )


@router.post("/code-feedback", response_model=CodeFeedbackResponse)
async def get_code_feedback(
    request: CodeFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> CodeFeedbackResponse:
    """
    Get AI feedback on submitted code
    """
    try:
        # Build student context
        student_context = {
            "student_id": current_user.id,
            "level": "intermediate"
        }
        
        # Get code feedback
        response = await ai_tutor_service.provide_code_feedback(
            request, student_context, db
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing code: {str(e)}"
        )


@router.get("/learning-path", response_model=LearningPathResponse)
async def get_learning_path(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> LearningPathResponse:
    """
    Get personalized learning path recommendations
    """
    try:
        # Build comprehensive student context
        student_context = {
            "student_id": current_user.id,
            "completion_percentage": 0.67,
            "level": "intermediate",
            "strengths": ["Quick learner", "Good with syntax", "Problem solving"],
            "weaknesses": ["Algorithm optimization", "Complex data structures"],
            "preferences": {"learning_style": "visual", "pace": "moderate"}
        }
        
        # Get learning suggestions
        suggestions = await ai_tutor_service.suggest_learning_path(
            student_context, db
        )
        
        # Create response
        response = LearningPathResponse(
            suggestions=suggestions,
            current_level="intermediate",
            strengths=student_context["strengths"],
            areas_for_improvement=student_context["weaknesses"],
            motivation_message="You're making excellent progress! Keep up the great work and focus on the suggested areas to level up your skills."
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating learning path: {str(e)}"
        )


@router.post("/adaptive-question", response_model=AdaptiveQuestionResponse)
async def generate_adaptive_question(
    request: AdaptiveQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> AdaptiveQuestionResponse:
    """
    Generate adaptive questions based on student performance
    """
    if not ai_tutor_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI question generation is currently unavailable"
        )
    
    try:
        # This would use AI to generate adaptive questions
        # For now, return a sample response
        sample_questions = {
            "coding": {
                "beginner": "Write a function that adds two numbers and returns the result.",
                "intermediate": "Implement a function that finds the longest substring without repeating characters.",
                "advanced": "Design a data structure that supports insert, delete, and getRandom operations in O(1) time."
            },
            "multiple_choice": {
                "beginner": "Which of the following is the correct syntax for a Python function?",
                "intermediate": "What is the time complexity of binary search?",
                "advanced": "Which design pattern is best suited for creating a family of related objects?"
            }
        }
        
        question_text = sample_questions.get(request.question_type, {}).get(
            request.difficulty_level, 
            "Practice the concepts you've learned so far."
        )
        
        response = AdaptiveQuestionResponse(
            question=question_text,
            question_type=request.question_type,
            difficulty_level=request.difficulty_level,
            expected_answer="[Generated based on question type]",
            grading_criteria=["Correctness", "Efficiency", "Code style"],
            hints=["Think step by step", "Consider edge cases", "Test your solution"],
            estimated_time=15
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating question: {str(e)}"
        )


@router.get("/progress-analysis", response_model=StudentProgressAnalysis)
async def get_progress_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> StudentProgressAnalysis:
    """
    Get detailed analysis of student progress and learning patterns
    """
    try:
        # In a real implementation, this would analyze actual user data
        # For now, return sample analysis
        
        analysis = StudentProgressAnalysis(
            student_id=current_user.id,
            overall_progress=0.73,
            learning_velocity=2.8,
            knowledge_gaps=["Advanced algorithms", "System design", "Database optimization"],
            mastered_topics=["Variables", "Functions", "Loops", "Basic data structures", "Object-oriented programming"],
            learning_style_assessment={
                "visual": 0.8,
                "auditory": 0.4,
                "kinesthetic": 0.6,
                "reading_writing": 0.7
            },
            engagement_metrics={
                "session_frequency": 4.2,
                "avg_session_duration": 47,
                "help_requests_per_session": 0.3,
                "completion_rate": 0.85,
                "time_to_mastery": 25.5
            },
            recommended_study_schedule={
                "sessions_per_week": 5,
                "minutes_per_session": 45,
                "focus_areas": ["Algorithm practice", "Code review", "System design basics"],
                "break_intervals": 15,
                "review_frequency": "weekly"
            }
        )
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing progress: {str(e)}"
        )


@router.get("/session-summary/{session_id}", response_model=TutorSessionSummary)
async def get_session_summary(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> TutorSessionSummary:
    """
    Get summary of a completed tutoring session
    """
    try:
        # In a real implementation, fetch actual session data
        # For now, return sample summary
        
        summary = TutorSessionSummary(
            session_id=session_id,
            duration_minutes=42,
            topics_covered=["Functions", "Recursion", "Base cases", "Tree traversal"],
            questions_asked=8,
            hints_provided=3,
            success_rate=0.75,
            key_insights=[
                "Student demonstrates good understanding of recursion concept",
                "Needs more practice with identifying base cases",
                "Shows creativity in problem-solving approach",
                "Benefits from visual examples and analogies"
            ],
            recommended_followup=[
                "Practice more recursive problems with different data structures",
                "Review tree and graph traversal algorithms",
                "Work on time complexity analysis",
                "Try implementing recursive solutions iteratively"
            ]
        )
        
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting session summary: {str(e)}"
        )


@router.post("/test-ai")
async def test_ai_connection():
    """
    Test AI service connection (public endpoint for testing)
    """
    try:
        # Simple test request
        test_request = TutorRequest(
            question="What is 2 + 2?",
            bubble_id="test",
            bubble_type="concept"
        )
        
        test_context = {
            "student_id": 1,
            "level": "beginner"
        }
        
        # Create a mock database session for testing
        from app.core.database import engine
        with Session(engine) as db:
            response = await ai_tutor_service.get_personalized_response(
                test_request, test_context, db
            )
        
        return {
            "ai_available": ai_tutor_service.is_available(),
            "test_successful": True,
            "sample_response": response.response[:100] + "..." if len(response.response) > 100 else response.response
        }
        
    except Exception as e:
        return {
            "ai_available": ai_tutor_service.is_available(),
            "test_successful": False,
            "error": str(e)
        }


# Additional utility endpoints

@router.get("/topics")
async def get_available_topics():
    """Get list of available topics for AI tutoring"""
    return {
        "programming": [
            "Variables and Data Types",
            "Control Structures",
            "Functions",
            "Object-Oriented Programming",
            "Data Structures",
            "Algorithms",
            "Recursion",
            "Dynamic Programming"
        ],
        "mathematics": [
            "Algebra",
            "Geometry",
            "Calculus",
            "Statistics",
            "Linear Algebra",
            "Discrete Mathematics"
        ],
        "computer_science": [
            "Database Design",
            "System Architecture",
            "Network Programming",
            "Operating Systems",
            "Computer Graphics",
            "Machine Learning"
        ]
    }


@router.get("/learning-styles")
async def get_learning_styles():
    """Get information about different learning styles"""
    return {
        "visual": {
            "description": "Learns best through visual aids, diagrams, and charts",
            "strategies": ["Mind maps", "Flowcharts", "Color coding", "Visual examples"]
        },
        "auditory": {
            "description": "Learns best through hearing and discussion",
            "strategies": ["Verbal explanations", "Discussion", "Music/rhythm", "Reading aloud"]
        },
        "kinesthetic": {
            "description": "Learns best through hands-on activities and movement",
            "strategies": ["Interactive exercises", "Building projects", "Trial and error", "Physical activity"]
        },
        "reading_writing": {
            "description": "Learns best through reading and writing activities",
            "strategies": ["Note-taking", "Lists", "Written exercises", "Research"]
        }
    }


@router.get("/hints/pricing")
async def get_hint_pricing():
    """Get current pricing for hints"""
    return {
        "level_1": {
            "description": "Subtle nudge in the right direction",
            "cost_coins": 5
        },
        "level_2": {
            "description": "Clearer guidance on approach",
            "cost_coins": 10
        },
        "level_3": {
            "description": "Direct help toward solution",
            "cost_coins": 15
        }
    } 