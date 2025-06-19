"""
User Management API endpoints
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/users", tags=["user-management"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action"
        )
    return current_user


def require_admin_or_instructor(current_user: User = Depends(get_current_user)) -> User:
    """Require admin or instructor role"""
    if current_user.role not in [UserRole.ADMIN, UserRole.INSTRUCTOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and instructors can perform this action"
        )
    return current_user


@router.get("/", response_model=List[UserResponse])
async def list_users(
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_instructor)
):
    """List all users with optional filtering"""
    # Build query
    stmt = select(User)
    
    # Apply filters
    if role:
        stmt = stmt.where(User.role == role)
    
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    
    # For instructors, they can only see students and their own profile
    if current_user.role == UserRole.INSTRUCTOR:
        stmt = stmt.where(
            (User.role == UserRole.STUDENT) | (User.id == current_user.id)
        )
    
    # Apply pagination
    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)
    
    users = db.exec(stmt).all()
    
    return [UserResponse.from_orm(user) for user in users]


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new user (admin only)"""
    # Check if username already exists
    stmt = select(User).where(User.username == user_data.username)
    existing_user = db.exec(stmt).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    stmt = select(User).where(User.email == user_data.email)
    existing_email = db.exec(stmt).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=hashed_password,
        role=user_data.role,
        is_active=True,
        is_verified=True,  # Admin-created users are auto-verified
        created_at=datetime.utcnow()
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse.from_orm(db_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_instructor)
):
    """Get user by ID"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Instructors can only view students and themselves
    if current_user.role == UserRole.INSTRUCTOR:
        if user.role != UserRole.STUDENT and user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user"
            )
    
    return UserResponse.from_orm(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update user (admin only)"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update allowed fields
    allowed_fields = {
        'first_name', 'last_name', 'email', 'role', 'is_active', 'is_verified'
    }
    
    for field, value in user_data.items():
        if field in allowed_fields and hasattr(user, field):
            setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete user (admin only)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}


@router.get("/stats/overview")
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_instructor)
):
    """Get user statistics overview"""
    # Count users by role
    total_users = len(db.exec(select(User)).all())
    admins = len(db.exec(select(User).where(User.role == UserRole.ADMIN)).all())
    instructors = len(db.exec(select(User).where(User.role == UserRole.INSTRUCTOR)).all())
    students = len(db.exec(select(User).where(User.role == UserRole.STUDENT)).all())
    
    # Count active users
    active_users = len(db.exec(select(User).where(User.is_active == True)).all())
    verified_users = len(db.exec(select(User).where(User.is_verified == True)).all())
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "verified_users": verified_users,
        "by_role": {
            "admins": admins,
            "instructors": instructors,
            "students": students
        }
    } 