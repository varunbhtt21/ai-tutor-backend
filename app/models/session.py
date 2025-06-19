"""
Session, BubbleNode, and StudentState models
Core models for the bubble graph learning experience
"""

from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from enum import Enum


class BubbleType(str, Enum):
    """Types of learning bubbles"""
    CONCEPT = "concept"      # Explanation/teaching bubble
    TASK = "task"           # Practice/exercise bubble
    QUIZ = "quiz"           # Assessment bubble
    DEMO = "demo"           # Demonstration bubble
    SUMMARY = "summary"     # Wrap-up bubble


class SessionStatus(str, Enum):
    """Session status"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Session(SQLModel, table=True):
    """Learning session with bubble graph structure"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    
    # Session configuration
    course_id: int = Field(foreign_key="course.id")
    status: SessionStatus = Field(default=SessionStatus.DRAFT)
    
    # Session scheduling
    start_time: datetime = Field(description="When the session starts")
    end_time: datetime = Field(description="When the session ends")
    
    # Bubble graph structure stored as JSON
    graph_json: Dict[str, Any] = Field(sa_column=Column(JSON))
    
    # Session settings
    max_attempts_per_bubble: int = Field(default=3)
    coins_per_bubble: int = Field(default=10)
    time_limit_minutes: Optional[int] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    published_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    course: "Course" = Relationship(back_populates="sessions")
    bubble_nodes: List["BubbleNode"] = Relationship(back_populates="session")
    student_states: List["StudentState"] = Relationship(back_populates="session")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Basic Chord Progression",
                "description": "Learn C-Am-F-G chord progression",
                "graph_json": {
                    "nodes": [
                        {"id": "start", "type": "concept", "title": "Welcome"},
                        {"id": "c_chord", "type": "task", "title": "C Major Chord"}
                    ],
                    "edges": [
                        {"from": "start", "to": "c_chord"}
                    ]
                }
            }
        }
    
    def __repr__(self):
        return f"<Session(id={self.id}, name={self.name}, course_id={self.course_id})>"
    
    @property
    def is_published(self) -> bool:
        """Check if session is published"""
        return self.status == SessionStatus.PUBLISHED
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active"""
        now = datetime.utcnow()
        return self.is_published and self.start_time <= now <= self.end_time
    
    @property
    def is_upcoming(self) -> bool:
        """Check if session is upcoming"""
        now = datetime.utcnow()
        return self.is_published and now < self.start_time
    
    @property
    def is_past(self) -> bool:
        """Check if session is past"""
        now = datetime.utcnow()
        return now > self.end_time
    
    def get_start_node_id(self) -> Optional[str]:
        """Get the starting node ID from graph"""
        if not self.graph_json or "start_node" not in self.graph_json:
            return None
        return self.graph_json["start_node"]


class BubbleNode(SQLModel, table=True):
    """Individual learning bubble/node in a session"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    node_id: str = Field(index=True)  # Unique within session
    session_id: int = Field(foreign_key="session.id")
    
    # Node configuration
    type: BubbleType
    title: str = Field(min_length=1, max_length=200)
    content_md: Optional[str] = Field(default=None)  # Markdown content
    
    # Task-specific fields
    code_template: Optional[str] = Field(default=None)
    test_cases: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    expected_output: Optional[str] = Field(default=None)
    hints: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    
    # AI tutor prompts
    tutor_prompt: Optional[str] = Field(default=None)
    success_message: Optional[str] = Field(default=None)
    failure_message: Optional[str] = Field(default=None)
    
    # Gamification
    coin_reward: int = Field(default=10)
    bonus_conditions: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    session: Session = Relationship(back_populates="bubble_nodes")
    
    class Config:
        schema_extra = {
            "example": {
                "node_id": "c_major_chord",
                "type": "task",
                "title": "Learn C Major Chord",
                "content_md": "Place your fingers on the 1st fret of B string, 2nd fret of D string, and 3rd fret of A string.",
                "hints": ["Start with the easiest finger placement", "Practice the transition slowly"]
            }
        }
    
    def __repr__(self):
        return f"<BubbleNode(id={self.id}, node_id={self.node_id}, type={self.type})>"


class StudentState(SQLModel, table=True):
    """Track student progress through a session"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="user.id")
    session_id: int = Field(foreign_key="session.id")
    
    # Progress tracking
    current_node_id: Optional[str] = Field(default=None)
    completed_nodes: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    failed_attempts: Dict[str, int] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Session state
    total_coins: int = Field(default=0)
    is_completed: bool = Field(default=False)
    completion_percentage: float = Field(default=0.0)
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    total_time_spent: int = Field(default=0)  # in seconds
    
    # Relationships
    student: "User" = Relationship(back_populates="student_states")
    session: Session = Relationship(back_populates="student_states")
    
    class Config:
        schema_extra = {
            "example": {
                "current_node_id": "c_major_chord",
                "completed_nodes": ["welcome", "intro"],
                "total_coins": 20,
                "completion_percentage": 25.0
            }
        }
    
    def __repr__(self):
        return f"<StudentState(student_id={self.student_id}, session_id={self.session_id}, progress={self.completion_percentage}%)>"
    
    def add_completed_node(self, node_id: str):
        """Mark a node as completed"""
        if node_id not in self.completed_nodes:
            self.completed_nodes.append(node_id)
    
    def increment_failed_attempt(self, node_id: str):
        """Increment failed attempts for a node"""
        if node_id not in self.failed_attempts:
            self.failed_attempts[node_id] = 0
        self.failed_attempts[node_id] += 1
    
    def get_failed_attempts(self, node_id: str) -> int:
        """Get number of failed attempts for a node"""
        return self.failed_attempts.get(node_id, 0) 