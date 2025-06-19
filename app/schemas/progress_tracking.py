"""
Progress Tracking Schemas - Models for advanced learning analytics
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum


class DifficultyLevel(str, Enum):
    """Difficulty levels for adaptive content"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LearningStyle(str, Enum):
    """Learning style preferences"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"


class MasteryStatus(str, Enum):
    """Mastery status levels"""
    BEGINNING = "beginning"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    MASTERED = "mastered"


class TrendDirection(str, Enum):
    """Trend directions"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"


class PerformanceMetrics(BaseModel):
    """Comprehensive performance metrics"""
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall performance score")
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Success rate accuracy")
    speed_score: float = Field(..., ge=0.0, le=1.0, description="Learning speed score")
    consistency: float = Field(..., ge=0.0, le=1.0, description="Performance consistency")
    improvement_rate: float = Field(..., ge=0.0, le=1.0, description="Rate of improvement")
    engagement_score: float = Field(..., ge=0.0, le=1.0, description="Engagement level")
    
    class Config:
        json_schema_extra = {
            "example": {
                "overall_score": 0.75,
                "accuracy": 0.82,
                "speed_score": 0.68,
                "consistency": 0.71,
                "improvement_rate": 0.85,
                "engagement_score": 0.73
            }
        }


class LearningPattern(BaseModel):
    """Identified learning behavior pattern"""
    pattern_type: str = Field(..., description="Type of pattern identified")
    description: str = Field(..., description="Human-readable pattern description")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in pattern detection")
    frequency: float = Field(..., ge=0.0, le=1.0, description="How often pattern occurs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "pattern_type": "temporal",
                "description": "Most active during evening hours (6-9 PM)",
                "confidence": 0.85,
                "frequency": 0.73
            }
        }


class SkillAssessment(BaseModel):
    """Assessment of specific skill domain"""
    skill_domain: str = Field(..., description="Name of skill domain")
    current_level: float = Field(..., ge=0.0, le=1.0, description="Current skill level")
    progress_rate: float = Field(..., ge=-1.0, le=1.0, description="Rate of progress")
    strengths: List[str] = Field(default_factory=list, description="Identified strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Areas for improvement")
    next_milestones: List[str] = Field(default_factory=list, description="Upcoming learning milestones")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in assessment")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "skill_domain": "problem_solving",
                "current_level": 0.72,
                "progress_rate": 0.15,
                "strengths": ["Logical thinking", "Pattern recognition"],
                "weaknesses": ["Complex algorithm design"],
                "next_milestones": ["Master dynamic programming", "Learn graph algorithms"],
                "confidence_score": 0.85
            }
        }


class LearningStyleProfile(BaseModel):
    """Student's learning style profile"""
    visual: float = Field(..., ge=0.0, le=1.0, description="Visual learning preference")
    auditory: float = Field(..., ge=0.0, le=1.0, description="Auditory learning preference")
    kinesthetic: float = Field(..., ge=0.0, le=1.0, description="Kinesthetic learning preference")
    reading_writing: float = Field(..., ge=0.0, le=1.0, description="Reading/writing learning preference")
    dominant_style: LearningStyle = Field(..., description="Most preferred learning style")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in style assessment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "visual": 0.85,
                "auditory": 0.45,
                "kinesthetic": 0.62,
                "reading_writing": 0.73,
                "dominant_style": "visual",
                "confidence": 0.78
            }
        }


class MasteryLevel(BaseModel):
    """Mastery level for specific topic"""
    topic: str = Field(..., description="Topic or concept name")
    level: MasteryStatus = Field(..., description="Current mastery level")
    score: float = Field(..., ge=0.0, le=1.0, description="Mastery score")
    consistency: float = Field(..., ge=0.0, le=1.0, description="Performance consistency")
    last_practiced: datetime = Field(..., description="Last time topic was practiced")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "recursion",
                "level": "proficient",
                "score": 0.78,
                "consistency": 0.82,
                "last_practiced": "2024-01-15T14:30:00Z"
            }
        }


class ProgressTrend(BaseModel):
    """Progress trend over time"""
    metric: str = Field(..., description="Metric being tracked")
    direction: TrendDirection = Field(..., description="Trend direction")
    magnitude: float = Field(..., ge=0.0, description="Magnitude of change")
    period: str = Field(..., description="Time period (day, week, month)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in trend")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metric": "overall_performance",
                "direction": "increasing",
                "magnitude": 0.12,
                "period": "week",
                "confidence": 0.85
            }
        }


