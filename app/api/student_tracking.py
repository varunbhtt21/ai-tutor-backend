"""
Student Tracking Analytics API endpoints
Handles real-time student interaction tracking and analysis
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.analytics import (
    StudentSessionTracking, ChatInteraction, CodeInteraction, 
    CodeSubmission, StruggleAnalysis, MessageType
)
from app.services.student_tracking_service import StudentTrackingService
from pydantic import BaseModel

router = APIRouter()
tracking_service = StudentTrackingService()


# Request/Response Models
class SessionTrackingInitRequest(BaseModel):
    session_id: int
    student_id: int


class ChatInteractionRequest(BaseModel):
    session_tracking_id: int
    student_id: int
    session_id: int
    message_type: MessageType
    content: str
    node_id: Optional[str] = None
    response_time_ms: Optional[int] = None


class CodeInteractionRequest(BaseModel):
    session_tracking_id: int
    student_id: int
    session_id: int
    code_snapshot: str
    interaction_type: str = "keypress"
    node_id: Optional[str] = None
    language: str = "python"
    previous_code: Optional[str] = None


class CodeSubmissionRequest(BaseModel):
    session_tracking_id: int
    student_id: int
    session_id: int
    node_id: str
    submitted_code: str
    is_correct: bool
    test_results: Dict[str, Any]
    language: str = "python"
    execution_time_ms: Optional[int] = None
    ai_feedback: Optional[str] = None


class StruggleDetectionRequest(BaseModel):
    session_tracking_id: int
    student_id: int
    session_id: int
    node_id: Optional[str] = None


@router.post("/session-tracking/initialize")
async def initialize_session_tracking(
    request: SessionTrackingInitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initialize or retrieve session tracking for a student"""
    
    # Verify user has access to this session
    if current_user.role == "student" and current_user.id != request.student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this student's session"
        )
    
    try:
        session_tracking = await tracking_service.initialize_session_tracking(
            session_id=request.session_id,
            student_id=request.student_id,
            db=db
        )
        
        return {
            "id": session_tracking.id,
            "session_id": session_tracking.session_id,
            "student_id": session_tracking.student_id,
            "start_time": session_tracking.start_time,
            "progress_percentage": session_tracking.progress_percentage,
            "current_struggle_score": session_tracking.current_struggle_score
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize session tracking: {str(e)}"
        )


@router.post("/chat-interaction")
async def track_chat_interaction(
    request: ChatInteractionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track detailed chat interaction"""
    
    # Verify user has access
    if current_user.role == "student" and current_user.id != request.student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to track this student's interactions"
        )
    
    try:
        chat_interaction = await tracking_service.track_chat_interaction(
            session_tracking_id=request.session_tracking_id,
            student_id=request.student_id,
            session_id=request.session_id,
            message_type=request.message_type,
            content=request.content,
            node_id=request.node_id,
            response_time_ms=request.response_time_ms,
            db=db
        )
        
        return {
            "id": chat_interaction.id,
            "timestamp": chat_interaction.timestamp,
            "message_type": chat_interaction.message_type,
            "emotional_tone": chat_interaction.emotional_tone,
            "intent_classification": chat_interaction.intent_classification,
            "complexity_score": chat_interaction.complexity_score
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track chat interaction: {str(e)}"
        )


@router.post("/code-interaction")
async def track_code_interaction(
    request: CodeInteractionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track code changes with intelligent filtering"""
    
    # Verify user has access
    if current_user.role == "student" and current_user.id != request.student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to track this student's interactions"
        )
    
    try:
        code_interaction = await tracking_service.track_code_interaction(
            session_tracking_id=request.session_tracking_id,
            student_id=request.student_id,
            session_id=request.session_id,
            code_snapshot=request.code_snapshot,
            interaction_type=request.interaction_type,
            node_id=request.node_id,
            language=request.language,
            previous_code=request.previous_code,
            db=db
        )
        
        if code_interaction:
            return {
                "id": code_interaction.id,
                "timestamp": code_interaction.timestamp,
                "interaction_type": code_interaction.interaction_type,
                "characters_added": code_interaction.characters_added,
                "characters_deleted": code_interaction.characters_deleted,
                "is_significant_change": code_interaction.is_significant_change,
                "completion_progress": code_interaction.completion_progress,
                "syntax_errors": code_interaction.syntax_errors
            }
        else:
            return {"message": "Interaction not significant enough to record"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track code interaction: {str(e)}"
        )


