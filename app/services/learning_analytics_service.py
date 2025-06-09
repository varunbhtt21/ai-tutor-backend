"""
Learning Analytics Service - Advanced analytics for personalized learning
Implements pattern recognition, engagement prediction, and learning optimization
"""
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
import json
import statistics
from dataclasses import dataclass
from enum import Enum

from app.database import SessionLocal
from app.models.learning_graph import (
    LearningConcept, ConceptPrerequisite, StudentProgress, 
    LearningPath, AssessmentResult, DifficultyLevel
)
from app.models.session import LearningSession, ConversationLog, LearningMetrics

class LearningPattern(Enum):
    """Identified learning patterns"""
    VISUAL_LEARNER = "visual_learner"
    HANDS_ON_LEARNER = "hands_on_learner"
    CONCEPTUAL_LEARNER = "conceptual_learner"
    EXAMPLE_DRIVEN = "example_driven"
    FAST_PROGRESSION = "fast_progression"
    NEEDS_REPETITION = "needs_repetition"
    STRUGGLES_WITH_ABSTRACTS = "struggles_with_abstracts"
    EXCELS_AT_PROBLEM_SOLVING = "excels_at_problem_solving"

class EngagementLevel(Enum):
    """Student engagement levels"""
    HIGHLY_ENGAGED = "highly_engaged"
    ENGAGED = "engaged"
    MODERATE = "moderate"
    DECLINING = "declining"
    DISENGAGED = "disengaged"

@dataclass
class LearningInsight:
    """Individual learning insight"""
    type: str
    message: str
    confidence: float
    actionable: bool
    priority: int  # 1-5, where 1 is highest priority
    supporting_data: Dict[str, Any]

@dataclass
class PerformancePrediction:
    """Prediction about student performance"""
    concept_id: int
    concept_name: str
    predicted_mastery_score: float
    predicted_time_to_mastery_hours: float
    confidence_interval: Tuple[float, float]
    factors: List[str]
    recommendations: List[str]

