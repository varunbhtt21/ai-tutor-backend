"""
Analytics and gamification models
"""

from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Types of events to track"""
    SESSION_START = "session_start"
    SESSION_COMPLETE = "session_complete"
    BUBBLE_ENTER = "bubble_enter"
    BUBBLE_SUCCESS = "bubble_success"
    BUBBLE_FAIL = "bubble_fail"
    HINT_REQUESTED = "hint_requested"
    CODE_EXECUTED = "code_executed"
    TUTOR_INTERACTION = "tutor_interaction"
    # New event types for enhanced tracking
    CHAT_MESSAGE = "chat_message"
    CODE_CHANGE = "code_change"
    IDLE_DETECTED = "idle_detected"
    STRUGGLE_DETECTED = "struggle_detected"
    HELP_REQUESTED = "help_requested"


class TransactionType(str, Enum):
    """Types of coin transactions"""
    EARNED = "earned"         # Coins earned from completing bubbles
    BONUS = "bonus"           # Bonus coins from achievements
    SPENT = "spent"           # Coins spent on hints/help
    REFUNDED = "refunded"     # Coins refunded


class StruggleSeverity(str, Enum):
    """Severity levels for struggle detection"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MessageType(str, Enum):
    """Types of chat messages"""
    STUDENT_QUESTION = "student_question"
    AI_RESPONSE = "ai_response"
    HINT_REQUEST = "hint_request"
    CODE_QUESTION = "code_question"
    CLARIFICATION = "clarification"
    ENCOURAGEMENT = "encouragement"


class EventLog(SQLModel, table=True):
    """Track all student interactions and events for analytics"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Event details
    event_type: EventType
    student_id: int = Field(foreign_key="user.id")
    session_id: Optional[int] = Field(default=None, foreign_key="session.id")
    node_id: Optional[str] = Field(default=None)
    
    # Event data
    payload: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Performance metrics
    response_time_ms: Optional[int] = Field(default=None)
    success: Optional[bool] = Field(default=None)
    score: Optional[float] = Field(default=None)
    
    # Context
    user_agent: Optional[str] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    student: "User" = Relationship(back_populates="event_logs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "bubble_success",
                "node_id": "c_major_chord",
                "payload": {
                    "attempts": 2,
                    "time_spent": 45,
                    "hints_used": 1
                },
                "response_time_ms": 250,
                "success": True,
                "score": 85.5
            }
        }
    
    def __repr__(self):
        return f"<EventLog(id={self.id}, event_type={self.event_type}, student_id={self.student_id})>"


class StudentSessionTracking(SQLModel, table=True):
    """Enhanced session-level tracking building on EventLog foundation"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Core identifiers
    session_id: int = Field(foreign_key="session.id")
    student_id: int = Field(foreign_key="user.id")
    
    # Session timeline
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    # Progress tracking
    current_node_id: Optional[str] = None
    progress_percentage: float = Field(default=0.0)
    nodes_completed: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    nodes_attempted: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Engagement metrics
    total_interactions: int = Field(default=0)
    active_time_seconds: int = Field(default=0)
    idle_time_seconds: int = Field(default=0)
    total_chat_messages: int = Field(default=0)
    total_code_changes: int = Field(default=0)
    
    # Performance metrics
    success_rate: float = Field(default=0.0)
    average_response_time_ms: float = Field(default=0.0)
    hints_used: int = Field(default=0)
    help_requests: int = Field(default=0)
    
    # Struggle detection
    current_struggle_score: float = Field(default=0.0)
    struggle_alerts_triggered: int = Field(default=0)
    consecutive_failures: int = Field(default=0)
    
    # Learning insights
    learning_style_indicators: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    engagement_patterns: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Relationships
    student: "User" = Relationship()
    session: "Session" = Relationship()
    chat_interactions: List["ChatInteraction"] = Relationship(back_populates="session_tracking")
    code_interactions: List["CodeInteraction"] = Relationship(back_populates="session_tracking")
    
    def __repr__(self):
        return f"<StudentSessionTracking(id={self.id}, student_id={self.student_id}, session_id={self.session_id})>"


