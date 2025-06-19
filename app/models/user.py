"""
User model and related schemas
"""

from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles in the system"""
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"


class User(SQLModel, table=True):
    """User model for authentication and authorization"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, min_length=3, max_length=50)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: UserRole = Field(default=UserRole.STUDENT)
    
    # Profile information
    first_name: Optional[str] = Field(default=None, max_length=50)
    last_name: Optional[str] = Field(default=None, max_length=50)
    avatar_url: Optional[str] = Field(default=None)
    
    # Status and timestamps
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    last_login: Optional[datetime] = Field(default=None)
    
    # Relationships
    created_courses: List["Course"] = Relationship(back_populates="instructor")
    student_states: List["StudentState"] = Relationship(back_populates="student")
    event_logs: List["EventLog"] = Relationship(back_populates="student")
    coin_transactions: List["CoinTransaction"] = Relationship(back_populates="student")
    
    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "role": "student",
                "first_name": "John",
                "last_name": "Doe"
            }
        }
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def is_instructor_or_admin(self) -> bool:
        """Check if user has instructor or admin privileges"""
        return self.role in [UserRole.INSTRUCTOR, UserRole.ADMIN] 