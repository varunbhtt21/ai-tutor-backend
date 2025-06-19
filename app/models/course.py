"""
Course model and related schemas
"""

from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime


class Course(SQLModel, table=True):
    """Course model for organizing learning sessions"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    
    # Course metadata
    subject: Optional[str] = Field(default=None, max_length=100)
    difficulty_level: Optional[str] = Field(default="beginner", max_length=20)
    estimated_duration: Optional[int] = Field(default=None)  # in minutes
    
    # Course settings
    is_active: bool = Field(default=True)
    is_public: bool = Field(default=False)
    requires_approval: bool = Field(default=False)
    
    # Course content configuration
    tags: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    learning_objectives: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    prerequisites: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    
    # Instructor and timestamps
    instructor_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    instructor: "User" = Relationship(back_populates="created_courses")
    sessions: List["Session"] = Relationship(back_populates="course")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Guitar Chords 101",
                "description": "Learn basic guitar chords through interactive lessons",
                "subject": "Music",
                "difficulty_level": "beginner",
                "estimated_duration": 120,
                "learning_objectives": [
                    "Master basic major and minor chords",
                    "Understand chord progressions",
                    "Play simple songs"
                ],
                "tags": {"instrument": "guitar", "style": "acoustic"}
            }
        }
    
    def __repr__(self):
        return f"<Course(id={self.id}, name={self.name}, instructor_id={self.instructor_id})>"
    
    @property
    def total_sessions(self) -> int:
        """Get total number of sessions in this course"""
        return len(self.sessions) if self.sessions else 0
    
    def can_be_accessed_by(self, user: "User") -> bool:
        """Check if a user can access this course"""
        if not self.is_active:
            return False
        
        # Instructor and admin can always access
        if user.id == self.instructor_id or user.role == "admin":
            return True
        
        # Public courses can be accessed by anyone
        if self.is_public:
            return True
        
        # TODO: Add enrollment logic here
        return False 