"""
Analytics API endpoints
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.analytics import EventLog, CoinTransaction
from app.services.session_service import SessionService
from app.api.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


def require_instructor_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require instructor or admin role"""
    if current_user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and admins can access analytics"
        )
    return current_user


@router.get("/sessions/{session_id}")
async def get_session_analytics(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor_or_admin)
):
    """Get analytics for a specific session"""
    # Verify session access
    from app.models.session import Session as SessionModel
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check instructor permissions
    if current_user.role == UserRole.INSTRUCTOR:
        from app.models.course import Course
        course = db.get(Course, session.course_id)
        if not course or course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this session"
            )
    
    session_service = SessionService()
    analytics = session_service.get_session_analytics(session_id, db)
    
    return analytics


@router.get("/students/{student_id}")
async def get_student_analytics(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics for a specific student"""
    # Students can only view their own analytics
    if current_user.role == UserRole.STUDENT:
        if current_user.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students can only view their own analytics"
            )
    elif current_user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view student analytics"
        )
    
    session_service = SessionService()
    progress = session_service.get_student_progress(student_id, db)
    
    return progress


@router.get("/courses/{course_id}")
async def get_course_analytics(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor_or_admin)
):
    """Get analytics for a course"""
    # Verify course access
    from app.models.course import Course
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check instructor permissions
    if current_user.role == UserRole.INSTRUCTOR and course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this course"
        )
    
    # Get all sessions for the course
    from app.models.session import Session as SessionModel, StudentState
    session_stmt = select(SessionModel).where(SessionModel.course_id == course_id)
    sessions = db.exec(session_stmt).all()
    
    if not sessions:
        return {
            "course_id": course_id,
            "total_sessions": 0,
            "total_students": 0,
            "sessions": []
        }
    
    # Get analytics for each session
    session_service = SessionService()
    session_analytics = []
    all_students = set()
    
    for session in sessions:
        analytics = session_service.get_session_analytics(session.id, db)
        analytics["session_id"] = session.id
        analytics["session_name"] = session.name
        session_analytics.append(analytics)
        
        # Track unique students
        if "student_states" in analytics:
            for state in analytics["student_states"]:
                all_students.add(state["student_id"])
    
    # Course-level metrics
    total_completions = sum(a.get("completed_students", 0) for a in session_analytics)
    total_enrollments = sum(a.get("total_students", 0) for a in session_analytics)
    avg_course_completion = (total_completions / total_enrollments * 100) if total_enrollments > 0 else 0
    
    return {
        "course_id": course_id,
        "course_name": course.name,
        "total_sessions": len(sessions),
        "total_unique_students": len(all_students),
        "total_enrollments": total_enrollments,
        "total_completions": total_completions,
        "avg_completion_rate": round(avg_course_completion, 2),
        "sessions": session_analytics
    }


@router.get("/events")
async def get_event_logs(
    student_id: Optional[int] = Query(None),
    session_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor_or_admin)
):
    """Get event logs with filtering"""
    stmt = select(EventLog)
    
    # Apply filters
    if student_id:
        stmt = stmt.where(EventLog.student_id == student_id)
    
    if session_id:
        stmt = stmt.where(EventLog.session_id == session_id)
    
    if event_type:
        stmt = stmt.where(EventLog.event_type == event_type)
    
    if start_date:
        stmt = stmt.where(EventLog.created_at >= start_date)
    
    if end_date:
        stmt = stmt.where(EventLog.created_at <= end_date)
    
    # Order by most recent first
    stmt = stmt.order_by(EventLog.created_at.desc()).limit(limit)
    
    events = db.exec(stmt).all()
    
    return {
        "events": [
            {
                "id": event.id,
                "student_id": event.student_id,
                "session_id": event.session_id,
                "event_type": event.event_type,
                "metadata": event.metadata,
                "created_at": event.created_at.isoformat()
            }
            for event in events
        ],
        "total": len(events)
    }


@router.get("/coins")
async def get_coin_transactions(
    student_id: Optional[int] = Query(None),
    session_id: Optional[int] = Query(None),
    transaction_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get coin transactions with filtering"""
    # Students can only view their own transactions
    if current_user.role == UserRole.STUDENT:
        student_id = current_user.id
    elif current_user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view coin transactions"
        )
    
    stmt = select(CoinTransaction)
    
    # Apply filters
    if student_id:
        stmt = stmt.where(CoinTransaction.student_id == student_id)
    
    if session_id:
        stmt = stmt.where(CoinTransaction.session_id == session_id)
    
    if transaction_type:
        stmt = stmt.where(CoinTransaction.transaction_type == transaction_type)
    
    if start_date:
        stmt = stmt.where(CoinTransaction.created_at >= start_date)
    
    if end_date:
        stmt = stmt.where(CoinTransaction.created_at <= end_date)
    
    # Order by most recent first
    stmt = stmt.order_by(CoinTransaction.created_at.desc()).limit(limit)
    
    transactions = db.exec(stmt).all()
    
    # Calculate totals
    total_earned = sum(t.amount for t in transactions if t.transaction_type == "earned")
    total_spent = sum(t.amount for t in transactions if t.transaction_type == "spent")
    
    return {
        "transactions": [
            {
                "id": transaction.id,
                "student_id": transaction.student_id,
                "session_id": transaction.session_id,
                "amount": transaction.amount,
                "transaction_type": transaction.transaction_type,
                "description": transaction.description,
                "created_at": transaction.created_at.isoformat()
            }
            for transaction in transactions
        ],
        "total_transactions": len(transactions),
        "total_earned": total_earned,
        "total_spent": total_spent,
        "net_coins": total_earned - total_spent
    }


