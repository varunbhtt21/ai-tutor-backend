"""
Session and Bubble Graph API endpoints
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, and_

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.session import Session as SessionModel, BubbleNode, StudentState
from app.schemas.session import (
    SessionCreate, SessionResponse, SessionUpdate, SessionListResponse,
    BubbleNodeCreate, BubbleNodeResponse, BubbleGraphSchema,
    GraphValidationResponse, BubbleAdvanceRequest, BubbleAdvanceResponse,
    StudentStateResponse
)
from app.services.graph_service import GraphService
from app.services.session_service import SessionService
from app.api.auth import get_current_user

router = APIRouter(prefix="/sessions", tags=["sessions"])


def require_instructor_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require instructor or admin role"""
    if current_user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and admins can perform this action"
        )
    return current_user


def require_instructor_access(session_id: int, current_user: User, db: Session) -> SessionModel:
    """Require instructor access to session"""
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Allow access if user is instructor of session's course or admin
    if current_user.role == UserRole.ADMIN:
        return session
    
    # Check if user is instructor of the course
    if current_user.role == UserRole.INSTRUCTOR:
        # Get course and check instructor
        from app.models.course import Course
        course = db.get(Course, session.course_id)
        if course and course.instructor_id == current_user.id:
            return session
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this session"
    )


@router.post("/", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor_or_admin)
):
    """Create a new session with bubble graph"""
    # Validate graph
    graph_service = GraphService()
    validation = graph_service.validate_graph(session_data.graph_json)
    
    if not validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid graph: {', '.join(validation.errors)}"
        )
    
    # Create session
    db_session = SessionModel(
        name=session_data.name,
        description=session_data.description,
        course_id=session_data.course_id,
        status="draft",
        start_time=session_data.start_time,
        end_time=session_data.end_time,
        graph_json=session_data.graph_json.dict(),
        max_attempts_per_bubble=session_data.max_attempts_per_bubble,
        coins_per_bubble=session_data.coins_per_bubble,
        time_limit_minutes=session_data.time_limit_minutes,
        created_at=datetime.utcnow()
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # Create bubble nodes
    for node in session_data.graph_json.nodes:
        # Set default values for bubble node
        bubble_node = BubbleNode(
            session_id=db_session.id,
            node_id=node.id,
            type=node.type,
            title=node.title,
            content_md="",  # Will be filled later
            coin_reward=session_data.coins_per_bubble,
            created_at=datetime.utcnow()
        )
        db.add(bubble_node)
    
    db.commit()
    
    # Return response with computed fields
    response = SessionResponse.from_orm(db_session)
    response.total_bubbles = len(session_data.graph_json.nodes)
    return response


@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    course_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    active_only: bool = Query(False, description="Filter for currently active sessions"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List sessions with filtering"""
    # Build query
    stmt = select(SessionModel)
    
    # Apply filters
    if course_id:
        stmt = stmt.where(SessionModel.course_id == course_id)
    
    if status:
        stmt = stmt.where(SessionModel.status == status)
    
    # Filter for active sessions
    if active_only:
        now = datetime.utcnow()
        stmt = stmt.where(
            and_(
                SessionModel.status == "published",
                SessionModel.start_time <= now,
                SessionModel.end_time >= now
            )
        )
    
    # For students, only show published sessions
    if current_user.role == UserRole.STUDENT:
        stmt = stmt.where(SessionModel.status == "published")
    
    # For instructors, only show their sessions (unless admin)
    if current_user.role == UserRole.INSTRUCTOR:
        from app.models.course import Course
        stmt = stmt.join(Course).where(Course.instructor_id == current_user.id)
    
    # Count total
    total_stmt = stmt
    total = len(db.exec(total_stmt).all())
    
    # Apply pagination
    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)
    
    sessions = db.exec(stmt).all()
    
    # Convert to response
    session_responses = []
    for session in sessions:
        response = SessionResponse.from_orm(session)
        response.total_bubbles = len(session.graph_json.get('nodes', []))
        
        # Get student count
        student_count_stmt = select(StudentState).where(StudentState.session_id == session.id)
        student_count = len(db.exec(student_count_stmt).all())
        response.student_count = student_count
        
        # Set computed status fields
        response.is_active = session.is_active
        response.is_upcoming = session.is_upcoming
        response.is_past = session.is_past
        
        session_responses.append(response)
    
    return SessionListResponse(
        sessions=session_responses,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get session details"""
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check access permissions
    if current_user.role == UserRole.STUDENT:
        if session.status != "published":
            raise HTTPException(status_code=404, detail="Session not found")
    elif current_user.role == UserRole.INSTRUCTOR:
        require_instructor_access(session_id, current_user, db)
    
    # Build response
    response = SessionResponse.from_orm(session)
    response.total_bubbles = len(session.graph_json.get('nodes', []))
    
    # Get student count
    student_count_stmt = select(StudentState).where(StudentState.session_id == session_id)
    student_count = len(db.exec(student_count_stmt).all())
    response.student_count = student_count
    
    # Set computed status fields
    response.is_active = session.is_active
    response.is_upcoming = session.is_upcoming
    response.is_past = session.is_past
    
    return response


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    session_data: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor_or_admin)
):
    """Update session"""
    session = require_instructor_access(session_id, current_user, db)
    
    # Update fields
    if session_data.name is not None:
        session.name = session_data.name
    if session_data.description is not None:
        session.description = session_data.description
    if session_data.status is not None:
        session.status = session_data.status
        if session_data.status == "published":
            session.published_at = datetime.utcnow()
    if session_data.max_attempts_per_bubble is not None:
        session.max_attempts_per_bubble = session_data.max_attempts_per_bubble
    if session_data.coins_per_bubble is not None:
        session.coins_per_bubble = session_data.coins_per_bubble
    if session_data.time_limit_minutes is not None:
        session.time_limit_minutes = session_data.time_limit_minutes
    
    # Update graph if provided
    if session_data.graph_json is not None:
        graph_service = GraphService()
        validation = graph_service.validate_graph(session_data.graph_json)
        
        if not validation.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid graph: {', '.join(validation.errors)}"
            )
        
        session.graph_json = session_data.graph_json.dict()
        session.updated_at = datetime.utcnow()
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    response = SessionResponse.from_orm(session)
    response.total_bubbles = len(session.graph_json.get('nodes', []))
    return response


