"""
Enrollment-related Pydantic schemas
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class EnrollmentCreate(BaseModel):
    """Schema for enrolling students in courses"""
    student_emails: List[str] = Field(..., description="List of student email addresses to enroll")
    course_id: int = Field(..., description="Course ID to enroll students in")


class EnrollmentResponse(BaseModel):
    """Schema for enrollment response"""
    id: int
    student_id: int
    course_id: int
    status: str
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    progress_percentage: float
    last_accessed_at: Optional[datetime] = None
    
    # Related data
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    course_name: Optional[str] = None

    class Config:
        from_attributes = True


class BulkEnrollmentResponse(BaseModel):
    """Schema for bulk enrollment response"""
    successful_enrollments: List[EnrollmentResponse]
    failed_enrollments: List[dict]  # Contains email and error reason
    total_processed: int
    successful_count: int
    failed_count: int


class EnrollmentListResponse(BaseModel):
    """Schema for enrollment list response"""
    enrollments: List[EnrollmentResponse]
    total: int
    page: int
    per_page: int 