class ChatInteraction(SQLModel, table=True):
    """Detailed chat interaction tracking"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Core identifiers
    session_tracking_id: int = Field(foreign_key="studentsessiontracking.id")
    student_id: int = Field(foreign_key="user.id")
    session_id: int = Field(foreign_key="session.id")
    
    # Message details
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_type: MessageType
    content: str = Field(max_length=5000)
    node_id: Optional[str] = None
    
    # Response metrics
    response_time_ms: Optional[int] = None
    character_count: int = Field(default=0)
    word_count: int = Field(default=0)
    
    # Context and analysis
    emotional_tone: Optional[str] = None  # positive, negative, neutral, frustrated, confused
    intent_classification: Optional[str] = None  # question, clarification, help_request, etc.
    complexity_score: Optional[float] = None  # 1-10 scale
    
    # AI analysis
    ai_confidence_score: Optional[float] = None
    requires_human_intervention: bool = Field(default=False)
    
    # Additional metadata
    additional_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Relationships
    session_tracking: StudentSessionTracking = Relationship(back_populates="chat_interactions")
    
    def __repr__(self):
        return f"<ChatInteraction(id={self.id}, student_id={self.student_id}, message_type={self.message_type})>"


class CodeInteraction(SQLModel, table=True):
    """Detailed code interaction and change tracking"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Core identifiers
    session_tracking_id: int = Field(foreign_key="studentsessiontracking.id")
    student_id: int = Field(foreign_key="user.id")
    session_id: int = Field(foreign_key="session.id")
    
    # Code details
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    node_id: Optional[str] = None
    interaction_type: str = Field(default="keypress")  # keypress, paste, delete, run, submit
    
    # Code content
    code_snapshot: str = Field(max_length=10000)
    code_diff: Optional[str] = Field(default=None, max_length=2000)
    language: str = Field(default="python")
    
    # Metrics
    characters_added: int = Field(default=0)
    characters_deleted: int = Field(default=0)
    lines_of_code: int = Field(default=0)
    
    # Analysis
    syntax_errors: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    execution_result: Optional[str] = Field(default=None, max_length=2000)
    execution_success: Optional[bool] = None
    execution_time_ms: Optional[int] = None
    
    # Progress indicators
    is_significant_change: bool = Field(default=False)  # More than just typos
    completion_progress: float = Field(default=0.0)  # 0-1 estimate of task completion
    
    # Additional metadata
    additional_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Relationships
    session_tracking: StudentSessionTracking = Relationship(back_populates="code_interactions")
    
    def __repr__(self):
        return f"<CodeInteraction(id={self.id}, student_id={self.student_id}, interaction_type={self.interaction_type})>"


class CodeSubmission(SQLModel, table=True):
    """Track code submissions and evaluation results"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Core identifiers
    session_tracking_id: int = Field(foreign_key="studentsessiontracking.id")
    student_id: int = Field(foreign_key="user.id")
    session_id: int = Field(foreign_key="session.id")
    node_id: str
    
    # Submission details
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    submission_number: int = Field(default=1)  # 1st attempt, 2nd attempt, etc.
    
    # Code content
    submitted_code: str = Field(max_length=10000)
    language: str = Field(default="python")
    
    # Evaluation results
    is_correct: bool = Field(default=False)
    score: Optional[float] = None  # 0-100 score if partial credit
    test_results: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Performance metrics
    execution_time_ms: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    
    # Error analysis
    compilation_errors: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    runtime_errors: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    logic_errors: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # AI feedback
    ai_feedback: Optional[str] = Field(default=None, max_length=2000)
    suggested_improvements: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Time tracking
    time_since_start_seconds: int = Field(default=0)
    time_since_last_attempt_seconds: Optional[int] = None
    
    # Relationships
    session_tracking: StudentSessionTracking = Relationship()
    
    def __repr__(self):
        return f"<CodeSubmission(id={self.id}, student_id={self.student_id}, node_id={self.node_id}, is_correct={self.is_correct})>"


class StruggleAnalysis(SQLModel, table=True):
    """Real-time struggle detection and analysis"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Core identifiers
    session_tracking_id: int = Field(foreign_key="studentsessiontracking.id")
    student_id: int = Field(foreign_key="user.id")
    session_id: int = Field(foreign_key="session.id")
    node_id: Optional[str] = None
    
    # Detection details
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    struggle_score: float = Field(default=0.0)  # 0-100 scale
    severity: StruggleSeverity = Field(default=StruggleSeverity.LOW)
    
    # Struggle indicators
    indicators: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    # Example indicators:
    # {
    #   "repetitive_questions": 3,
    #   "idle_time_minutes": 5,
    #   "consecutive_errors": 4,
    #   "help_requests": 2,
    #   "frustration_signals": ["repeated_deletions", "rapid_typing"]
    # }
    
    # AI analysis
    ai_analysis: Optional[str] = Field(default=None, max_length=1000)
    recommendations: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    intervention_suggested: bool = Field(default=False)
    
    # Resolution tracking
    resolved: bool = Field(default=False)
    resolution_time_seconds: Optional[int] = None
    resolution_method: Optional[str] = None  # "hint", "instructor_help", "breakthrough", etc.
    
    # Instructor notification
    instructor_notified: bool = Field(default=False)
    instructor_response_time_seconds: Optional[int] = None
    
    # Relationships
    session_tracking: StudentSessionTracking = Relationship()
    
    def __repr__(self):
        return f"<StruggleAnalysis(id={self.id}, student_id={self.student_id}, severity={self.severity}, score={self.struggle_score})>"


