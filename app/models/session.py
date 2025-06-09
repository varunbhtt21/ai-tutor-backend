from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.sql import func
from app.database import Base

class LearningSession(Base):
    """Model for tracking learning sessions"""
    __tablename__ = "learning_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(String(255), index=True, nullable=False)
    lesson_id = Column(String(255), index=True, nullable=False)
    status = Column(String(50), default="active")  # active, completed, paused
    
    # Audio/TTS preferences
    audio_enabled = Column(Boolean, default=True)
    preferred_voice = Column(String(50), default="alloy")  # TTS voice preference
    speech_rate = Column(Float, default=1.0)  # Speech speed (0.25 - 4.0)
    audio_format = Column(String(10), default="mp3")  # Audio format preference
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ConversationLog(Base):
    """Model for logging conversation interactions"""
    __tablename__ = "conversation_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True, nullable=False)
    node_id = Column(String(255), index=True, nullable=True)  # Plan-Graph node
    user_input = Column(Text, nullable=True)
    ai_response = Column(Text, nullable=True)
    audio_duration = Column(Float, nullable=True)  # seconds
    response_latency = Column(Float, nullable=True)  # milliseconds
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LearningMetrics(Base):
    """Model for tracking learning progress metrics"""
    __tablename__ = "learning_metrics"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True, nullable=False)
    node_id = Column(String(255), index=True, nullable=False)
    metric_type = Column(String(100), nullable=False)  # comprehension, engagement, etc
    metric_value = Column(Float, nullable=False)
    metadata_json = Column("metadata", Text, nullable=True)  # JSON string for additional data
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 