class LearningAnalyticsService:
    """Advanced analytics service for personalized learning insights"""
    
    def __init__(self):
        self.db_session = None
    
    def get_db(self) -> Session:
        """Get database session"""
        if not self.db_session:
            self.db_session = SessionLocal()
        return self.db_session
    
    async def analyze_student_profile(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive student learning profile"""
        db = self.get_db()
        
        # Gather all student data
        progress_data = await self._get_progress_data(session_id, user_id)
        conversation_data = await self._get_conversation_data(session_id, user_id)
        engagement_data = await self._analyze_engagement_patterns(session_id, user_id)
        learning_patterns = await self._identify_learning_patterns(session_id, user_id)
        performance_trends = await self._analyze_performance_trends(session_id, user_id)
        
        # Generate insights
        insights = await self._generate_learning_insights(
            progress_data, conversation_data, engagement_data, learning_patterns
        )
        
        # Performance predictions
        predictions = await self._predict_future_performance(session_id, user_id)
        
        # Personalization recommendations
        recommendations = await self._generate_personalization_recommendations(
            learning_patterns, performance_trends, insights
        )
        
        return {
            "student_id": user_id,
            "session_id": session_id,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "profile": {
                "learning_patterns": [p.value for p in learning_patterns],
                "current_engagement": engagement_data["current_level"].value,
                "average_mastery_rate": performance_trends.get("avg_mastery_rate", 0.0),
                "preferred_difficulty": performance_trends.get("preferred_difficulty", 2),
                "learning_velocity": performance_trends.get("learning_velocity", 1.0),
                "total_concepts_studied": len(progress_data),
                "concepts_mastered": len([p for p in progress_data if p.status == "mastered"]),
                "total_study_time_hours": sum(p.time_spent_minutes for p in progress_data) / 60
            },
            "insights": [
                {
                    "type": insight.type,
                    "message": insight.message,
                    "confidence": insight.confidence,
                    "actionable": insight.actionable,
                    "priority": insight.priority
                } for insight in insights
            ],
            "performance_predictions": [
                {
                    "concept_id": pred.concept_id,
                    "concept_name": pred.concept_name,
                    "predicted_mastery_score": pred.predicted_mastery_score,
                    "predicted_time_hours": pred.predicted_time_to_mastery_hours,
                    "confidence_range": pred.confidence_interval,
                    "key_factors": pred.factors,
                    "recommendations": pred.recommendations
                } for pred in predictions
            ],
            "personalization_recommendations": recommendations
        }
    
    async def _get_progress_data(self, session_id: str, user_id: str) -> List[StudentProgress]:
        """Get all student progress data"""
        db = self.get_db()
        return db.query(StudentProgress).filter(
            and_(
                StudentProgress.session_id == session_id,
                StudentProgress.user_id == user_id
            )
        ).all()
    
    async def _get_conversation_data(self, session_id: str, user_id: str) -> List[ConversationLog]:
        """Get conversation interaction data"""
        db = self.get_db()
        return db.query(ConversationLog).filter(
            ConversationLog.session_id == session_id
        ).order_by(ConversationLog.created_at).all()
    
    async def _analyze_engagement_patterns(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Analyze student engagement over time"""
        conversation_data = await self._get_conversation_data(session_id, user_id)
        
        if not conversation_data:
            return {
                "current_level": EngagementLevel.MODERATE,
                "trend": "stable",
                "indicators": []
            }
        
        # Analyze response times, message lengths, and interaction frequency
        response_times = []
        message_lengths = []
        interaction_gaps = []
        
        for i, log in enumerate(conversation_data):
            if log.ai_response:
                message_lengths.append(len(log.ai_response))
            
            if log.response_latency and log.response_latency > 0:
                response_times.append(log.response_latency)
            
            if i > 0:
                gap = (log.created_at - conversation_data[i-1].created_at).total_seconds()
                interaction_gaps.append(gap)
        
        # Calculate engagement indicators
        avg_response_time = statistics.mean(response_times) if response_times else 0
        avg_message_length = statistics.mean(message_lengths) if message_lengths else 0
        avg_interaction_gap = statistics.mean(interaction_gaps) if interaction_gaps else 0
        
        # Determine engagement level
        engagement_score = 0.5  # Start neutral
        
        # Quick responses indicate engagement
        if avg_response_time < 30:
            engagement_score += 0.2
        elif avg_response_time > 120:
            engagement_score -= 0.2
        
        # Longer messages indicate engagement
        if avg_message_length > 100:
            engagement_score += 0.15
        elif avg_message_length < 30:
            engagement_score -= 0.15
        
        # Short gaps between interactions indicate engagement
        if avg_interaction_gap < 300:  # 5 minutes
            engagement_score += 0.1
        elif avg_interaction_gap > 1800:  # 30 minutes
            engagement_score -= 0.2
        
        # Map score to engagement level
        if engagement_score >= 0.8:
            current_level = EngagementLevel.HIGHLY_ENGAGED
        elif engagement_score >= 0.6:
            current_level = EngagementLevel.ENGAGED
        elif engagement_score >= 0.4:
            current_level = EngagementLevel.MODERATE
        elif engagement_score >= 0.2:
            current_level = EngagementLevel.DECLINING
        else:
            current_level = EngagementLevel.DISENGAGED
        
        return {
            "current_level": current_level,
            "engagement_score": engagement_score,
            "avg_response_time": avg_response_time,
            "avg_message_length": avg_message_length,
            "avg_interaction_gap": avg_interaction_gap,
            "total_interactions": len(conversation_data),
            "indicators": []
        }
    
    async def _identify_learning_patterns(self, session_id: str, user_id: str) -> List[LearningPattern]:
        """Identify student's learning patterns"""
        progress_data = await self._get_progress_data(session_id, user_id)
        conversation_data = await self._get_conversation_data(session_id, user_id)
        
        patterns = []
        
        if not progress_data:
            return patterns
        
        # Analyze learning velocity
        mastery_times = [p.time_spent_minutes for p in progress_data if p.status == "mastered"]
        if mastery_times:
            avg_mastery_time = statistics.mean(mastery_times)
            if avg_mastery_time < 30:  # Quick learner
                patterns.append(LearningPattern.FAST_PROGRESSION)
            elif avg_mastery_time > 90:  # Needs more time
                patterns.append(LearningPattern.NEEDS_REPETITION)
        
        # Analyze struggle patterns
        struggle_count = len([p for p in progress_data if p.struggle_indicators])
        if struggle_count > len(progress_data) * 0.3:
            patterns.append(LearningPattern.STRUGGLES_WITH_ABSTRACTS)
        
        # Analyze confidence levels
        confidence_levels = [p.confidence_level for p in progress_data if p.confidence_level]
        if confidence_levels:
            avg_confidence = statistics.mean(confidence_levels)
            if avg_confidence > 0.8:
                patterns.append(LearningPattern.EXCELS_AT_PROBLEM_SOLVING)
        
        # Analyze preferred explanation types from conversation data
        visual_keywords = ["diagram", "chart", "visual", "show me", "picture"]
        example_keywords = ["example", "show", "demonstrate", "practice"]
        
        visual_requests = 0
        example_requests = 0
        
        for log in conversation_data:
            if log.user_input:
                user_text = log.user_input.lower()
                visual_requests += sum(1 for keyword in visual_keywords if keyword in user_text)
                example_requests += sum(1 for keyword in example_keywords if keyword in user_text)
        
        if visual_requests > example_requests:
            patterns.append(LearningPattern.VISUAL_LEARNER)
        elif example_requests > visual_requests:
            patterns.append(LearningPattern.EXAMPLE_DRIVEN)
        
        return patterns
    
    async def _analyze_performance_trends(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Analyze student performance trends over time"""
        progress_data = await self._get_progress_data(session_id, user_id)
        
        if not progress_data:
            return {}
        
        # Calculate mastery rate
        mastered_count = len([p for p in progress_data if p.status == "mastered"])
        mastery_rate = mastered_count / len(progress_data) if progress_data else 0
        
        # Calculate learning velocity (concepts mastered per hour)
        total_time_hours = sum(p.time_spent_minutes for p in progress_data) / 60
        learning_velocity = mastered_count / total_time_hours if total_time_hours > 0 else 0
        
        # Analyze difficulty preference
        difficulty_scores = [p.concept.difficulty_level for p in progress_data if p.concept]
        preferred_difficulty = statistics.mean(difficulty_scores) if difficulty_scores else 2
        
        return {
            "avg_mastery_rate": mastery_rate,
            "learning_velocity": learning_velocity,
            "preferred_difficulty": preferred_difficulty,
            "total_concepts": len(progress_data),
            "mastered_concepts": mastered_count
        }
    
    async def _generate_learning_insights(
        self, 
        progress_data: List[StudentProgress],
        conversation_data: List[ConversationLog],
        engagement_data: Dict[str, Any],
        learning_patterns: List[LearningPattern]
    ) -> List[LearningInsight]:
        """Generate actionable learning insights"""
        insights = []
        
        # Engagement insights
        if engagement_data["current_level"] == EngagementLevel.DECLINING:
            insights.append(LearningInsight(
                type="engagement_warning",
                message="Student engagement is declining. Consider introducing more interactive content or adjusting difficulty.",
                confidence=0.8,
                actionable=True,
                priority=1,
                supporting_data={"engagement_score": engagement_data["engagement_score"]}
            ))
        
        # Learning pattern insights
        if LearningPattern.FAST_PROGRESSION in learning_patterns:
            insights.append(LearningInsight(
                type="acceleration_opportunity",
                message="Student shows fast progression. Consider advancing to more challenging concepts.",
                confidence=0.9,
                actionable=True,
                priority=2,
                supporting_data={"pattern": "fast_progression"}
            ))
        
        if LearningPattern.VISUAL_LEARNER in learning_patterns:
            insights.append(LearningInsight(
                type="learning_style",
                message="Student prefers visual explanations. Prioritize diagrams and visual aids.",
                confidence=0.75,
                actionable=True,
                priority=2,
                supporting_data={"pattern": "visual_learner"}
            ))
        
        # Performance insights
        if progress_data:
            low_confidence_count = len([p for p in progress_data if p.confidence_level and p.confidence_level < 0.5])
            if low_confidence_count > len(progress_data) * 0.3:
                insights.append(LearningInsight(
                    type="confidence_building",
                    message="Student shows low confidence in multiple areas. Focus on confidence-building exercises.",
                    confidence=0.85,
                    actionable=True,
                    priority=1,
                    supporting_data={"low_confidence_ratio": low_confidence_count / len(progress_data)}
                ))
        
        return insights
    
    async def _predict_future_performance(self, session_id: str, user_id: str) -> List[PerformancePrediction]:
        """Predict student performance on upcoming concepts"""
        # This is a simplified prediction model - in a real system, you'd use ML models
        db = self.get_db()
        progress_data = await self._get_progress_data(session_id, user_id)
        
        if not progress_data:
            return []
        
        # Get concepts the student hasn't started yet
        mastered_concept_ids = [p.concept_id for p in progress_data]
        available_concepts = db.query(LearningConcept).filter(
            and_(
                LearningConcept.is_active == True,
                ~LearningConcept.id.in_(mastered_concept_ids)
            )
        ).limit(5).all()
        
        predictions = []
        
        # Calculate baseline performance metrics
        avg_mastery_score = statistics.mean([p.mastery_score for p in progress_data]) if progress_data else 0.7
        avg_time_per_concept = statistics.mean([p.time_spent_minutes for p in progress_data]) if progress_data else 45
        
        for concept in available_concepts:
            # Simple prediction based on difficulty and student's historical performance
            difficulty_factor = concept.difficulty_level / 5.0
            predicted_score = max(0.1, avg_mastery_score * (1.1 - difficulty_factor * 0.2))
            predicted_time = avg_time_per_concept * (0.8 + difficulty_factor * 0.4)
            
            predictions.append(PerformancePrediction(
                concept_id=concept.id,
                concept_name=concept.name,
                predicted_mastery_score=predicted_score,
                predicted_time_to_mastery_hours=predicted_time / 60,
                confidence_interval=(predicted_score * 0.8, min(1.0, predicted_score * 1.2)),
                factors=["historical_performance", "concept_difficulty"],
                recommendations=[
                    f"Estimated {predicted_time:.0f} minutes needed",
                    f"Expected mastery score: {predicted_score:.1%}"
                ]
            ))
        
        return predictions
    
    async def _generate_personalization_recommendations(
        self,
        learning_patterns: List[LearningPattern],
        performance_trends: Dict[str, Any],
        insights: List[LearningInsight]
    ) -> List[Dict[str, Any]]:
        """Generate personalized learning recommendations"""
        recommendations = []
        
        # Difficulty adjustment recommendations
        if performance_trends.get("avg_mastery_rate", 0) > 0.9:
            recommendations.append({
                "type": "difficulty_adjustment",
                "action": "increase_difficulty",
                "message": "Student is mastering concepts quickly. Consider increasing difficulty level.",
                "confidence": 0.8
            })
        elif performance_trends.get("avg_mastery_rate", 0) < 0.5:
            recommendations.append({
                "type": "difficulty_adjustment",
                "action": "decrease_difficulty",
                "message": "Student is struggling with current difficulty. Consider easier concepts or more support.",
                "confidence": 0.8
            })
        
        # Learning style recommendations
        if LearningPattern.VISUAL_LEARNER in learning_patterns:
            recommendations.append({
                "type": "content_format",
                "action": "prioritize_visuals",
                "message": "Provide more diagrams, charts, and visual explanations.",
                "confidence": 0.75
            })
        
        if LearningPattern.EXAMPLE_DRIVEN in learning_patterns:
            recommendations.append({
                "type": "content_format",
                "action": "provide_examples",
                "message": "Focus on practical examples and hands-on exercises.",
                "confidence": 0.75
            })
        
        # Pacing recommendations
        if LearningPattern.FAST_PROGRESSION in learning_patterns:
            recommendations.append({
                "type": "pacing",
                "action": "accelerate",
                "message": "Student can handle faster pacing. Introduce concepts more quickly.",
                "confidence": 0.8
            })
        elif LearningPattern.NEEDS_REPETITION in learning_patterns:
            recommendations.append({
                "type": "pacing",
                "action": "add_repetition",
                "message": "Add more practice exercises and review sessions.",
                "confidence": 0.8
            })
        
        return recommendations
    
    async def generate_real_time_insights(self, session_id: str, user_id: str, conversation_context: Dict) -> Dict[str, Any]:
        """Generate real-time insights during conversation"""
        # Quick analysis for immediate use during conversation
        progress_data = await self._get_progress_data(session_id, user_id)
        engagement_data = await self._analyze_engagement_patterns(session_id, user_id)
        
        current_concept = conversation_context.get("current_concept")
        user_response = conversation_context.get("user_response", "")
        
        insights = {
            "engagement_level": engagement_data["current_level"].value,
            "should_adjust_difficulty": False,
            "should_provide_encouragement": False,
            "recommended_next_action": "continue",
            "content_suggestions": []
        }
        
        # Check if student seems confused
        confusion_keywords = ["confused", "don't understand", "hard", "difficult", "help"]
        if any(keyword in user_response.lower() for keyword in confusion_keywords):
            insights["should_adjust_difficulty"] = True
            insights["recommended_next_action"] = "simplify_explanation"
            insights["content_suggestions"].append("Provide simpler explanation")
        
        # Check if student seems bored or finding it too easy
        boredom_keywords = ["easy", "simple", "boring", "already know"]
        if any(keyword in user_response.lower() for keyword in boredom_keywords):
            insights["recommended_next_action"] = "increase_challenge"
            insights["content_suggestions"].append("Introduce more challenging aspects")
        
        # Check if encouragement is needed
        if engagement_data["current_level"] in [EngagementLevel.DECLINING, EngagementLevel.DISENGAGED]:
            insights["should_provide_encouragement"] = True
            insights["content_suggestions"].append("Provide encouragement and motivation")
        
        return insights
    
    def close(self):
        """Close database connection"""
        if self.db_session:
            self.db_session.close()
            self.db_session = None 