@router.post("/code-submission")
async def track_code_submission(
    request: CodeSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track code submission and evaluation results"""
    
    # Verify user has access
    if current_user.role == "student" and current_user.id != request.student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to track this student's submissions"
        )
    
    try:
        code_submission = await tracking_service.track_code_submission(
            session_tracking_id=request.session_tracking_id,
            student_id=request.student_id,
            session_id=request.session_id,
            node_id=request.node_id,
            submitted_code=request.submitted_code,
            is_correct=request.is_correct,
            test_results=request.test_results,
            language=request.language,
            execution_time_ms=request.execution_time_ms,
            ai_feedback=request.ai_feedback,
            db=db
        )
        
        return {
            "id": code_submission.id,
            "timestamp": code_submission.timestamp,
            "submission_number": code_submission.submission_number,
            "is_correct": code_submission.is_correct,
            "score": code_submission.score,
            "compilation_errors": code_submission.compilation_errors,
            "runtime_errors": code_submission.runtime_errors,
            "logic_errors": code_submission.logic_errors,
            "time_since_start_seconds": code_submission.time_since_start_seconds
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track code submission: {str(e)}"
        )


@router.post("/detect-struggle")
async def detect_student_struggle(
    request: StruggleDetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze and detect student struggle in real-time"""
    
    # Verify user has access
    if current_user.role == "student" and current_user.id != request.student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to analyze this student's data"
        )
    
    try:
        struggle_analysis = await tracking_service.detect_real_time_struggle(
            session_tracking_id=request.session_tracking_id,
            student_id=request.student_id,
            session_id=request.session_id,
            node_id=request.node_id,
            db=db
        )
        
        if struggle_analysis:
            return {
                "id": struggle_analysis.id,
                "timestamp": struggle_analysis.timestamp,
                "struggle_score": struggle_analysis.struggle_score,
                "severity": struggle_analysis.severity,
                "indicators": struggle_analysis.indicators,
                "ai_analysis": struggle_analysis.ai_analysis,
                "recommendations": struggle_analysis.recommendations,
                "intervention_suggested": struggle_analysis.intervention_suggested
            }
        else:
            return {
                "struggle_score": 0.0,
                "severity": "low",
                "message": "No significant struggle detected"
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect struggle: {str(e)}"
        )


@router.get("/session-tracking/{session_tracking_id}")
async def get_session_tracking(
    session_tracking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive session tracking data"""
    
    from sqlmodel import select
    
    statement = select(StudentSessionTracking).where(
        StudentSessionTracking.id == session_tracking_id
    )
    session_tracking = db.exec(statement).first()
    
    if not session_tracking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session tracking not found"
        )
    
    # Verify user has access
    if (current_user.role == "student" and 
        current_user.id != session_tracking.student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session tracking data"
        )
    
    return {
        "id": session_tracking.id,
        "session_id": session_tracking.session_id,
        "student_id": session_tracking.student_id,
        "start_time": session_tracking.start_time,
        "end_time": session_tracking.end_time,
        "last_activity": session_tracking.last_activity,
        "current_node_id": session_tracking.current_node_id,
        "progress_percentage": session_tracking.progress_percentage,
        "nodes_completed": session_tracking.nodes_completed,
        "nodes_attempted": session_tracking.nodes_attempted,
        "total_interactions": session_tracking.total_interactions,
        "active_time_seconds": session_tracking.active_time_seconds,
        "idle_time_seconds": session_tracking.idle_time_seconds,
        "total_chat_messages": session_tracking.total_chat_messages,
        "total_code_changes": session_tracking.total_code_changes,
        "success_rate": session_tracking.success_rate,
        "current_struggle_score": session_tracking.current_struggle_score,
        "struggle_alerts_triggered": session_tracking.struggle_alerts_triggered,
        "consecutive_failures": session_tracking.consecutive_failures,
        "learning_style_indicators": session_tracking.learning_style_indicators,
        "engagement_patterns": session_tracking.engagement_patterns
    }


@router.get("/student/{student_id}/learning-profile")
@require_role(["admin", "instructor"])
async def get_student_learning_profile(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get or generate student learning profile"""
    
    try:
        profile = await tracking_service.update_learning_profile(
            student_id=student_id,
            db=db
        )
        
        return {
            "id": profile.id,
            "student_id": profile.student_id,
            "created_at": profile.created_at,
            "last_updated": profile.last_updated,
            "learning_style": profile.learning_style,
            "learning_style_confidence": profile.learning_style_confidence,
            "preferred_time_of_day": profile.preferred_time_of_day,
            "average_session_duration_minutes": profile.average_session_duration_minutes,
            "average_response_time_ms": profile.average_response_time_ms,
            "preferred_help_method": profile.preferred_help_method,
            "common_struggle_areas": profile.common_struggle_areas,
            "struggle_recovery_methods": profile.struggle_recovery_methods,
            "resilience_score": profile.resilience_score,
            "motivation_drivers": profile.motivation_drivers,
            "overall_success_rate": profile.overall_success_rate,
            "consistency_score": profile.consistency_score,
            "total_sessions": profile.total_sessions,
            "total_study_time_hours": profile.total_study_time_hours,
            "ai_generated_insights": profile.ai_generated_insights,
            "personalized_recommendations": profile.personalized_recommendations
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get learning profile: {str(e)}"
        ) 