@router.delete("/{session_id}")
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor_or_admin)
):
    """Delete session"""
    session = require_instructor_access(session_id, current_user, db)
    
    # Check if session has student progress
    student_stmt = select(StudentState).where(StudentState.session_id == session_id)
    students = db.exec(student_stmt).all()
    
    if students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete session with student progress"
        )
    
    # Delete bubble nodes first
    bubble_stmt = select(BubbleNode).where(BubbleNode.session_id == session_id)
    bubbles = db.exec(bubble_stmt).all()
    for bubble in bubbles:
        db.delete(bubble)
    
    # Delete session
    db.delete(session)
    db.commit()
    
    return {"message": "Session deleted successfully"}


@router.post("/validate-graph", response_model=GraphValidationResponse)
async def validate_graph_standalone(
    graph_data: BubbleGraphSchema
):
    """Validate a bubble graph structure without requiring an existing session (public endpoint)"""
    graph_service = GraphService()
    validation = graph_service.validate_graph(graph_data)
    return validation


@router.post("/{session_id}/validate", response_model=GraphValidationResponse)
async def validate_graph(
    session_id: int,
    graph_data: Optional[BubbleGraphSchema] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor_or_admin)
):
    """Validate bubble graph"""
    if graph_data:
        # Validate provided graph
        graph_to_validate = graph_data
    else:
        # Validate session's current graph
        session = require_instructor_access(session_id, current_user, db)
        graph_to_validate = BubbleGraphSchema(**session.graph_json)
    
    graph_service = GraphService()
    return graph_service.validate_graph(graph_to_validate)


