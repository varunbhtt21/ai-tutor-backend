"""
Course enrollment model
"""

from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime


class CourseEnrollment(SQLModel, table=True):
    """Track student enrollments in courses"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="user.id")
    course_id: int = Field(foreign_key="course.id") 
    
    # Enrollment status
    status: str = Field(default="active")  # active, completed, dropped, suspended
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Progress tracking
    progress_percentage: float = Field(default=0.0)
    last_accessed_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    student: "User" = Relationship()
    course: "Course" = Relationship()
    
    class Config:
        schema_extra = {
            "example": {
                "student_id": 1,
                "course_id": 1,
                "status": "active",
                "progress_percentage": 0.0
            }
        }
    
    def __repr__(self):
        return f"<CourseEnrollment(student_id={self.student_id}, course_id={self.course_id}, status={self.status})>" 