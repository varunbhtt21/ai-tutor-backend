"""
Analytics and gamification models
"""

from typing import Optional, Dict, Any
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


class TransactionType(str, Enum):
    """Types of coin transactions"""
    EARNED = "earned"         # Coins earned from completing bubbles
    BONUS = "bonus"           # Bonus coins from achievements
    SPENT = "spent"           # Coins spent on hints/help
    REFUNDED = "refunded"     # Coins refunded


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