# Student endpoints
@router.post("/{session_id}/start", response_model=StudentStateResponse)
async def start_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start session for student"""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can start sessions"
        )
    
    session = db.get(SessionModel, session_id)
    if not session or session.status != "published":
        raise HTTPException(status_code=404, detail="Session not available")
    
    session_service = SessionService()
    student_state = session_service.start_session(current_user.id, session_id, db)
    
    return StudentStateResponse.from_orm(student_state)


@router.post("/{session_id}/advance", response_model=BubbleAdvanceResponse)
async def advance_bubble(
    session_id: int,
    advance_data: BubbleAdvanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Advance to next bubble"""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can advance through sessions"
        )
    
    session_service = SessionService()
    return session_service.advance_bubble(current_user.id, session_id, advance_data, db)


@router.get("/{session_id}/state", response_model=StudentStateResponse)
async def get_student_state(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get student state for session"""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view session state"
        )
    
    session_service = SessionService()
    state = session_service.get_student_state(current_user.id, session_id, db)
    
    if not state:
        raise HTTPException(status_code=404, detail="Session not started")
    
    return state


# Bubble node management
@router.post("/{session_id}/bubbles", response_model=BubbleNodeResponse)
async def create_bubble_node(
    session_id: int,
    bubble_data: BubbleNodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor_or_admin)
):
    """Create or update bubble node details"""
    session = require_instructor_access(session_id, current_user, db)
    
    # Check if bubble node already exists
    stmt = select(BubbleNode).where(
        and_(BubbleNode.session_id == session_id, BubbleNode.node_id == bubble_data.node_id)
    )
    existing_bubble = db.exec(stmt).first()
    
    if existing_bubble:
        # Update existing
        for field, value in bubble_data.dict(exclude_unset=True).items():
            setattr(existing_bubble, field, value)
        existing_bubble.updated_at = datetime.utcnow()
        
        db.add(existing_bubble)
        db.commit()
        db.refresh(existing_bubble)
        
        return BubbleNodeResponse.from_orm(existing_bubble)
    else:
        # Create new
        bubble_node = BubbleNode(
            session_id=session_id,
            **bubble_data.dict(),
            created_at=datetime.utcnow()
        )
        
        db.add(bubble_node)
        db.commit()
        db.refresh(bubble_node)
        
        return BubbleNodeResponse.from_orm(bubble_node)


@router.get("/{session_id}/bubbles", response_model=List[BubbleNodeResponse])
async def list_bubble_nodes(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List bubble nodes for session"""
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check access
    if current_user.role == UserRole.STUDENT and session.status != "published":
        raise HTTPException(status_code=404, detail="Session not found")
    elif current_user.role == UserRole.INSTRUCTOR:
        require_instructor_access(session_id, current_user, db)
    
    stmt = select(BubbleNode).where(BubbleNode.session_id == session_id)
    bubbles = db.exec(stmt).all()
    
    return [BubbleNodeResponse.from_orm(bubble) for bubble in bubbles]


@router.get("/{session_id}/bubbles/{node_id}", response_model=BubbleNodeResponse)
async def get_bubble_node(
    session_id: int,
    node_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific bubble node"""
    stmt = select(BubbleNode).where(
        and_(BubbleNode.session_id == session_id, BubbleNode.node_id == node_id)
    )
    bubble = db.exec(stmt).first()
    
    if not bubble:
        raise HTTPException(status_code=404, detail="Bubble node not found")
    
    # Check access to session
    session = db.get(SessionModel, session_id)
    if current_user.role == UserRole.STUDENT and session.status != "published":
        raise HTTPException(status_code=404, detail="Session not found")
    elif current_user.role == UserRole.INSTRUCTOR:
        require_instructor_access(session_id, current_user, db)
    
    return BubbleNodeResponse.from_orm(bubble) 