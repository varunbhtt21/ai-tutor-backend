"""
Course-related Pydantic schemas
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CourseBase(BaseModel):
    """Base course schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    subject: Optional[str] = Field(None, max_length=100)
    difficulty_level: str = Field("beginner", max_length=20)
    estimated_duration: Optional[int] = None  # in minutes


class CourseCreate(CourseBase):
    """Schema for course creation"""
    is_public: bool = False
    requires_approval: bool = False
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    tags: Optional[Dict[str, Any]] = None


class CourseUpdate(BaseModel):
    """Schema for course updates"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    subject: Optional[str] = Field(None, max_length=100)
    difficulty_level: Optional[str] = Field(None, max_length=20)
    estimated_duration: Optional[int] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    requires_approval: Optional[bool] = None
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    tags: Optional[Dict[str, Any]] = None


class CourseResponse(CourseBase):
    """Schema for course response"""
    id: int
    instructor_id: int
    is_active: bool
    is_public: bool
    requires_approval: bool
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    tags: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    total_sessions: int = 0
    student_count: int = 0

    class Config:
        from_attributes = True


class CourseListResponse(BaseModel):
    """Schema for course list response"""
    courses: List[CourseResponse]
    total: int
    page: int
    per_page: int 