@router.get("/dashboard")
async def get_dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor_or_admin)
):
    """Get dashboard analytics overview"""
    if current_user.role == UserRole.INSTRUCTOR:
        # Instructor dashboard - only their courses
        from app.models.course import Course
        course_stmt = select(Course).where(Course.instructor_id == current_user.id)
        courses = db.exec(course_stmt).all()
        course_ids = [c.id for c in courses]
        
        from app.models.session import Session as SessionModel, StudentState
        session_stmt = select(SessionModel).where(SessionModel.course_id.in_(course_ids))
        sessions = db.exec(session_stmt).all()
        
        # Get student states for instructor's sessions
        session_ids = [s.id for s in sessions]
        if session_ids:
            state_stmt = select(StudentState).where(StudentState.session_id.in_(session_ids))
            states = db.exec(state_stmt).all()
        else:
            states = []
        
    else:
        # Admin dashboard - all data
        from app.models.course import Course
        from app.models.session import Session as SessionModel, StudentState
        
        courses = db.exec(select(Course)).all()
        sessions = db.exec(select(SessionModel)).all()
        states = db.exec(select(StudentState)).all()
    
    # Calculate metrics
    total_courses = len(courses)
    total_sessions = len(sessions)
    active_sessions = len([s for s in sessions if s.status == "published"])
    
    unique_students = len(set(s.student_id for s in states))
    completed_sessions = len([s for s in states if s.is_completed])
    total_enrollments = len(states)
    
    completion_rate = (completed_sessions / total_enrollments * 100) if total_enrollments > 0 else 0
    
    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_events = db.exec(
        select(EventLog).where(EventLog.created_at >= week_ago)
    ).all()
    
    recent_enrollments = len([e for e in recent_events if e.event_type == "session_started"])
    recent_completions = len([e for e in recent_events if e.event_type == "session_completed"])
    
    # Top performing sessions
    session_performance = []
    for session in sessions[:10]:  # Limit to top 10
        session_states = [s for s in states if s.session_id == session.id]
        if session_states:
            completion_rate = len([s for s in session_states if s.is_completed]) / len(session_states) * 100
            avg_time = sum(s.total_time_spent for s in session_states if s.is_completed) / max(1, len([s for s in session_states if s.is_completed]))
            
            session_performance.append({
                "session_id": session.id,
                "session_name": session.name,
                "total_students": len(session_states),
                "completion_rate": round(completion_rate, 2),
                "avg_completion_time_minutes": round(avg_time / 60, 2) if avg_time else 0
            })
    
    # Sort by completion rate
    session_performance.sort(key=lambda x: x["completion_rate"], reverse=True)
    
    return {
        "overview": {
            "total_courses": total_courses,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "unique_students": unique_students,
            "total_enrollments": total_enrollments,
            "completed_sessions": completed_sessions,
            "overall_completion_rate": round(completion_rate, 2)
        },
        "recent_activity": {
            "new_enrollments_7d": recent_enrollments,
            "completions_7d": recent_completions,
            "total_events_7d": len(recent_events)
        },
        "top_sessions": session_performance[:5]
    } 