class LearningGoal(BaseModel):
    """Personalized learning goal"""
    title: str = Field(..., description="Goal title")
    description: str = Field(..., description="Detailed goal description")
    target_metric: str = Field(..., description="Metric to improve")
    current_value: float = Field(..., description="Current value of metric")
    target_value: float = Field(..., description="Target value to achieve")
    deadline: datetime = Field(..., description="Goal deadline")
    priority: str = Field(..., description="Goal priority (high, medium, low)")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Current progress toward goal")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Improve Problem Solving Skills",
                "description": "Focus on algorithmic thinking and solution optimization",
                "target_metric": "problem_solving_score",
                "current_value": 0.65,
                "target_value": 0.80,
                "deadline": "2024-02-15T00:00:00Z",
                "priority": "high",
                "progress": 0.30
            }
        }


class AchievementBadge(BaseModel):
    """Achievement badge earned by student"""
    name: str = Field(..., description="Badge name")
    description: str = Field(..., description="Achievement description")
    category: str = Field(..., description="Badge category")
    earned_date: datetime = Field(..., description="Date badge was earned")
    points: int = Field(..., ge=0, description="Points awarded for badge")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Problem Solver",
                "description": "Successfully solved 50 programming problems",
                "category": "achievement",
                "earned_date": "2024-01-20T15:45:00Z",
                "points": 150
            }
        }


class StudySession(BaseModel):
    """Detailed study session information"""
    session_id: str = Field(..., description="Session identifier")
    start_time: datetime = Field(..., description="Session start time")
    end_time: Optional[datetime] = Field(None, description="Session end time")
    duration_minutes: Optional[int] = Field(None, description="Session duration")
    topics_covered: List[str] = Field(default_factory=list, description="Topics studied")
    activities_completed: int = Field(default=0, description="Number of activities completed")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Success rate in session")
    hints_used: int = Field(default=0, description="Number of hints used")
    engagement_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Engagement level")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_123",
                "start_time": "2024-01-20T14:00:00Z",
                "end_time": "2024-01-20T15:30:00Z",
                "duration_minutes": 90,
                "topics_covered": ["arrays", "sorting", "searching"],
                "activities_completed": 12,
                "success_rate": 0.83,
                "hints_used": 3,
                "engagement_score": 0.78
            }
        }


class DifficultyRecommendation(BaseModel):
    """Adaptive difficulty recommendation"""
    topic: str = Field(..., description="Topic for recommendation")
    current_level: str = Field(..., description="Current difficulty level")
    recommended_level: str = Field(..., description="Recommended adjustment")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in recommendation")
    reasoning: str = Field(..., description="Explanation for recommendation")
    expected_improvement: float = Field(..., description="Expected performance improvement")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "binary_search",
                "current_level": "intermediate",
                "recommended_level": "increase",
                "confidence": 0.85,
                "reasoning": "High success rate and low hint usage indicate readiness for more challenge",
                "expected_improvement": 0.15
            }
        }


class ProgressAnalysis(BaseModel):
    """Comprehensive progress analysis"""
    student_id: int = Field(..., description="Student identifier")
    analysis_period: timedelta = Field(..., description="Time period analyzed")
    performance_metrics: PerformanceMetrics = Field(..., description="Performance metrics")
    learning_patterns: List[LearningPattern] = Field(default_factory=list, description="Identified patterns")
    skill_assessments: List[SkillAssessment] = Field(default_factory=list, description="Skill assessments")
    learning_style_profile: LearningStyleProfile = Field(..., description="Learning style profile")
    mastery_levels: List[MasteryLevel] = Field(default_factory=list, description="Topic mastery levels")
    progress_trends: List[ProgressTrend] = Field(default_factory=list, description="Progress trends")
    recommendations: List[str] = Field(default_factory=list, description="Personalized recommendations")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis generation time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "student_id": 123,
                "analysis_period": "30 days",
                "performance_metrics": {
                    "overall_score": 0.75,
                    "accuracy": 0.82,
                    "speed_score": 0.68,
                    "consistency": 0.71,
                    "improvement_rate": 0.85,
                    "engagement_score": 0.73
                },
                "recommendations": [
                    "Focus on consistency in daily practice",
                    "Try more challenging problems in strong areas",
                    "Review fundamental concepts in weak areas"
                ]
            }
        }


class LearningInsight(BaseModel):
    """Learning insight or observation"""
    insight_type: str = Field(..., description="Type of insight")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed insight description")
    importance: str = Field(..., description="Importance level (high, medium, low)")
    actionable: bool = Field(..., description="Whether insight leads to actionable recommendations")
    related_metrics: List[str] = Field(default_factory=list, description="Related performance metrics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "insight_type": "learning_plateau",
                "title": "Performance Plateau Detected",
                "description": "Student's performance has remained stable for the past 2 weeks, suggesting need for new challenges",
                "importance": "medium",
                "actionable": True,
                "related_metrics": ["overall_score", "improvement_rate"]
            }
        }