class StudentLearningProfile(SQLModel, table=True):
    """Aggregated learning insights and patterns for each student"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Core identifiers
    student_id: int = Field(foreign_key="user.id", unique=True)
    
    # Profile metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Learning style analysis
    learning_style: Optional[str] = None  # visual, auditory, kinesthetic, mixed
    learning_style_confidence: float = Field(default=0.0)  # 0-1 confidence score
    
    # Performance patterns
    preferred_time_of_day: Optional[str] = None  # morning, afternoon, evening
    average_session_duration_minutes: float = Field(default=0.0)
    optimal_session_length_minutes: Optional[int] = None
    
    # Interaction patterns
    average_response_time_ms: float = Field(default=0.0)
    preferred_help_method: Optional[str] = None  # hints, chat, examples
    collaboration_preference: Optional[str] = None  # independent, collaborative
    
    # Struggle patterns
    common_struggle_areas: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    struggle_recovery_methods: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    resilience_score: float = Field(default=50.0)  # 0-100 scale
    
    # Motivation patterns
    motivation_drivers: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    engagement_triggers: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Progress metrics
    overall_success_rate: float = Field(default=0.0)
    average_completion_time_ratio: float = Field(default=1.0)  # actual/expected time
    consistency_score: float = Field(default=50.0)  # 0-100 scale
    
    # AI insights
    ai_generated_insights: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    personalized_recommendations: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Statistical data
    total_sessions: int = Field(default=0)
    total_study_time_hours: float = Field(default=0.0)
    last_activity_date: Optional[datetime] = None
    
    # Relationships
    student: "User" = Relationship()
    
    def __repr__(self):
        return f"<StudentLearningProfile(id={self.id}, student_id={self.student_id}, learning_style={self.learning_style})>"


class CoinTransaction(SQLModel, table=True):
    """Track coin transactions for gamification"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Transaction details
    student_id: int = Field(foreign_key="user.id")
    transaction_type: TransactionType
    amount: int  # Can be positive (earned) or negative (spent)
    
    # Context
    session_id: Optional[int] = Field(default=None, foreign_key="session.id")
    node_id: Optional[str] = Field(default=None)
    description: str = Field(max_length=200)
    
    # Transaction metadata
    transaction_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Balances (for easier queries)
    balance_before: int = Field(default=0)
    balance_after: int = Field(default=0)
    
    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    student: "User" = Relationship(back_populates="coin_transactions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction_type": "earned",
                "amount": 15,
                "node_id": "c_major_chord",
                "description": "Completed C Major Chord task",
                "balance_before": 25,
                "balance_after": 40,
                "transaction_metadata": {
                    "bonus_multiplier": 1.5,
                    "completion_time": 30
                }
            }
        }
    
    def __repr__(self):
        return f"<CoinTransaction(id={self.id}, student_id={self.student_id}, amount={self.amount}, type={self.transaction_type})>"
    
    @property
    def is_earning(self) -> bool:
        """Check if this is an earning transaction"""
        return self.transaction_type in [TransactionType.EARNED, TransactionType.BONUS]
    
    @property
    def is_spending(self) -> bool:
        """Check if this is a spending transaction"""
        return self.transaction_type == TransactionType.SPENT 