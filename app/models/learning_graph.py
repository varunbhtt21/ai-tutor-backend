from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database import Base

class DifficultyLevel(enum.IntEnum):
    """Difficulty levels for learning concepts"""
    BEGINNER = 1
    BASIC = 2
    INTERMEDIATE = 3
    ADVANCED = 4
    EXPERT = 5

class PrerequisiteType(enum.Enum):
    """Types of prerequisite relationships"""
    HARD = "hard"          # Must understand A before B
    SOFT = "soft"          # Helpful to understand A before B  
    REINFORCEMENT = "reinforcement"  # A and B reinforce each other

class LearningConcept(Base):
    """Core learning concepts in the curriculum"""
    __tablename__ = "learning_concepts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    slug = Column(String(200), unique=True, nullable=False, index=True)  # URL-friendly name
    description = Column(Text, nullable=False)
    learning_objectives = Column(JSON)  # List of specific objectives
    
    # Metadata
    difficulty_level = Column(Integer, default=DifficultyLevel.BEGINNER)
    estimated_time_minutes = Column(Integer, default=30)
    category = Column(String(100), nullable=False, index=True)  # e.g., "python-basics", "data-structures"
    
    # Content structure
    explanation_text = Column(Text)
    code_examples = Column(JSON)  # List of code examples with explanations
    visual_aids = Column(JSON)    # Links to diagrams, visualizations
    practice_exercises = Column(JSON)  # List of practice problems
    
    # Assessment
    assessment_questions = Column(JSON)  # Knowledge check questions
    mastery_threshold = Column(Float, default=0.75)  # Required score to "master" concept
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    prerequisites = relationship("ConceptPrerequisite", foreign_keys="ConceptPrerequisite.concept_id", back_populates="concept")
    required_for = relationship("ConceptPrerequisite", foreign_keys="ConceptPrerequisite.prerequisite_id", back_populates="prerequisite")
    student_progress = relationship("StudentProgress", back_populates="concept")

class ConceptPrerequisite(Base):
    """Prerequisite relationships between concepts"""
    __tablename__ = "concept_prerequisites"
    
    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("learning_concepts.id"), nullable=False)
    prerequisite_id = Column(Integer, ForeignKey("learning_concepts.id"), nullable=False)
    
    prerequisite_type = Column(String(20), default=PrerequisiteType.HARD.value)
    strength = Column(Float, default=1.0)  # How important this prerequisite is (0.0-1.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    concept = relationship("LearningConcept", foreign_keys=[concept_id], back_populates="prerequisites")
    prerequisite = relationship("LearningConcept", foreign_keys=[prerequisite_id], back_populates="required_for")

class StudentProgress(Base):
    """Track individual student progress through concepts"""
    __tablename__ = "student_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    concept_id = Column(Integer, ForeignKey("learning_concepts.id"), nullable=False)
    
    # Progress metrics
    mastery_score = Column(Float, default=0.0)  # 0.0 - 1.0 scale
    confidence_level = Column(Float, default=0.5)  # Student's self-reported confidence
    time_spent_minutes = Column(Integer, default=0)
    attempts_count = Column(Integer, default=0)
    
    # Status tracking
    status = Column(String(20), default="not_started")  # not_started, in_progress, completed, mastered
    first_introduced_at = Column(DateTime)
    last_practiced_at = Column(DateTime)
    mastered_at = Column(DateTime)
    
    # Learning pattern analysis
    learning_velocity = Column(Float, default=1.0)  # How quickly student learns (relative to average)
    struggle_indicators = Column(JSON)  # Areas where student had difficulty
    preferred_explanations = Column(JSON)  # Which explanation types worked best
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    concept = relationship("LearningConcept", back_populates="student_progress")

class LearningPath(Base):
    """Personalized learning sequences for students"""
    __tablename__ = "learning_paths"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    
    # Path metadata
    name = Column(String(200), nullable=False)  # e.g., "Python Fundamentals"
    description = Column(Text)
    goal = Column(String(500))  # Student's learning goal
    
    # Sequence definition
    concept_sequence = Column(JSON)  # Ordered list of concept IDs
    current_position = Column(Integer, default=0)  # Index in concept_sequence
    
    # Adaptation parameters
    difficulty_preference = Column(Float, default=0.5)  # 0.0=easy, 1.0=challenging
    pacing_preference = Column(String(20), default="normal")  # slow, normal, fast
    learning_style = Column(JSON)  # Preferences for visual/textual/hands-on
    
    # Progress tracking
    completion_percentage = Column(Float, default=0.0)
    estimated_completion_hours = Column(Float)
    actual_time_spent_minutes = Column(Integer, default=0)
    
    # Status
    status = Column(String(20), default="active")  # active, paused, completed, abandoned
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AssessmentResult(Base):
    """Track assessment results for concepts"""
    __tablename__ = "assessment_results"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    concept_id = Column(Integer, ForeignKey("learning_concepts.id"), nullable=False)
    
    # Assessment data
    questions_asked = Column(JSON)  # List of questions and student responses
    score = Column(Float, nullable=False)  # 0.0 - 1.0
    max_possible_score = Column(Float, default=1.0)
    
    # Context
    assessment_type = Column(String(50), default="knowledge_check")  # knowledge_check, practice, final
    taken_at = Column(DateTime(timezone=True), server_default=func.now())
    duration_minutes = Column(Integer)
    
    # Analysis
    strengths = Column(JSON)  # Areas of strong performance
    weaknesses = Column(JSON)  # Areas needing improvement
    recommendations = Column(JSON)  # Suggested next steps
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 