class AdaptivePath(BaseModel):
    """Adaptive learning path recommendation"""
    path_id: str = Field(..., description="Learning path identifier")
    title: str = Field(..., description="Path title")
    description: str = Field(..., description="Path description")
    estimated_duration: int = Field(..., description="Estimated completion time in hours")
    difficulty_progression: List[str] = Field(..., description="Difficulty progression")
    topics: List[str] = Field(..., description="Topics to cover")
    prerequisites: List[str] = Field(default_factory=list, description="Required prerequisites")
    personalization_factors: List[str] = Field(default_factory=list, description="Factors used for personalization")
    
    class Config:
        json_schema_extra = {
            "example": {
                "path_id": "adaptive_algorithms_path",
                "title": "Personalized Algorithms Journey",
                "description": "Tailored algorithm learning path based on your strengths and interests",
                "estimated_duration": 40,
                "difficulty_progression": ["beginner", "intermediate", "advanced"],
                "topics": ["sorting", "searching", "dynamic_programming", "graph_algorithms"],
                "prerequisites": ["basic_programming", "data_structures"],
                "personalization_factors": ["visual_learner", "prefers_examples", "strong_in_logic"]
            }
        }


class InterventionSuggestion(BaseModel):
    """Suggestion for learning intervention"""
    intervention_type: str = Field(..., description="Type of intervention")
    trigger: str = Field(..., description="What triggered this suggestion")
    urgency: str = Field(..., description="Urgency level (low, medium, high, critical)")
    suggested_actions: List[str] = Field(..., description="Recommended actions")
    expected_outcome: str = Field(..., description="Expected result of intervention")
    monitoring_metrics: List[str] = Field(default_factory=list, description="Metrics to monitor post-intervention")
    
    class Config:
        json_schema_extra = {
            "example": {
                "intervention_type": "difficulty_adjustment",
                "trigger": "Three consecutive sessions with <40% success rate",
                "urgency": "high",
                "suggested_actions": [
                    "Reduce problem difficulty",
                    "Provide additional scaffolding",
                    "Review prerequisite concepts"
                ],
                "expected_outcome": "Improved confidence and success rate",
                "monitoring_metrics": ["success_rate", "engagement_score", "hint_usage"]
            }
        }


class CompetencyMap(BaseModel):
    """Map of student competencies across domains"""
    student_id: int = Field(..., description="Student identifier")
    competency_scores: Dict[str, float] = Field(..., description="Scores by competency area")
    skill_relationships: Dict[str, List[str]] = Field(default_factory=dict, description="Relationships between skills")
    growth_areas: List[str] = Field(default_factory=list, description="Areas with highest growth potential")
    strength_areas: List[str] = Field(default_factory=list, description="Current strength areas")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "student_id": 123,
                "competency_scores": {
                    "problem_decomposition": 0.78,
                    "algorithm_design": 0.65,
                    "code_implementation": 0.82,
                    "debugging": 0.71,
                    "optimization": 0.58
                },
                "skill_relationships": {
                    "algorithm_design": ["problem_decomposition", "optimization"],
                    "debugging": ["code_implementation", "problem_decomposition"]
                },
                "growth_areas": ["optimization", "algorithm_design"],
                "strength_areas": ["code_implementation", "problem_decomposition"]
            }
        }


class PredictiveModel(BaseModel):
    """Predictive model results for learning outcomes"""
    model_type: str = Field(..., description="Type of predictive model")
    predictions: Dict[str, Any] = Field(..., description="Model predictions")
    confidence_intervals: Dict[str, List[float]] = Field(default_factory=dict, description="Confidence intervals")
    feature_importance: Dict[str, float] = Field(default_factory=dict, description="Feature importance scores")
    model_accuracy: float = Field(..., ge=0.0, le=1.0, description="Model accuracy")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_type": "performance_prediction",
                "predictions": {
                    "next_week_score": 0.78,
                    "time_to_mastery": 45,
                    "optimal_difficulty": "intermediate"
                },
                "confidence_intervals": {
                    "next_week_score": [0.73, 0.83]
                },
                "feature_importance": {
                    "recent_performance": 0.35,
                    "consistency": 0.28,
                    "engagement": 0.25,
                    "learning_style": 0.12
                },
                "model_accuracy": 0.85
            }
        } 