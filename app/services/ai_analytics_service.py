"""
AI-Powered Analytics Service - Advanced learning analytics with AI insights
Processes comprehensive tracking data to generate intelligent insights and predictions
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from sqlmodel import Session, select, and_, or_, func
from sqlalchemy import desc
import numpy as np
from dataclasses import dataclass

from app.models.analytics import (
    StudentSessionTracking, ChatInteraction, CodeInteraction, CodeSubmission,
    StruggleAnalysis, StudentLearningProfile, EventLog, EventType,
    MessageType, StruggleSeverity
)
from app.models.user import User
from app.models.session import Session as SessionModel

logger = logging.getLogger(__name__)


@dataclass
class LearningInsight:
    """Structured learning insight"""
    insight_type: str  # "performance", "behavior", "prediction", "recommendation"
    title: str
    description: str
    confidence: float  # 0-1 confidence score
    priority: str  # "low", "medium", "high", "critical"
    action_items: List[str]
    supporting_data: Dict[str, Any]


@dataclass
class StudentRiskAssessment:
    """Student risk assessment for early intervention"""
    student_id: int
    risk_level: str  # "low", "medium", "high", "critical"
    risk_factors: List[str]
    predicted_outcome: str
    intervention_suggestions: List[str]
    confidence: float


@dataclass
class LearningPathRecommendation:
    """Personalized learning path recommendation"""
    student_id: int
    current_level: str
    recommended_next_steps: List[str]
    estimated_completion_time: int  # minutes
    difficulty_adjustment: str  # "easier", "maintain", "harder"
    rationale: str


class AIAnalyticsService:
    """AI-powered analytics service for intelligent insights"""
    
    def __init__(self):
        """Initialize AI analytics service"""
        self.insight_types = [
            "performance_analysis", "learning_style_detection", "struggle_prediction",
            "engagement_optimization", "skill_gap_identification", "progress_forecasting"
        ]
        self.confidence_threshold = 0.7  # Minimum confidence for actionable insights
        logger.info("AI Analytics Service initialized")
    
    async def generate_comprehensive_insights(
        self,
        student_id: int,
        time_period: timedelta = timedelta(days=30),
        db: Session = None
    ) -> List[LearningInsight]:
        """Generate comprehensive AI insights for a student"""
        
        # Gather comprehensive data
        tracking_data = await self._gather_student_tracking_data(student_id, time_period, db)
        
        insights = []
        
        # Performance analysis insights
        performance_insights = await self._analyze_performance_patterns(tracking_data)
        insights.extend(performance_insights)
        
        # Learning behavior insights
        behavior_insights = await self._analyze_learning_behaviors(tracking_data)
        insights.extend(behavior_insights)
        
        # Struggle prediction insights
        struggle_insights = await self._predict_struggle_areas(tracking_data)
        insights.extend(struggle_insights)
        
        # Filter and prioritize insights
        insights = self._prioritize_insights(insights)
        
        return insights
    
    async def assess_student_risk(
        self,
        student_id: int,
        session_id: Optional[int] = None,
        db: Session = None
    ) -> StudentRiskAssessment:
        """Assess student risk for early intervention"""
        
        # Gather recent data for risk assessment
        tracking_data = await self._gather_student_tracking_data(
            student_id, timedelta(days=14), db
        )
        
        risk_factors = []
        risk_score = 0.0
        
        # Analyze struggle patterns
        if tracking_data.get("recent_struggles", []):
            struggle_count = len(tracking_data["recent_struggles"])
            if struggle_count > 5:
                risk_factors.append(f"High struggle frequency ({struggle_count} incidents)")
                risk_score += 0.3
        
        # Analyze engagement patterns
        engagement_score = tracking_data.get("engagement_score", 1.0)
        if engagement_score < 0.3:
            risk_factors.append("Low engagement levels")
            risk_score += 0.25
        
        # Analyze performance trends
        performance_trend = tracking_data.get("performance_trend", "stable")
        if performance_trend == "declining":
            risk_factors.append("Declining performance trend")
            risk_score += 0.2
        
        # Analyze session consistency
        session_consistency = tracking_data.get("session_consistency", 1.0)
        if session_consistency < 0.5:
            risk_factors.append("Inconsistent learning sessions")
            risk_score += 0.15
        
        # Analyze help-seeking behavior
        help_ratio = tracking_data.get("help_request_ratio", 0.0)
        if help_ratio < 0.1:
            risk_factors.append("Reluctant to seek help")
            risk_score += 0.1
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "critical"
        elif risk_score >= 0.5:
            risk_level = "high"
        elif risk_score >= 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Generate intervention suggestions
        intervention_suggestions = self._generate_intervention_suggestions(
            risk_level, risk_factors, tracking_data
        )
        
        # Predict likely outcome
        predicted_outcome = self._predict_student_outcome(risk_score, tracking_data)
        
        return StudentRiskAssessment(
            student_id=student_id,
            risk_level=risk_level,
            risk_factors=risk_factors,
            predicted_outcome=predicted_outcome,
            intervention_suggestions=intervention_suggestions,
            confidence=min(0.95, max(0.6, 1.0 - abs(0.5 - risk_score)))
        )
    
    async def generate_learning_path_recommendation(
        self,
        student_id: int,
        current_session_id: Optional[int] = None,
        db: Session = None
    ) -> LearningPathRecommendation:
        """Generate personalized learning path recommendations"""
        
        # Gather student data
        tracking_data = await self._gather_student_tracking_data(
            student_id, timedelta(days=30), db
        )
        
        # Analyze current performance level
        current_level = self._assess_current_level(tracking_data)
        
        # Determine optimal difficulty adjustment
        difficulty_adjustment = self._recommend_difficulty_adjustment(tracking_data)
        
        # Generate next steps
        next_steps = self._generate_next_steps(tracking_data, current_level)
        
        # Estimate completion time
        estimated_time = self._estimate_completion_time(next_steps, tracking_data)
        
        # Generate rationale
        rationale = self._generate_path_rationale(
            current_level, difficulty_adjustment, tracking_data
        )
        
        return LearningPathRecommendation(
            student_id=student_id,
            current_level=current_level,
            recommended_next_steps=next_steps,
            estimated_completion_time=estimated_time,
            difficulty_adjustment=difficulty_adjustment,
            rationale=rationale
        )
    
    async def generate_cohort_insights(
        self,
        session_id: int,
        db: Session = None
    ) -> Dict[str, Any]:
        """Generate AI insights for entire cohort/session"""
        
        # Get all students in session
        statement = select(StudentSessionTracking).where(
            StudentSessionTracking.session_id == session_id
        )
        session_trackings = db.exec(statement).all()
        
        if not session_trackings:
            return {"error": "No tracking data found for session"}
        
        student_ids = [tracking.student_id for tracking in session_trackings]
        
        # Analyze cohort patterns
        cohort_analysis = {
            "session_id": session_id,
            "total_students": len(student_ids),
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }
        
        # Performance distribution analysis
        performance_distribution = await self._analyze_cohort_performance(session_trackings)
        cohort_analysis["performance_distribution"] = performance_distribution
        
        # Identify at-risk students
        at_risk_students = []
        for student_id in student_ids:
            risk_assessment = await self.assess_student_risk(student_id, session_id, db)
            if risk_assessment.risk_level in ["high", "critical"]:
                at_risk_students.append({
                    "student_id": student_id,
                    "risk_level": risk_assessment.risk_level,
                    "risk_factors": risk_assessment.risk_factors,
                    "intervention_suggestions": risk_assessment.intervention_suggestions
                })
        
        cohort_analysis["at_risk_students"] = at_risk_students
        
        # Common struggle areas
        common_struggles = await self._identify_common_struggle_areas(session_trackings, db)
        cohort_analysis["common_struggle_areas"] = common_struggles
        
        # Engagement patterns
        engagement_analysis = await self._analyze_cohort_engagement(session_trackings)
        cohort_analysis["engagement_patterns"] = engagement_analysis
        
        # Learning pace analysis
        pace_analysis = await self._analyze_learning_pace(session_trackings)
        cohort_analysis["learning_pace"] = pace_analysis
        
        # Collaborative learning opportunities
        collaboration_suggestions = await self._suggest_collaboration_opportunities(
            session_trackings, db
        )
        cohort_analysis["collaboration_suggestions"] = collaboration_suggestions
        
        # Instructor recommendations
        instructor_recommendations = self._generate_instructor_recommendations(
            cohort_analysis, at_risk_students
        )
        cohort_analysis["instructor_recommendations"] = instructor_recommendations
        
        return cohort_analysis
    
    async def predict_session_outcomes(
        self,
        session_id: int,
        prediction_horizon_days: int = 7,
        db: Session = None
    ) -> Dict[str, Any]:
        """Predict session outcomes and completion rates"""
        
        # Get current session data
        statement = select(StudentSessionTracking).where(
            StudentSessionTracking.session_id == session_id
        )
        session_trackings = db.exec(statement).all()
        
        predictions = {
            "session_id": session_id,
            "prediction_horizon_days": prediction_horizon_days,
            "prediction_timestamp": datetime.utcnow().isoformat(),
            "total_students": len(session_trackings)
        }
        
        if not session_trackings:
            return predictions
        
        # Predict completion rates
        completion_predictions = []
        struggle_predictions = []
        
        for tracking in session_trackings:
            # Predict individual completion probability
            completion_prob = self._predict_completion_probability(tracking)
            completion_predictions.append(completion_prob)
            
            # Predict struggle likelihood
            struggle_prob = self._predict_struggle_probability(tracking)
            struggle_predictions.append(struggle_prob)
        
        # Aggregate predictions
        predicted_completion_rate = np.mean(completion_predictions)
        predicted_struggle_rate = np.mean(struggle_predictions)
        
        predictions.update({
            "predicted_completion_rate": round(predicted_completion_rate, 2),
            "predicted_struggle_rate": round(predicted_struggle_rate, 2),
            "high_completion_probability_students": len([p for p in completion_predictions if p > 0.8]),
            "at_risk_completion_students": len([p for p in completion_predictions if p < 0.3]),
            "confidence": self._calculate_prediction_confidence(session_trackings)
        })
        
        return predictions
    
    # Private helper methods
    
    async def _gather_student_tracking_data(
        self,
        student_id: int,
        time_period: timedelta,
        db: Session
    ) -> Dict[str, Any]:
        """Gather comprehensive tracking data for a student"""
        
        cutoff_date = datetime.utcnow() - time_period
        
        # Get session trackings
        statement = select(StudentSessionTracking).where(
            and_(
                StudentSessionTracking.student_id == student_id,
                StudentSessionTracking.start_time >= cutoff_date
            )
        )
        session_trackings = db.exec(statement).all()
        
        # Get related data
        tracking_ids = [t.id for t in session_trackings] if session_trackings else []
        
        chat_interactions = []
        code_interactions = []
        code_submissions = []
        struggles = []
        
        if tracking_ids:
            # Get chat interactions
            chat_statement = select(ChatInteraction).where(
                ChatInteraction.session_tracking_id.in_(tracking_ids)
            )
            chat_interactions = db.exec(chat_statement).all()
            
            # Get code interactions
            code_statement = select(CodeInteraction).where(
                CodeInteraction.session_tracking_id.in_(tracking_ids)
            )
            code_interactions = db.exec(code_statement).all()
            
            # Get submissions
            submission_statement = select(CodeSubmission).where(
                CodeSubmission.session_tracking_id.in_(tracking_ids)
            )
            code_submissions = db.exec(submission_statement).all()
            
            # Get struggle analyses
            struggle_statement = select(StruggleAnalysis).where(
                StruggleAnalysis.session_tracking_id.in_(tracking_ids)
            )
            struggles = db.exec(struggle_statement).all()
        
        # Process and structure the data
        return {
            "student_id": student_id,
            "time_period_days": time_period.days,
            "session_trackings": session_trackings,
            "chat_interactions": chat_interactions,
            "code_interactions": code_interactions,
            "code_submissions": code_submissions,
            "recent_struggles": struggles,
            "engagement_score": self._calculate_engagement_score(session_trackings, chat_interactions, code_interactions),
            "performance_trend": self._calculate_performance_trend(code_submissions),
            "session_consistency": self._calculate_session_consistency(session_trackings),
            "help_request_ratio": self._calculate_help_request_ratio(chat_interactions)
        }
    
    async def _analyze_performance_patterns(self, tracking_data: Dict[str, Any]) -> List[LearningInsight]:
        """Analyze performance patterns and generate insights"""
        insights = []
        
        submissions = tracking_data.get("code_submissions", [])
        if not submissions:
            return insights
        
        # Success rate analysis
        success_rate = len([s for s in submissions if s.is_correct]) / len(submissions)
        
        if success_rate > 0.8:
            insights.append(LearningInsight(
                insight_type="performance",
                title="High Performance Achievement",
                description=f"Student demonstrates excellent performance with {success_rate:.1%} success rate",
                confidence=0.9,
                priority="medium",
                action_items=[
                    "Consider advancing to more challenging content",
                    "Explore advanced topics in areas of strength"
                ],
                supporting_data={"success_rate": success_rate, "total_submissions": len(submissions)}
            ))
        elif success_rate < 0.5:
            insights.append(LearningInsight(
                insight_type="performance",
                title="Performance Improvement Needed",
                description=f"Student showing challenges with {success_rate:.1%} success rate",
                confidence=0.85,
                priority="high",
                action_items=[
                    "Provide additional foundational support",
                    "Consider one-on-one tutoring sessions",
                    "Review prerequisite concepts"
                ],
                supporting_data={"success_rate": success_rate, "total_submissions": len(submissions)}
            ))
        
        return insights
    
    async def _analyze_learning_behaviors(self, tracking_data: Dict[str, Any]) -> List[LearningInsight]:
        """Analyze learning behaviors and patterns"""
        insights = []
        
        session_trackings = tracking_data.get("session_trackings", [])
        chat_interactions = tracking_data.get("chat_interactions", [])
        
        if session_trackings:
            # Session duration patterns
            avg_session_duration = np.mean([
                (t.end_time or datetime.utcnow() - t.start_time).total_seconds() / 60
                for t in session_trackings
            ])
            
            if avg_session_duration > 90:
                insights.append(LearningInsight(
                    insight_type="behavior",
                    title="Extended Learning Sessions",
                    description=f"Student engages in long learning sessions (avg {avg_session_duration:.0f} min)",
                    confidence=0.8,
                    priority="low",
                    action_items=[
                        "Consider breaking content into smaller chunks",
                        "Add regular break reminders"
                    ],
                    supporting_data={"avg_session_duration": avg_session_duration}
                ))
            elif avg_session_duration < 15:
                insights.append(LearningInsight(
                    insight_type="behavior",
                    title="Short Learning Sessions",
                    description=f"Student has brief learning sessions (avg {avg_session_duration:.0f} min)",
                    confidence=0.8,
                    priority="medium",
                    action_items=[
                        "Investigate engagement barriers",
                        "Provide incentives for longer engagement"
                    ],
                    supporting_data={"avg_session_duration": avg_session_duration}
                ))
        
        # Communication patterns
        if chat_interactions:
            question_ratio = len([c for c in chat_interactions 
                                if c.message_type == MessageType.STUDENT_QUESTION]) / len(chat_interactions)
            
            if question_ratio > 0.6:
                insights.append(LearningInsight(
                    insight_type="behavior",
                    title="High Question Frequency",
                    description="Student asks many questions, showing active engagement",
                    confidence=0.75,
                    priority="low",
                    action_items=[
                        "Encourage continued curiosity",
                        "Provide comprehensive resources"
                    ],
                    supporting_data={"question_ratio": question_ratio}
                ))
        
        return insights
    
    async def _predict_struggle_areas(self, tracking_data: Dict[str, Any]) -> List[LearningInsight]:
        """Predict potential struggle areas"""
        insights = []
        
        struggles = tracking_data.get("recent_struggles", [])
        code_interactions = tracking_data.get("code_interactions", [])
        
        # Analyze syntax error patterns
        if code_interactions:
            syntax_error_count = sum(len(c.syntax_errors) for c in code_interactions if c.syntax_errors)
            if syntax_error_count > 10:
                insights.append(LearningInsight(
                    insight_type="prediction",
                    title="Syntax Mastery Challenge Predicted",
                    description="High syntax error frequency suggests potential struggle with language fundamentals",
                    confidence=0.7,
                    priority="medium",
                    action_items=[
                        "Provide syntax reference materials",
                        "Include syntax-focused exercises",
                        "Consider IDE with better error highlighting"
                    ],
                    supporting_data={"syntax_error_count": syntax_error_count}
                ))
        
        return insights
    
    def _calculate_engagement_score(self, sessions, chats, codes) -> float:
        """Calculate overall engagement score"""
        if not sessions:
            return 0.0
        
        # Simple engagement calculation based on multiple factors
        total_interactions = sum(s.total_interactions for s in sessions)
        avg_active_time_ratio = np.mean([
            s.active_time_seconds / max(1, (s.end_time or datetime.utcnow() - s.start_time).total_seconds())
            for s in sessions
        ])
        
        # Normalize and combine metrics
        interaction_score = min(1.0, total_interactions / 100)  # Normalize to 100 interactions
        time_score = avg_active_time_ratio
        
        return (interaction_score + time_score) / 2
    
    def _calculate_performance_trend(self, submissions) -> str:
        """Calculate performance trend over time"""
        if len(submissions) < 3:
            return "insufficient_data"
        
        # Sort by timestamp and analyze success rate over time
        sorted_submissions = sorted(submissions, key=lambda x: x.timestamp)
        first_half = sorted_submissions[:len(sorted_submissions)//2]
        second_half = sorted_submissions[len(sorted_submissions)//2:]
        
        first_success_rate = len([s for s in first_half if s.is_correct]) / len(first_half)
        second_success_rate = len([s for s in second_half if s.is_correct]) / len(second_half)
        
        if second_success_rate > first_success_rate + 0.1:
            return "improving"
        elif second_success_rate < first_success_rate - 0.1:
            return "declining"
        else:
            return "stable"
    
    def _calculate_session_consistency(self, sessions) -> float:
        """Calculate consistency of learning sessions"""
        if len(sessions) < 2:
            return 1.0
        
        # Analyze time gaps between sessions
        sorted_sessions = sorted(sessions, key=lambda x: x.start_time)
        gaps = []
        for i in range(1, len(sorted_sessions)):
            gap = (sorted_sessions[i].start_time - sorted_sessions[i-1].start_time).days
            gaps.append(gap)
        
        if not gaps:
            return 1.0
        
        # Lower variance = higher consistency
        gap_variance = np.var(gaps)
        consistency = max(0.0, 1.0 - gap_variance / 100)  # Normalize variance
        
        return consistency
    
    def _calculate_help_request_ratio(self, chat_interactions) -> float:
        """Calculate ratio of help requests to total interactions"""
        if not chat_interactions:
            return 0.0
        
        help_requests = len([c for c in chat_interactions 
                           if c.message_type in [MessageType.HINT_REQUEST, MessageType.STUDENT_QUESTION]])
        
        return help_requests / len(chat_interactions)
    
    def _prioritize_insights(self, insights: List[LearningInsight]) -> List[LearningInsight]:
        """Prioritize insights by confidence and priority"""
        # Filter by confidence threshold
        filtered_insights = [i for i in insights if i.confidence >= self.confidence_threshold]
        
        # Sort by priority and confidence
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        
        filtered_insights.sort(
            key=lambda x: (priority_order.get(x.priority, 0), x.confidence),
            reverse=True
        )
        
        return filtered_insights[:10]  # Return top 10 insights
    
    def _generate_intervention_suggestions(
        self,
        risk_level: str,
        risk_factors: List[str],
        tracking_data: Dict[str, Any]
    ) -> List[str]:
        """Generate intervention suggestions based on risk assessment"""
        suggestions = []
        
        if risk_level == "critical":
            suggestions.extend([
                "Immediate instructor intervention recommended",
                "Schedule one-on-one support session",
                "Consider peer tutoring or study group"
            ])
        elif risk_level == "high":
            suggestions.extend([
                "Proactive instructor check-in within 48 hours",
                "Provide additional learning resources",
                "Monitor progress closely"
            ])
        
        # Specific suggestions based on risk factors
        for factor in risk_factors:
            if "engagement" in factor.lower():
                suggestions.append("Implement gamification or interactive elements")
            elif "performance" in factor.lower():
                suggestions.append("Review prerequisite knowledge and fill gaps")
            elif "help" in factor.lower():
                suggestions.append("Encourage help-seeking behavior and normalize asking questions")
        
        return list(set(suggestions))  # Remove duplicates
    
    def _predict_student_outcome(self, risk_score: float, tracking_data: Dict[str, Any]) -> str:
        """Predict likely student outcome"""
        if risk_score >= 0.7:
            return "At risk of not completing successfully without intervention"
        elif risk_score >= 0.5:
            return "May struggle but likely to complete with support"
        elif risk_score >= 0.3:
            return "On track with minor challenges expected"
        else:
            return "Highly likely to complete successfully"
    
    # Additional helper methods for cohort analysis, learning path generation, etc.
    # (Implementation details would continue with similar pattern)
    
    async def _analyze_cohort_performance(self, session_trackings) -> Dict[str, Any]:
        """Analyze performance distribution across cohort"""
        if not session_trackings:
            return {}
        
        progress_scores = [t.progress_percentage for t in session_trackings]
        struggle_scores = [t.current_struggle_score for t in session_trackings]
        
        return {
            "progress_distribution": {
                "mean": np.mean(progress_scores),
                "median": np.median(progress_scores),
                "std_dev": np.std(progress_scores),
                "quartiles": np.percentile(progress_scores, [25, 50, 75]).tolist()
            },
            "struggle_distribution": {
                "mean": np.mean(struggle_scores),
                "students_struggling": len([s for s in struggle_scores if s > 70]),
                "high_performers": len([p for p in progress_scores if p > 80])
            }
        }
    
    def _predict_completion_probability(self, tracking: StudentSessionTracking) -> float:
        """Predict probability of successful completion for a student"""
        # Simple prediction based on current metrics
        factors = []
        
        # Progress factor
        progress_factor = tracking.progress_percentage / 100
        factors.append(progress_factor)
        
        # Engagement factor
        if tracking.total_interactions > 0:
            engagement_factor = min(1.0, tracking.total_interactions / 50)  # Normalize to 50 interactions
            factors.append(engagement_factor)
        
        # Struggle factor (inverted)
        struggle_factor = max(0.0, 1.0 - tracking.current_struggle_score / 100)
        factors.append(struggle_factor)
        
        # Success rate factor
        success_factor = tracking.success_rate
        factors.append(success_factor)
        
        return np.mean(factors) if factors else 0.5
    
    def _predict_struggle_probability(self, tracking: StudentSessionTracking) -> float:
        """Predict probability of future struggle"""
        return tracking.current_struggle_score / 100
    
    def _calculate_prediction_confidence(self, session_trackings) -> float:
        """Calculate confidence in predictions based on data quality"""
        if not session_trackings:
            return 0.0
        
        # Confidence based on data volume and recency
        total_interactions = sum(t.total_interactions for t in session_trackings)
        confidence = min(1.0, total_interactions / 100)  # More interactions = higher confidence
        
        return confidence
    
    def _generate_instructor_recommendations(self, cohort_analysis, at_risk_students) -> List[str]:
        """Generate recommendations for instructors"""
        recommendations = []
        
        if at_risk_students:
            recommendations.append(f"Focus on {len(at_risk_students)} at-risk students")
        
        performance_dist = cohort_analysis.get("performance_distribution", {})
        if performance_dist.get("mean", 0) < 50:
            recommendations.append("Consider reviewing foundational concepts with entire class")
        
        return recommendations 