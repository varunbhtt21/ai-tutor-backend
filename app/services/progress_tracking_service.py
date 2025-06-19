"""
Progress Tracking Service - Advanced learning analytics and student progress monitoring
Provides detailed insights into learning patterns, skill development, and personalized recommendations
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from sqlmodel import Session, select, func
import numpy as np
from dataclasses import dataclass

from app.models.user import User
from app.models.session import Session, BubbleNode, StudentState
from app.models.analytics import EventLog, EventType, CoinTransaction
from app.schemas.progress_tracking import (
    ProgressAnalysis, SkillAssessment, LearningPattern, DifficultyRecommendation,
    PerformanceMetrics, LearningStyleProfile, MasteryLevel, StudySession,
    ProgressTrend, LearningGoal, AchievementBadge, LearningStyle, MasteryStatus,
    TrendDirection
)

logger = logging.getLogger(__name__)


@dataclass
class LearningMetrics:
    """Core learning metrics for analysis"""
    accuracy: float
    speed: float
    consistency: float
    improvement_rate: float
    engagement_score: float


class ProgressTrackingService:
    """Advanced progress tracking and analytics service"""
    
    def __init__(self):
        """Initialize progress tracking service"""
        self.learning_styles = ["visual", "auditory", "kinesthetic", "reading_writing"]
        self.skill_domains = ["problem_solving", "conceptual_understanding", "implementation", "debugging", "optimization"]
        logger.info("Progress Tracking Service initialized")
    
    async def analyze_student_progress(
        self,
        student_id: int,
        time_period: Optional[timedelta] = None,
        db: Session = None
    ) -> ProgressAnalysis:
        """Comprehensive analysis of student progress"""
        
        if time_period is None:
            time_period = timedelta(days=30)  # Default to last 30 days
        
        # Gather comprehensive data
        sessions = self._get_student_sessions(student_id, time_period, db)
        events = self._get_student_events(student_id, time_period, db)
        transactions = self._get_coin_transactions(student_id, time_period, db)
        
        # Analyze different aspects
        performance_metrics = self._calculate_performance_metrics(events, sessions)
        learning_patterns = self._identify_learning_patterns(events, sessions)
        skill_assessments = self._assess_skills(events, sessions)
        learning_style = self._analyze_learning_style(events)
        mastery_levels = self._calculate_mastery_levels(events, sessions)
        trends = self._calculate_progress_trends(events, sessions)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            performance_metrics, learning_patterns, skill_assessments
        )
        
        return ProgressAnalysis(
            student_id=student_id,
            analysis_period=time_period,
            performance_metrics=performance_metrics,
            learning_patterns=learning_patterns,
            skill_assessments=skill_assessments,
            learning_style_profile=learning_style,
            mastery_levels=mastery_levels,
            progress_trends=trends,
            recommendations=recommendations,
            generated_at=datetime.utcnow()
        )
    
    async def track_skill_development(
        self,
        student_id: int,
        skill_domain: str,
        db: Session
    ) -> SkillAssessment:
        """Track development in specific skill domain"""
        
        # Get skill-specific events
        events = self._get_skill_specific_events(student_id, skill_domain, db)
        
        # Calculate skill metrics
        current_level = self._calculate_skill_level(events)
        progress_rate = self._calculate_skill_progress_rate(events)
        strengths = self._identify_skill_strengths(events)
        weaknesses = self._identify_skill_weaknesses(events)
        next_milestones = self._predict_next_milestones(current_level, progress_rate)
        
        return SkillAssessment(
            skill_domain=skill_domain,
            current_level=current_level,
            progress_rate=progress_rate,
            strengths=strengths,
            weaknesses=weaknesses,
            next_milestones=next_milestones,
            confidence_score=self._calculate_confidence_score(events),
            last_updated=datetime.utcnow()
        )
    
    async def detect_learning_difficulties(
        self,
        student_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Detect potential learning difficulties and intervention points"""
        
        events = self._get_student_events(student_id, timedelta(days=14), db)
        
        difficulties = []
        
        # Check for various difficulty patterns
        if self._detect_confusion_pattern(events):
            difficulties.append({
                "type": "confusion",
                "severity": "medium",
                "description": "Student showing signs of confusion in recent sessions",
                "recommendations": ["Review fundamentals", "Provide additional examples", "Consider one-on-one help"]
            })
        
        if self._detect_frustration_pattern(events):
            difficulties.append({
                "type": "frustration",
                "severity": "high",
                "description": "High frequency of failed attempts without progress",
                "recommendations": ["Break down complex problems", "Provide more hints", "Adjust difficulty level"]
            })
        
        if self._detect_disengagement_pattern(events):
            difficulties.append({
                "type": "disengagement",
                "severity": "high",
                "description": "Decreasing engagement and session frequency",
                "recommendations": ["Gamify learning", "Introduce new content", "Check learning preferences"]
            })
        
        if self._detect_plateau_pattern(events):
            difficulties.append({
                "type": "plateau",
                "severity": "medium",
                "description": "Learning progress has stagnated",
                "recommendations": ["Introduce advanced challenges", "Review learning style", "Set new goals"]
            })
        
        return difficulties
    
    async def recommend_adaptive_difficulty(
        self,
        student_id: int,
        topic: str,
        db: Session
    ) -> DifficultyRecommendation:
        """Recommend optimal difficulty level for student"""
        
        # Analyze recent performance in topic
        topic_events = self._get_topic_events(student_id, topic, db)
        
        # Calculate performance metrics
        success_rate = self._calculate_success_rate(topic_events)
        average_time = self._calculate_average_time(topic_events)
        hint_usage = self._calculate_hint_usage(topic_events)
        
        # Determine optimal difficulty
        if success_rate > 0.8 and hint_usage < 0.2:
            recommended_level = "increase"
            confidence = 0.9
        elif success_rate < 0.4 or hint_usage > 0.6:
            recommended_level = "decrease"
            confidence = 0.8
        else:
            recommended_level = "maintain"
            confidence = 0.7
        
        return DifficultyRecommendation(
            topic=topic,
            current_level=self._estimate_current_difficulty(topic_events),
            recommended_level=recommended_level,
            confidence=confidence,
            reasoning=self._generate_difficulty_reasoning(success_rate, hint_usage),
            expected_improvement=self._predict_improvement(recommended_level)
        )
    
    async def generate_learning_goals(
        self,
        student_id: int,
        db: Session
    ) -> List[LearningGoal]:
        """Generate personalized learning goals based on progress analysis"""
        
        progress = await self.analyze_student_progress(student_id, db=db)
        
        goals = []
        
        # Goal based on weakest skill
        if progress.skill_assessments:
            weakest_skill = min(progress.skill_assessments, key=lambda x: x.current_level)
            goals.append(LearningGoal(
                title=f"Improve {weakest_skill.skill_domain.replace('_', ' ').title()}",
                description=f"Focus on developing {weakest_skill.skill_domain} skills",
                target_metric="skill_level",
                current_value=weakest_skill.current_level,
                target_value=min(weakest_skill.current_level + 0.2, 1.0),
                deadline=datetime.utcnow() + timedelta(days=14),
                priority="high"
            ))
        
        # Goal based on overall performance
        if progress.performance_metrics.overall_score < 0.7:
            goals.append(LearningGoal(
                title="Improve Overall Performance",
                description="Focus on consistency and accuracy across all topics",
                target_metric="overall_score",
                current_value=progress.performance_metrics.overall_score,
                target_value=0.75,
                deadline=datetime.utcnow() + timedelta(days=21),
                priority="medium"
            ))
        
        # Engagement goal if needed
        if progress.performance_metrics.engagement_score < 0.6:
            goals.append(LearningGoal(
                title="Increase Learning Engagement",
                description="Participate more actively in learning sessions",
                target_metric="engagement_score",
                current_value=progress.performance_metrics.engagement_score,
                target_value=0.75,
                deadline=datetime.utcnow() + timedelta(days=10),
                priority="high"
            ))
        
        return goals
    
    async def calculate_achievement_badges(
        self,
        student_id: int,
        db: Session
    ) -> List[AchievementBadge]:
        """Calculate earned achievement badges"""
        
        events = self._get_student_events(student_id, timedelta(days=90), db)
        sessions = self._get_student_sessions(student_id, timedelta(days=90), db)
        
        badges = []
        
        # Streak badges
        current_streak = self._calculate_learning_streak(sessions)
        if current_streak >= 7:
            badges.append(AchievementBadge(
                name="Week Warrior",
                description="Completed learning sessions for 7 consecutive days",
                category="consistency",
                earned_date=datetime.utcnow(),
                points=100
            ))
        
        # Performance badges
        success_events = [e for e in events if e.event_type == EventType.BUBBLE_SUCCESS]
        if len(success_events) >= 100:
            badges.append(AchievementBadge(
                name="Century Champion",
                description="Successfully completed 100 learning activities",
                category="achievement",
                earned_date=datetime.utcnow(),
                points=200
            ))
        
        # Skill mastery badges
        for skill in self.skill_domains:
            skill_level = self._calculate_skill_level(
                self._get_skill_specific_events(student_id, skill, db)
            )
            if skill_level >= 0.8:
                badges.append(AchievementBadge(
                    name=f"{skill.replace('_', ' ').title()} Master",
                    description=f"Achieved mastery in {skill.replace('_', ' ')}",
                    category="mastery",
                    earned_date=datetime.utcnow(),
                    points=300
                ))
        
        return badges
    
    # Private helper methods
    
    def _get_student_sessions(self, student_id: int, time_period: timedelta, db: Session) -> List[StudentState]:
        """Get student sessions within time period"""
        try:
            cutoff_date = datetime.utcnow() - time_period
            stmt = (select(StudentState)
                   .where(StudentState.student_id == student_id)
                   .where(StudentState.started_at >= cutoff_date)
                   .order_by(StudentState.started_at.desc()))
            return db.exec(stmt).all()
        except Exception as e:
            logger.error(f"Error fetching student sessions: {e}")
            return []
    
    def _get_student_events(self, student_id: int, time_period: timedelta, db: Session) -> List[EventLog]:
        """Get student events within time period"""
        try:
            cutoff_date = datetime.utcnow() - time_period
            stmt = (select(EventLog)
                   .where(EventLog.student_id == student_id)
                   .where(EventLog.timestamp >= cutoff_date)
                   .order_by(EventLog.timestamp.desc()))
            return db.exec(stmt).all()
        except Exception as e:
            logger.error(f"Error fetching student events: {e}")
            return []
    
    def _get_coin_transactions(self, student_id: int, time_period: timedelta, db: Session) -> List[CoinTransaction]:
        """Get coin transactions within time period"""
        try:
            cutoff_date = datetime.utcnow() - time_period
            stmt = (select(CoinTransaction)
                   .where(CoinTransaction.student_id == student_id)
                   .where(CoinTransaction.timestamp >= cutoff_date)
                   .order_by(CoinTransaction.timestamp.desc()))
            return db.exec(stmt).all()
        except Exception as e:
            logger.error(f"Error fetching coin transactions: {e}")
            return []
    
    def _calculate_performance_metrics(self, events: List[EventLog], sessions: List[StudentState]) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        
        if not events:
            return PerformanceMetrics(
                overall_score=0.0,
                accuracy=0.0,
                speed_score=0.0,
                consistency=0.0,
                improvement_rate=0.0,
                engagement_score=0.0
            )
        
        # Calculate accuracy
        success_events = [e for e in events if e.event_type == EventType.BUBBLE_SUCCESS]
        total_attempts = [e for e in events if e.event_type in [EventType.BUBBLE_SUCCESS, EventType.BUBBLE_FAIL]]
        accuracy = len(success_events) / max(len(total_attempts), 1)
        
        # Calculate speed (tasks per hour)
        if sessions:
            total_time = sum(s.total_time_spent / 60 or 0 for s in sessions)  # convert seconds to minutes
            speed_score = len(success_events) / max(total_time / 60, 0.1)  # tasks per hour
            speed_score = min(speed_score / 10, 1.0)  # normalize to 0-1
        else:
            speed_score = 0.0
        
        # Calculate consistency (variance in daily performance)
        daily_scores = self._calculate_daily_scores(events)
        if daily_scores and len(daily_scores) > 1:
            consistency = 1.0 - np.std(daily_scores)
            consistency = max(0.0, min(consistency, 1.0))
        else:
            consistency = 0.0
        
        # Calculate improvement rate
        improvement_rate = self._calculate_improvement_rate(events)
        
        # Calculate engagement score
        engagement_score = self._calculate_engagement_score(events, sessions)
        
        # Overall score (weighted average)
        overall_score = (
            accuracy * 0.3 +
            speed_score * 0.2 +
            consistency * 0.2 +
            improvement_rate * 0.15 +
            engagement_score * 0.15
        )
        
        return PerformanceMetrics(
            overall_score=overall_score,
            accuracy=accuracy,
            speed_score=speed_score,
            consistency=consistency,
            improvement_rate=improvement_rate,
            engagement_score=engagement_score
        )
    
    def _identify_learning_patterns(self, events: List[EventLog], sessions: List[StudentState]) -> List[LearningPattern]:
        """Identify patterns in learning behavior"""
        
        patterns = []
        
        # Time-based patterns
        hour_distribution = defaultdict(int)
        for event in events:
            hour_distribution[event.timestamp.hour] += 1
        
        if hour_distribution:
            peak_hours = sorted(hour_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
            if peak_hours:
                patterns.append(LearningPattern(
                    pattern_type="temporal",
                    description=f"Most active during hours: {', '.join(str(h[0]) for h in peak_hours)}",
                    confidence=0.8,
                    frequency=sum(h[1] for h in peak_hours) / max(len(events), 1)
                ))
        
        # Session length patterns
        if sessions:
            avg_session_length = np.mean([s.total_time_spent / 60 or 0 for s in sessions])  # convert to minutes
            if avg_session_length < 15:
                patterns.append(LearningPattern(
                    pattern_type="session_length",
                    description="Prefers short, focused learning sessions",
                    confidence=0.7,
                    frequency=0.8
                ))
            elif avg_session_length > 45:
                patterns.append(LearningPattern(
                    pattern_type="session_length",
                    description="Engages in long, deep learning sessions",
                    confidence=0.7,
                    frequency=0.8
                ))
        
        # Difficulty preference patterns
        hint_events = [e for e in events if e.event_type == EventType.HINT_REQUESTED]
        total_attempts = len([e for e in events if e.event_type in [EventType.BUBBLE_SUCCESS, EventType.BUBBLE_FAIL]])
        
        if total_attempts > 0:
            hint_ratio = len(hint_events) / total_attempts
            if hint_ratio > 0.3:
                patterns.append(LearningPattern(
                    pattern_type="help_seeking",
                    description="Frequently seeks hints and guidance",
                    confidence=0.8,
                    frequency=hint_ratio
                ))
            elif hint_ratio < 0.1:
                patterns.append(LearningPattern(
                    pattern_type="independence",
                    description="Prefers to work independently without hints",
                    confidence=0.8,
                    frequency=1.0 - hint_ratio
                ))
        
        return patterns
    
    def _assess_skills(self, events: List[EventLog], sessions: List[StudentState]) -> List[SkillAssessment]:
        """Assess skill levels across different domains"""
        
        assessments = []
        
        for skill in self.skill_domains:
            skill_events = self._get_skill_specific_events_from_list(events, skill)
            
            if skill_events:
                current_level = self._calculate_skill_level(skill_events)
                progress_rate = self._calculate_skill_progress_rate(skill_events)
                
                assessments.append(SkillAssessment(
                    skill_domain=skill,
                    current_level=current_level,
                    progress_rate=progress_rate,
                    strengths=self._identify_skill_strengths(skill_events),
                    weaknesses=self._identify_skill_weaknesses(skill_events),
                    next_milestones=self._predict_next_milestones(current_level, progress_rate),
                    confidence_score=self._calculate_confidence_score(skill_events),
                    last_updated=datetime.utcnow()
                ))
            else:
                # Default assessment for skills with no data
                assessments.append(SkillAssessment(
                    skill_domain=skill,
                    current_level=0.0,
                    progress_rate=0.0,
                    strengths=[],
                    weaknesses=["Insufficient data"],
                    next_milestones=["Complete initial assessment"],
                    confidence_score=0.0,
                    last_updated=datetime.utcnow()
                ))
        
        return assessments
    
    def _analyze_learning_style(self, events: List[EventLog]) -> LearningStyleProfile:
        """Analyze student's learning style preferences"""
        
        # Analyze interaction patterns to infer learning style
        visual_score = 0.0
        auditory_score = 0.0
        kinesthetic_score = 0.0
        reading_writing_score = 0.0
        
        # Placeholder analysis - in real implementation, analyze actual behavior patterns
        hint_events = [e for e in events if e.event_type == EventType.HINT_REQUESTED]
        tutor_events = [e for e in events if e.event_type == EventType.TUTOR_INTERACTION]
        
        if len(hint_events) > len(tutor_events):
            reading_writing_score = 0.7
            visual_score = 0.6
        else:
            auditory_score = 0.7
            kinesthetic_score = 0.6
        
        # Determine dominant style
        style_scores = [
            ("visual", visual_score), 
            ("auditory", auditory_score), 
            ("kinesthetic", kinesthetic_score), 
            ("reading_writing", reading_writing_score)
        ]
        dominant_style_name = max(style_scores, key=lambda x: x[1])[0]
        
        # Map to enum
        style_mapping = {
            "visual": LearningStyle.VISUAL,
            "auditory": LearningStyle.AUDITORY,
            "kinesthetic": LearningStyle.KINESTHETIC,
            "reading_writing": LearningStyle.READING_WRITING
        }
        
        return LearningStyleProfile(
            visual=visual_score,
            auditory=auditory_score,
            kinesthetic=kinesthetic_score,
            reading_writing=reading_writing_score,
            dominant_style=style_mapping[dominant_style_name],
            confidence=0.6
        )
    
    def _calculate_mastery_levels(self, events: List[EventLog], sessions: List[StudentState]) -> List[MasteryLevel]:
        """Calculate mastery levels for different topics"""
        
        # Group events by topic/node
        topic_events = defaultdict(list)
        for event in events:
            if event.node_id:
                topic_events[event.node_id].append(event)
        
        mastery_levels = []
        for topic, topic_event_list in topic_events.items():
            success_rate = self._calculate_success_rate(topic_event_list)
            consistency = self._calculate_topic_consistency(topic_event_list)
            
            # Determine mastery level
            if success_rate >= 0.9 and consistency >= 0.8:
                level = MasteryStatus.MASTERED
            elif success_rate >= 0.7 and consistency >= 0.6:
                level = MasteryStatus.PROFICIENT
            elif success_rate >= 0.5:
                level = MasteryStatus.DEVELOPING
            else:
                level = MasteryStatus.BEGINNING
            
            mastery_levels.append(MasteryLevel(
                topic=topic,
                level=level,
                score=success_rate,
                consistency=consistency,
                last_practiced=max(e.timestamp for e in topic_event_list) if topic_event_list else datetime.utcnow()
            ))
        
        return mastery_levels
    
    def _calculate_progress_trends(self, events: List[EventLog], sessions: List[StudentState]) -> List[ProgressTrend]:
        """Calculate progress trends over time"""
        
        trends = []
        
        # Weekly performance trend
        weekly_scores = self._calculate_weekly_scores(events)
        if len(weekly_scores) >= 2:
            recent_trend = TrendDirection.INCREASING if weekly_scores[-1] > weekly_scores[-2] else TrendDirection.DECREASING
            trends.append(ProgressTrend(
                metric="weekly_performance",
                direction=recent_trend,
                magnitude=abs(weekly_scores[-1] - weekly_scores[-2]),
                period="week",
                confidence=0.7
            ))
        
        # Session frequency trend
        session_frequencies = self._calculate_session_frequencies(sessions)
        if len(session_frequencies) >= 2:
            freq_trend = TrendDirection.INCREASING if session_frequencies[-1] > session_frequencies[-2] else TrendDirection.DECREASING
            trends.append(ProgressTrend(
                metric="session_frequency",
                direction=freq_trend,
                magnitude=abs(session_frequencies[-1] - session_frequencies[-2]),
                period="week",
                confidence=0.8
            ))
        
        return trends
    
    def _generate_recommendations(
        self,
        performance: PerformanceMetrics,
        patterns: List[LearningPattern],
        skills: List[SkillAssessment]
    ) -> List[str]:
        """Generate personalized recommendations"""
        
        recommendations = []
        
        # Performance-based recommendations
        if performance.accuracy < 0.6:
            recommendations.append("Focus on understanding concepts before attempting problems")
        
        if performance.consistency < 0.5:
            recommendations.append("Try to maintain a regular study schedule")
        
        if performance.engagement_score < 0.6:
            recommendations.append("Explore different types of learning activities to increase engagement")
        
        # Pattern-based recommendations
        for pattern in patterns:
            if pattern.pattern_type == "help_seeking" and pattern.frequency > 0.4:
                recommendations.append("Try working through problems independently before seeking hints")
            elif pattern.pattern_type == "session_length" and "short" in pattern.description:
                recommendations.append("Consider gradually extending study sessions for deeper learning")
        
        # Skill-based recommendations
        weak_skills = [s for s in skills if s.current_level < 0.5]
        if weak_skills:
            skill_names = [s.skill_domain.replace('_', ' ') for s in weak_skills[:2]]
            recommendations.append(f"Focus additional practice on: {', '.join(skill_names)}")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    # Additional helper methods (simplified implementations)
    
    def _get_skill_specific_events(self, student_id: int, skill: str, db: Session) -> List[EventLog]:
        """Get events related to specific skill domain"""
        # In a real implementation, this would filter events by skill domain
        # For now, return a sample of events
        try:
            stmt = (select(EventLog)
                   .where(EventLog.student_id == student_id)
                   .limit(20))
            return db.exec(stmt).all()
        except Exception:
            return []
    
    def _get_skill_specific_events_from_list(self, events: List[EventLog], skill: str) -> List[EventLog]:
        """Filter events for specific skill from event list"""
        # Simplified - in real implementation, would use node metadata to determine skill
        return events[:max(1, len(events) // len(self.skill_domains))]
    
    def _calculate_skill_level(self, events: List[EventLog]) -> float:
        """Calculate skill level from events"""
        if not events:
            return 0.0
        success_rate = self._calculate_success_rate(events)
        return min(success_rate * 1.2, 1.0)  # Slight boost for skill calculation
    
    def _calculate_skill_progress_rate(self, events: List[EventLog]) -> float:
        """Calculate rate of skill improvement"""
        if len(events) < 4:
            return 0.0
        
        # Compare first half vs second half performance
        mid_point = len(events) // 2
        early_success = self._calculate_success_rate(events[:mid_point])
        recent_success = self._calculate_success_rate(events[mid_point:])
        
        return max(0.0, recent_success - early_success)
    
    def _calculate_success_rate(self, events: List[EventLog]) -> float:
        """Calculate success rate from events"""
        if not events:
            return 0.0
        
        success_events = [e for e in events if e.event_type == EventType.BUBBLE_SUCCESS]
        total_attempts = [e for e in events if e.event_type in [EventType.BUBBLE_SUCCESS, EventType.BUBBLE_FAIL]]
        
        return len(success_events) / max(len(total_attempts), 1)
    
    def _calculate_daily_scores(self, events: List[EventLog]) -> List[float]:
        """Calculate daily performance scores"""
        daily_events = defaultdict(list)
        for event in events:
            day = event.timestamp.date()
            daily_events[day].append(event)
        
        return [self._calculate_success_rate(day_events) for day_events in daily_events.values()]
    
    def _calculate_weekly_scores(self, events: List[EventLog]) -> List[float]:
        """Calculate weekly performance scores"""
        weekly_events = defaultdict(list)
        for event in events:
            week = event.timestamp.isocalendar()[1]  # ISO week number
            weekly_events[week].append(event)
        
        return [self._calculate_success_rate(week_events) for week_events in weekly_events.values()]
    
    def _calculate_improvement_rate(self, events: List[EventLog]) -> float:
        """Calculate overall improvement rate"""
        if len(events) < 10:
            return 0.0
        
        # Compare first 25% vs last 25%
        quarter = len(events) // 4
        early_performance = self._calculate_success_rate(events[:quarter])
        recent_performance = self._calculate_success_rate(events[-quarter:])
        
        return max(0.0, min(1.0, recent_performance - early_performance + 0.5))
    
    def _calculate_engagement_score(self, events: List[EventLog], sessions: List[StudentState]) -> float:
        """Calculate engagement score"""
        if not sessions:
            return 0.0
        
        # Factors: session frequency, duration, interaction variety
        avg_session_length = np.mean([s.total_time_spent / 60 or 0 for s in sessions])  # convert to minutes
        session_frequency = len(sessions) / 30  # sessions per day over 30 days
        
        # Normalize scores
        length_score = min(avg_session_length / 30, 1.0)  # 30 min = full score
        frequency_score = min(session_frequency * 7, 1.0)  # 1/week = full score
        
        return (length_score + frequency_score) / 2
    
    # Pattern detection methods
    
    def _detect_confusion_pattern(self, events: List[EventLog]) -> bool:
        """Detect if student shows confusion patterns"""
        hint_requests = [e for e in events if e.event_type == EventType.HINT_REQUESTED]
        tutor_interactions = [e for e in events if e.event_type == EventType.TUTOR_INTERACTION]
        
        total_activities = len([e for e in events if e.event_type in [EventType.BUBBLE_SUCCESS, EventType.BUBBLE_FAIL]])
        help_seeking_ratio = (len(hint_requests) + len(tutor_interactions)) / max(total_activities, 1)
        
        return help_seeking_ratio > 0.4
    
    def _detect_frustration_pattern(self, events: List[EventLog]) -> bool:
        """Detect frustration patterns"""
        failures = [e for e in events if e.event_type == EventType.BUBBLE_FAIL]
        total_attempts = [e for e in events if e.event_type in [EventType.BUBBLE_SUCCESS, EventType.BUBBLE_FAIL]]
        
        failure_rate = len(failures) / max(len(total_attempts), 1)
        return failure_rate > 0.7
    
    def _detect_disengagement_pattern(self, events: List[EventLog]) -> bool:
        """Detect disengagement patterns"""
        if len(events) < 10:
            return True  # Too few events suggest disengagement
        
        # Check if recent activity is decreasing
        recent_events = events[:len(events)//2]  # First half (more recent)
        older_events = events[len(events)//2:]   # Second half (older)
        
        return len(recent_events) < len(older_events) * 0.7
    
    def _detect_plateau_pattern(self, events: List[EventLog]) -> bool:
        """Detect learning plateau"""
        if len(events) < 20:
            return False
        
        # Check if performance hasn't improved in recent sessions
        quarter = len(events) // 4
        segments = [
            events[:quarter],           # Most recent
            events[quarter:quarter*2],  # Recent
            events[quarter*2:quarter*3], # Older
            events[quarter*3:quarter*4]  # Oldest
        ]
        
        success_rates = [self._calculate_success_rate(segment) for segment in segments]
        
        # Plateau if no improvement in last 3 segments
        return all(success_rates[i] <= success_rates[i+1] + 0.05 for i in range(2))
    
    # Additional helper methods with simplified implementations
    
    def _identify_skill_strengths(self, events: List[EventLog]) -> List[str]:
        """Identify strengths in skill domain"""
        success_rate = self._calculate_success_rate(events)
        if success_rate > 0.7:
            return ["Quick understanding", "Good problem solving"]
        elif success_rate > 0.5:
            return ["Steady progress"]
        else:
            return []
    
    def _identify_skill_weaknesses(self, events: List[EventLog]) -> List[str]:
        """Identify weaknesses in skill domain"""
        success_rate = self._calculate_success_rate(events)
        if success_rate < 0.4:
            return ["Needs more practice", "Fundamental concepts unclear"]
        elif success_rate < 0.6:
            return ["Inconsistent performance"]
        else:
            return []
    
    def _predict_next_milestones(self, current_level: float, progress_rate: float) -> List[str]:
        """Predict next learning milestones"""
        milestones = []
        if current_level < 0.3:
            milestones.append("Master basic concepts")
        elif current_level < 0.6:
            milestones.append("Apply concepts to new problems")
        elif current_level < 0.8:
            milestones.append("Achieve consistent performance")
        else:
            milestones.append("Tackle advanced challenges")
        
        return milestones
    
    def _calculate_confidence_score(self, events: List[EventLog]) -> float:
        """Calculate confidence in skill assessment"""
        return min(len(events) / 20, 1.0)  # More events = higher confidence
    
    def _calculate_average_time(self, events: List[EventLog]) -> float:
        """Calculate average time spent on activities"""
        # Simplified - would need timing data in events
        return 5.0  # minutes
    
    def _calculate_hint_usage(self, events: List[EventLog]) -> float:
        """Calculate hint usage ratio"""
        hints = [e for e in events if e.event_type == EventType.HINT_REQUESTED]
        total = [e for e in events if e.event_type in [EventType.BUBBLE_SUCCESS, EventType.BUBBLE_FAIL]]
        return len(hints) / max(len(total), 1)
    
    def _estimate_current_difficulty(self, events: List[EventLog]) -> str:
        """Estimate current difficulty level"""
        success_rate = self._calculate_success_rate(events)
        if success_rate > 0.8:
            return "easy"
        elif success_rate > 0.5:
            return "appropriate"
        else:
            return "challenging"
    
    def _generate_difficulty_reasoning(self, success_rate: float, hint_usage: float) -> str:
        """Generate reasoning for difficulty recommendation"""
        if success_rate > 0.8:
            return "High success rate indicates content may be too easy"
        elif success_rate < 0.4:
            return "Low success rate suggests content is too challenging"
        elif hint_usage > 0.6:
            return "High hint usage indicates need for easier content"
        else:
            return "Performance metrics suggest current difficulty is appropriate"
    
    def _predict_improvement(self, level_change: str) -> float:
        """Predict expected improvement from difficulty change"""
        if level_change == "increase":
            return 0.1  # Expect slight improvement from challenge
        elif level_change == "decrease":
            return 0.2  # Expect more improvement from easier content
        else:
            return 0.05  # Maintain current trajectory
    
    def _calculate_learning_streak(self, sessions: List[StudentState]) -> int:
        """Calculate current learning streak in days"""
        if not sessions:
            return 0
        
        # Sort by date and count consecutive days
        dates = sorted(set(s.started_at.date() for s in sessions), reverse=True)
        
        streak = 0
        expected_date = datetime.utcnow().date()
        
        for date in dates:
            if date == expected_date:
                streak += 1
                expected_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def _calculate_topic_consistency(self, events: List[EventLog]) -> float:
        """Calculate consistency for a specific topic"""
        if len(events) < 3:
            return 0.0
        
        # Calculate variance in performance
        daily_scores = []
        daily_events = defaultdict(list)
        
        for event in events:
            daily_events[event.timestamp.date()].append(event)
        
        for day_events in daily_events.values():
            daily_scores.append(self._calculate_success_rate(day_events))
        
        if len(daily_scores) < 2:
            return 1.0
        
        return max(0.0, 1.0 - np.std(daily_scores))
    
    def _calculate_session_frequencies(self, sessions: List[StudentState]) -> List[float]:
        """Calculate weekly session frequencies"""
        weekly_counts = defaultdict(int)
        for session in sessions:
            week = session.started_at.isocalendar()[1]
            weekly_counts[week] += 1
        
        return list(weekly_counts.values())
    
    def _get_topic_events(self, student_id: int, topic: str, db: Session) -> List[EventLog]:
        """Get events for specific topic"""
        try:
            stmt = (select(EventLog)
                   .where(EventLog.student_id == student_id)
                   .where(EventLog.node_id.like(f"%{topic}%"))
                   .limit(50))
            return db.exec(stmt).all()
        except Exception:
            return [] 