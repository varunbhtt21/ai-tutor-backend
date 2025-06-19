"""
Course API endpoints
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate, CourseListResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/courses", tags=["courses"])


def require_instructor_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require instructor or admin role"""
    if current_user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and admins can perform this action"
        )
    return current_user


def require_course_access(course_id: int, current_user: User, db: Session) -> Course:
    """Require access to course"""
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Allow access if user is instructor of course or admin
    if current_user.role == UserRole.ADMIN or course.instructor_id == current_user.id:
        return course
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this course"
    )


@router.post("/", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor_or_admin)
):
    """Create a new course"""
    db_course = Course(
        name=course_data.name,
        description=course_data.description,
        subject=course_data.subject,
        difficulty_level=course_data.difficulty_level,
        estimated_duration=course_data.estimated_duration,
        instructor_id=current_user.id,
        is_active=True,
        is_public=course_data.is_public,
        requires_approval=course_data.requires_approval,
        learning_objectives=course_data.learning_objectives,
        prerequisites=course_data.prerequisites,
        tags=course_data.tags,
        created_at=datetime.utcnow()
    )
    
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    
    return CourseResponse.from_orm(db_course)


@router.get("/", response_model=CourseListResponse)
async def list_courses(
    subject: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List courses with filtering"""
    # Build query
    stmt = select(Course)
    
    # Apply filters
    if subject:
        stmt = stmt.where(Course.subject == subject)
    
    if difficulty:
        stmt = stmt.where(Course.difficulty_level == difficulty)
    
    if is_public is not None:
        stmt = stmt.where(Course.is_public == is_public)
    
    # For students, only show public active courses
    if current_user.role == UserRole.STUDENT:
        stmt = stmt.where(Course.is_public == True, Course.is_active == True)
    
    # For instructors, show their courses plus public ones
    elif current_user.role == UserRole.INSTRUCTOR:
        stmt = stmt.where(
            (Course.instructor_id == current_user.id) | 
            (Course.is_public == True)
        )
    
    # Count total
    total_stmt = stmt
    total = len(db.exec(total_stmt).all())
    
    # Apply pagination
    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)
    
    courses = db.exec(stmt).all()
    
    # Convert to response
    course_responses = []
    for course in courses:
        response = CourseResponse.from_orm(course)
        
        # Add computed fields
        from app.models.session import Session as SessionModel
        session_stmt = select(SessionModel).where(SessionModel.course_id == course.id)
        sessions = db.exec(session_stmt).all()
        response.total_sessions = len(sessions)
        
        # Count unique students across all sessions
        from app.models.session import StudentState
        student_stmt = select(StudentState).join(SessionModel).where(SessionModel.course_id == course.id)
        unique_students = set(state.student_id for state in db.exec(student_stmt).all())
        response.student_count = len(unique_students)
        
        course_responses.append(response)
    
    return CourseListResponse(
        courses=course_responses,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get course details"""
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check access permissions
    if current_user.role == UserRole.STUDENT:
        if not course.is_public or not course.is_active:
            raise HTTPException(status_code=404, detail="Course not found")
    elif current_user.role == UserRole.INSTRUCTOR:
        if course.instructor_id != current_user.id and not course.is_public:
            raise HTTPException(status_code=404, detail="Course not found")
    
    # Build response with computed fields
    response = CourseResponse.from_orm(course)
    
    from app.models.session import Session as SessionModel, StudentState
    session_stmt = select(SessionModel).where(SessionModel.course_id == course_id)
    sessions = db.exec(session_stmt).all()
    response.total_sessions = len(sessions)
    
    # Count unique students
    student_stmt = select(StudentState).join(SessionModel).where(SessionModel.course_id == course_id)
    unique_students = set(state.student_id for state in db.exec(student_stmt).all())
    response.student_count = len(unique_students)
    
    return response


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor_or_admin)
):
    """Update course"""
    course = require_course_access(course_id, current_user, db)
    
    # Update fields
    update_data = course_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    
    course.updated_at = datetime.utcnow()
    
    db.add(course)
    db.commit()
    db.refresh(course)
    
    return CourseResponse.from_orm(course)


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor_or_admin)
):
    """Delete course"""
    course = require_course_access(course_id, current_user, db)
    
    # Check if course has sessions
    from app.models.session import Session as SessionModel
    session_stmt = select(SessionModel).where(SessionModel.course_id == course_id)
    sessions = db.exec(session_stmt).all()
    
    if sessions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete course with sessions"
        )
    
    db.delete(course)
    db.commit()
    
    return {"message": "Course deleted successfully"}


@router.post("/{course_id}/enroll")
async def enroll_in_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enroll student in course (placeholder)"""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can enroll in courses"
        )
    
    course = db.get(Course, course_id)
    if not course or not course.is_public or not course.is_active:
        raise HTTPException(status_code=404, detail="Course not available")
    
    # For now, just return success
    # In a full implementation, you'd create enrollment records
    return {"message": "Enrolled successfully", "course_id": course_id}


@router.get("/{course_id}/sessions")
async def list_course_sessions(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List sessions for a course"""
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check access
    if current_user.role == UserRole.STUDENT:
        if not course.is_public or not course.is_active:
            raise HTTPException(status_code=404, detail="Course not found")
    elif current_user.role == UserRole.INSTRUCTOR:
        if course.instructor_id != current_user.id and not course.is_public:
            raise HTTPException(status_code=404, detail="Course not found")
    
    from app.models.session import Session as SessionModel
    stmt = select(SessionModel).where(SessionModel.course_id == course_id)
    
    # For students, only show published sessions
    if current_user.role == UserRole.STUDENT:
        stmt = stmt.where(SessionModel.status == "published")
    
    sessions = db.exec(stmt).all()
    
    # Convert to basic response format
    session_list = []
    for session in sessions:
        session_data = {
            "id": session.id,
            "name": session.name,
            "description": session.description,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "total_bubbles": len(session.graph_json.get('nodes', []))
        }
        session_list.append(session_data)
    
    return {"sessions": session_list, "total": len(session_list)} 