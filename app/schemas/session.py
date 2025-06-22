"""
Session and Bubble Graph related Pydantic schemas
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

from app.models.session import BubbleType, SessionStatus


class BubbleNodeSchema(BaseModel):
    """Schema for bubble node in graph JSON"""
    id: str = Field(..., min_length=1)
    type: BubbleType
    title: str = Field(..., min_length=1, max_length=200)
    x: float = Field(..., description="X coordinate in graph")
    y: float = Field(..., description="Y coordinate in graph")
    
    # Optional properties
    width: Optional[float] = 150
    height: Optional[float] = 80
    color: Optional[str] = None


class GraphEdgeSchema(BaseModel):
    """Schema for graph edge"""
    from_node: str
    to_node: str
    
    # Optional edge properties
    label: Optional[str] = None
    condition: Optional[str] = None  # For conditional edges


class BubbleGraphSchema(BaseModel):
    """Schema for complete bubble graph"""
    start_node: str = Field(..., min_length=1)
    nodes: List[BubbleNodeSchema] = Field(..., min_items=1)
    edges: List[GraphEdgeSchema] = Field(default_factory=list)
    
    @validator('nodes')
    def validate_nodes(cls, v):
        """Validate nodes have unique IDs"""
        node_ids = [node.id for node in v]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Node IDs must be unique")
        return v
    
    @validator('start_node')
    def validate_start_node(cls, v, values):
        """Validate start_node exists in nodes"""
        if 'nodes' in values:
            node_ids = [node.id for node in values['nodes']]
            if v not in node_ids:
                raise ValueError("start_node must exist in nodes")
        return v
    
    @validator('edges')
    def validate_edges(cls, v, values):
        """Validate edges reference existing nodes"""
        if 'nodes' in values:
            node_ids = [node.id for node in values['nodes']]
            for edge in v:
                if edge.from_node not in node_ids:
                    raise ValueError(f"Edge from_node '{edge.from_node}' not found in nodes")
                if edge.to_node not in node_ids:
                    raise ValueError(f"Edge to_node '{edge.to_node}' not found in nodes")
        return v


class BubbleNodeCreate(BaseModel):
    """Schema for creating a bubble node"""
    node_id: str = Field(..., min_length=1)
    type: BubbleType
    title: str = Field(..., min_length=1, max_length=200)
    content_md: Optional[str] = None
    
    # Task-specific fields
    code_template: Optional[str] = None
    test_cases: Optional[Dict[str, Any]] = None
    expected_output: Optional[str] = None
    hints: Optional[List[str]] = None
    
    # AI tutor prompts
    tutor_prompt: Optional[str] = None
    success_message: Optional[str] = None
    failure_message: Optional[str] = None
    
    # Gamification
    coin_reward: int = Field(10, ge=0)
    bonus_conditions: Optional[Dict[str, Any]] = None


class BubbleNodeResponse(BubbleNodeCreate):
    """Schema for bubble node response"""
    id: int
    session_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    """Schema for session creation"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    course_id: int
    
    # Session scheduling
    start_time: datetime
    end_time: datetime
    
    # Bubble graph
    graph_json: BubbleGraphSchema
    
    # Session settings
    max_attempts_per_bubble: int = Field(3, ge=1, le=10)
    coins_per_bubble: int = Field(10, ge=0)
    time_limit_minutes: Optional[int] = Field(None, gt=0)
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Validate end_time is after start_time"""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError("end_time must be after start_time")
        return v


class SessionUpdate(BaseModel):
    """Schema for session updates"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[SessionStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    graph_json: Optional[BubbleGraphSchema] = None
    max_attempts_per_bubble: Optional[int] = Field(None, ge=1, le=10)
    coins_per_bubble: Optional[int] = Field(None, ge=0)
    time_limit_minutes: Optional[int] = Field(None, gt=0)


class SessionResponse(BaseModel):
    """Schema for session response"""
    id: int
    name: str
    description: Optional[str] = None
    course_id: int
    status: SessionStatus
    start_time: datetime
    end_time: datetime
    graph_json: Dict[str, Any]  # Raw JSON for client
    max_attempts_per_bubble: int
    coins_per_bubble: int
    time_limit_minutes: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    
    # Computed fields
    total_bubbles: int = 0
    student_count: int = 0
    avg_completion_time: Optional[float] = None
    is_active: bool = False
    is_upcoming: bool = False
    is_past: bool = False

    class Config:
        from_attributes = True


class StudentStateResponse(BaseModel):
    """Schema for student state response"""
    id: int
    student_id: int
    session_id: int
    current_node_id: Optional[str] = None
    completed_nodes: List[str]
    failed_attempts: Dict[str, int]
    total_coins: int
    is_completed: bool
    completion_percentage: float
    started_at: datetime
    last_activity_at: datetime
    completed_at: Optional[datetime] = None
    total_time_spent: int  # seconds

    class Config:
        from_attributes = True


class GraphValidationResponse(BaseModel):
    """Schema for graph validation response"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    node_count: int
    edge_count: int
    has_cycles: bool
    unreachable_nodes: List[str] = Field(default_factory=list)


class SessionListResponse(BaseModel):
    """Schema for session list response"""
    sessions: List[SessionResponse]
    total: int
    page: int
    per_page: int


class BubbleAdvanceRequest(BaseModel):
    """Schema for advancing to next bubble"""
    node_id: str
    student_response: str
    code_output: Optional[str] = None
    time_spent: Optional[int] = None  # seconds


class BubbleAdvanceResponse(BaseModel):
    """Schema for bubble advancement response"""
    success: bool
    next_node_id: Optional[str] = None
    feedback: str
    coins_earned: int = 0
    is_session_complete: bool = False
    hints_available: List[str] = Field(default_factory=list) 