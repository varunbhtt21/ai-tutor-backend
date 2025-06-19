"""
Progress Tracking API - Advanced analytics and student progress monitoring endpoints
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.models.user import User
from app.services.progress_tracking_service import ProgressTrackingService
from app.schemas.progress_tracking import (
    ProgressAnalysis, SkillAssessment, LearningGoal, AchievementBadge,
    DifficultyRecommendation, CompetencyMap, LearningInsight,
    InterventionSuggestion, AdaptivePath
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/progress", tags=["progress-tracking"])

# Initialize service
progress_service = ProgressTrackingService()


@router.get("/health", summary="Check progress tracking service health")
async def health_check():
    """Check if progress tracking service is operational"""
    return {
        "status": "healthy",
        "service": "progress_tracking",
        "features": {
            "progress_analysis": True,
            "skill_assessment": True,
            "learning_patterns": True,
            "adaptive_difficulty": True,
            "achievement_badges": True,
            "learning_goals": True,
            "predictive_analytics": True
        },
        "timestamp": datetime.utcnow()
    }


@router.get("/analysis/{student_id}", response_model=ProgressAnalysis, summary="Get comprehensive progress analysis")
async def get_progress_analysis(
    student_id: int,
    days: Optional[int] = Query(30, description="Analysis period in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive progress analysis for a student
    
    - **student_id**: Student to analyze
    - **days**: Number of days to analyze (default: 30)
    
    Returns detailed analysis including:
    - Performance metrics and trends
    - Learning patterns and behavior
    - Skill assessments across domains
    - Learning style profile
    - Mastery levels per topic
    - Personalized recommendations
    """
    try:
        # Verify access (students can only view their own progress)
        if current_user.role != "admin" and current_user.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        time_period = timedelta(days=days)
        analysis = await progress_service.analyze_student_progress(
            student_id=student_id,
            time_period=time_period,
            db=db
        )
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing student progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze progress")


@router.get("/skills/{student_id}", response_model=List[SkillAssessment], summary="Get skill assessments")
async def get_skill_assessments(
    student_id: int,
    skill_domain: Optional[str] = Query(None, description="Specific skill domain to assess"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed skill assessments for student
    
    - **student_id**: Student to assess
    - **skill_domain**: Optional specific skill to focus on
    
    Returns skill assessments including:
    - Current skill levels
    - Progress rates
    - Strengths and weaknesses
    - Next milestones
    """
    try:
        # Verify access
        if current_user.role != "admin" and current_user.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if skill_domain:
            # Get specific skill assessment
            assessment = await progress_service.track_skill_development(
                student_id=student_id,
                skill_domain=skill_domain,
                db=db
            )
            return [assessment]
        else:
            # Get all skill assessments through progress analysis
            analysis = await progress_service.analyze_student_progress(
                student_id=student_id,
                db=db
            )
            return analysis.skill_assessments
            
    except Exception as e:
        logger.error(f"Error getting skill assessments: {e}")
        raise HTTPException(status_code=500, detail="Failed to get skill assessments")


@router.get("/difficulties/{student_id}", summary="Detect learning difficulties")
async def detect_learning_difficulties(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Detect potential learning difficulties and intervention points
    
    - **student_id**: Student to analyze
    
    Returns list of detected difficulties with:
    - Difficulty type and severity
    - Description of the issue
    - Recommended interventions
    """
    try:
        # Verify access
        if current_user.role != "admin" and current_user.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        difficulties = await progress_service.detect_learning_difficulties(
            student_id=student_id,
            db=db
        )
        
        return {
            "student_id": student_id,
            "difficulties_detected": len(difficulties),
            "difficulties": difficulties,
            "analysis_date": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error detecting learning difficulties: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect difficulties")


@router.get("/difficulty-recommendation/{student_id}", response_model=DifficultyRecommendation, summary="Get adaptive difficulty recommendation")
async def get_difficulty_recommendation(
    student_id: int,
    topic: str = Query(..., description="Topic to get difficulty recommendation for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get adaptive difficulty recommendation for specific topic
    
    - **student_id**: Student to analyze
    - **topic**: Topic to get recommendation for
    
    Returns recommendation including:
    - Current and recommended difficulty levels
    - Confidence in recommendation
    - Reasoning and expected improvement
    """
    try:
        # Verify access
        if current_user.role != "admin" and current_user.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        recommendation = await progress_service.recommend_adaptive_difficulty(
            student_id=student_id,
            topic=topic,
            db=db
        )
        
        return recommendation
        
    except Exception as e:
        logger.error(f"Error getting difficulty recommendation: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendation")


@router.get("/goals/{student_id}", response_model=List[LearningGoal], summary="Get personalized learning goals")
async def get_learning_goals(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate personalized learning goals based on progress analysis
    
    - **student_id**: Student to generate goals for
    
    Returns list of learning goals including:
    - Goal titles and descriptions
    - Target metrics and values
    - Deadlines and priorities
    - Current progress
    """
    try:
        # Verify access
        if current_user.role != "admin" and current_user.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        goals = await progress_service.generate_learning_goals(
            student_id=student_id,
            db=db
        )
        
        return goals
        
    except Exception as e:
        logger.error(f"Error generating learning goals: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate goals")


@router.get("/badges/{student_id}", response_model=List[AchievementBadge], summary="Get achievement badges")
async def get_achievement_badges(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculate and return earned achievement badges
    
    - **student_id**: Student to get badges for
    
    Returns list of earned badges including:
    - Badge names and descriptions
    - Categories and points
    - Earned dates
    """
    try:
        # Verify access
        if current_user.role != "admin" and current_user.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        badges = await progress_service.calculate_achievement_badges(
            student_id=student_id,
            db=db
        )
        
        return badges
        
    except Exception as e:
        logger.error(f"Error getting achievement badges: {e}")
        raise HTTPException(status_code=500, detail="Failed to get badges")


@router.get("/insights/{student_id}", summary="Get learning insights")
async def get_learning_insights(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get actionable learning insights based on progress analysis
    
    - **student_id**: Student to analyze
    
    Returns insights including:
    - Key observations and patterns
    - Actionable recommendations
    - Areas of concern and opportunity
    """
    try:
        # Verify access
        if current_user.role != "admin" and current_user.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get comprehensive analysis
        analysis = await progress_service.analyze_student_progress(
            student_id=student_id,
            db=db
        )
        
        # Generate insights based on analysis
        insights = []
        
        # Performance insights
        if analysis.performance_metrics.overall_score < 0.5:
            insights.append({
                "type": "performance_concern",
                "title": "Performance Below Average",
                "description": f"Overall performance score is {analysis.performance_metrics.overall_score:.2f}, indicating need for additional support",
                "importance": "high",
                "actionable": True,
                "recommendations": ["Review learning approach", "Seek additional help", "Focus on fundamentals"]
            })
        
        # Consistency insights
        if analysis.performance_metrics.consistency < 0.4:
            insights.append({
                "type": "consistency_issue",
                "title": "Inconsistent Performance",
                "description": "Performance varies significantly between sessions",
                "importance": "medium",
                "actionable": True,
                "recommendations": ["Establish regular study routine", "Review difficult topics more frequently"]
            })
        
        # Engagement insights
        if analysis.performance_metrics.engagement_score < 0.6:
            insights.append({
                "type": "engagement_low",
                "title": "Low Engagement Detected",
                "description": "Student engagement levels are below optimal",
                "importance": "medium",
                "actionable": True,
                "recommendations": ["Try different learning activities", "Set short-term goals", "Gamify learning"]
            })
        
        # Learning pattern insights
        for pattern in analysis.learning_patterns:
            if pattern.pattern_type == "help_seeking" and pattern.frequency > 0.5:
                insights.append({
                    "type": "dependency_pattern",
                    "title": "High Dependency on Help",
                    "description": pattern.description,
                    "importance": "medium",
                    "actionable": True,
                    "recommendations": ["Encourage independent problem solving", "Provide scaffolded practice"]
                })
        
        return {
            "student_id": student_id,
            "total_insights": len(insights),
            "insights": insights,
            "analysis_date": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting learning insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get insights")


@router.get("/competency-map/{student_id}", summary="Get competency map")
async def get_competency_map(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive competency map showing skill relationships and growth areas
    
    - **student_id**: Student to map competencies for
    
    Returns competency map including:
    - Scores across all competency areas
    - Skill relationships and dependencies
    - Growth and strength areas
    """
    try:
        # Verify access
        if current_user.role != "admin" and current_user.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get skill assessments
        analysis = await progress_service.analyze_student_progress(
            student_id=student_id,
            db=db
        )
        
        # Build competency map
        competency_scores = {}
        for skill in analysis.skill_assessments:
            competency_scores[skill.skill_domain] = skill.current_level
        
        # Identify growth and strength areas
        sorted_skills = sorted(competency_scores.items(), key=lambda x: x[1])
        growth_areas = [skill[0] for skill in sorted_skills[:2]]  # Bottom 2
        strength_areas = [skill[0] for skill in sorted_skills[-2:]]  # Top 2
        
        # Define skill relationships (simplified)
        skill_relationships = {
            "problem_solving": ["conceptual_understanding", "debugging"],
            "implementation": ["problem_solving", "debugging"],
            "optimization": ["implementation", "conceptual_understanding"],
            "debugging": ["implementation", "problem_solving"],
            "conceptual_understanding": []
        }
        
        competency_map = {
            "student_id": student_id,
            "competency_scores": competency_scores,
            "skill_relationships": skill_relationships,
            "growth_areas": growth_areas,
            "strength_areas": strength_areas,
            "last_updated": datetime.utcnow()
        }
        
        return competency_map
        
    except Exception as e:
        logger.error(f"Error getting competency map: {e}")
        raise HTTPException(status_code=500, detail="Failed to get competency map")


@router.get("/adaptive-path/{student_id}", summary="Get adaptive learning path")
async def get_adaptive_learning_path(
    student_id: int,
    focus_area: Optional[str] = Query(None, description="Area to focus the learning path on"),
    duration_hours: Optional[int] = Query(40, description="Desired path duration in hours"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate adaptive learning path based on student's progress and preferences
    
    - **student_id**: Student to generate path for
    - **focus_area**: Optional area to focus on
    - **duration_hours**: Desired path duration
    
    Returns personalized learning path including:
    - Recommended topics and sequence
    - Difficulty progression
    - Estimated duration
    - Personalization factors
    """
    try:
        # Verify access
        if current_user.role != "admin" and current_user.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get student analysis for personalization
        analysis = await progress_service.analyze_student_progress(
            student_id=student_id,
            db=db
        )
        
        # Determine focus area if not specified
        if not focus_area and analysis.skill_assessments:
            # Focus on weakest skill
            weakest_skill = min(analysis.skill_assessments, key=lambda x: x.current_level)
            focus_area = weakest_skill.skill_domain
        
        # Generate adaptive path
        if focus_area == "problem_solving":
            topics = ["basic_algorithms", "sorting", "searching", "recursion", "dynamic_programming"]
            difficulty_progression = ["beginner", "beginner", "intermediate", "intermediate", "advanced"]
        elif focus_area == "implementation":
            topics = ["syntax_basics", "data_structures", "object_oriented", "design_patterns", "optimization"]
            difficulty_progression = ["beginner", "intermediate", "intermediate", "advanced", "advanced"]
        else:
            # General path
            topics = ["fundamentals", "problem_solving", "implementation", "debugging", "optimization"]
            difficulty_progression = ["beginner", "intermediate", "intermediate", "advanced", "expert"]
        
        # Personalization factors
        personalization_factors = []
        personalization_factors.append(f"dominant_learning_style_{analysis.learning_style_profile.dominant_style.value}")
        
        if analysis.performance_metrics.accuracy < 0.6:
            personalization_factors.append("needs_practice")
        if analysis.performance_metrics.consistency < 0.5:
            personalization_factors.append("needs_structure")
        
        adaptive_path = {
            "path_id": f"adaptive_{focus_area}_{student_id}",
            "title": f"Personalized {focus_area.replace('_', ' ').title()} Journey",
            "description": f"Tailored learning path for {focus_area.replace('_', ' ')} based on your progress and learning style",
            "estimated_duration": duration_hours,
            "difficulty_progression": difficulty_progression,
            "topics": topics,
            "prerequisites": ["basic_programming"] if focus_area != "fundamentals" else [],
            "personalization_factors": personalization_factors
        }
        
        return adaptive_path
        
    except Exception as e:
        logger.error(f"Error generating adaptive learning path: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate learning path")


@router.get("/dashboard/{student_id}", summary="Get progress dashboard data")
async def get_progress_dashboard(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard data for progress tracking
    
    - **student_id**: Student to get dashboard for
    
    Returns dashboard data including:
    - Key performance metrics
    - Recent trends
    - Active goals
    - Recent achievements
    - Quick insights
    """
    try:
        # Verify access
        if current_user.role != "admin" and current_user.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get comprehensive data
        analysis = await progress_service.analyze_student_progress(
            student_id=student_id,
            time_period=timedelta(days=30),
            db=db
        )
        
        goals = await progress_service.generate_learning_goals(
            student_id=student_id,
            db=db
        )
        
        badges = await progress_service.calculate_achievement_badges(
            student_id=student_id,
            db=db
        )
        
        # Dashboard summary
        dashboard = {
            "student_id": student_id,
            "summary": {
                "overall_score": analysis.performance_metrics.overall_score,
                "accuracy": analysis.performance_metrics.accuracy,
                "consistency": analysis.performance_metrics.consistency,
                "engagement": analysis.performance_metrics.engagement_score,
                "improvement_rate": analysis.performance_metrics.improvement_rate
            },
            "trends": [
                {
                    "metric": trend.metric,
                    "direction": trend.direction.value,
                    "magnitude": trend.magnitude,
                    "period": trend.period
                } for trend in analysis.progress_trends
            ],
            "active_goals": [
                {
                    "title": goal.title,
                    "progress": goal.progress,
                    "deadline": goal.deadline,
                    "priority": goal.priority
                } for goal in goals
            ],
            "recent_badges": [
                {
                    "name": badge.name,
                    "category": badge.category,
                    "points": badge.points,
                    "earned_date": badge.earned_date
                } for badge in badges[-3:]  # Last 3 badges
            ],
            "skill_breakdown": [
                {
                    "skill": skill.skill_domain,
                    "level": skill.current_level,
                    "progress_rate": skill.progress_rate
                } for skill in analysis.skill_assessments
            ],
            "learning_style": {
                "dominant": analysis.learning_style_profile.dominant_style.value,
                "confidence": analysis.learning_style_profile.confidence
            },
            "recommendations": analysis.recommendations[:3],  # Top 3 recommendations
            "last_updated": datetime.utcnow()
        }
        
        return dashboard
        
    except Exception as e:
        logger.error(f"Error getting progress dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard")


@router.get("/predictions/{student_id}", summary="Get predictive analytics")
async def get_predictive_analytics(
    student_id: int,
    prediction_horizon: Optional[int] = Query(7, description="Prediction horizon in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get predictive analytics for student performance
    
    - **student_id**: Student to predict for
    - **prediction_horizon**: Days to predict ahead
    
    Returns predictions including:
    - Expected performance scores
    - Time to mastery estimates
    - Optimal difficulty recommendations
    - Risk factors
    """
    try:
        # Verify access
        if current_user.role != "admin" and current_user.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get current analysis
        analysis = await progress_service.analyze_student_progress(
            student_id=student_id,
            db=db
        )
        
        # Simple predictive model (in production, this would use ML models)
        current_score = analysis.performance_metrics.overall_score
        improvement_rate = analysis.performance_metrics.improvement_rate
        
        # Predict future score based on current trend
        predicted_score = min(1.0, current_score + (improvement_rate * prediction_horizon / 30))
        
        # Estimate time to mastery (0.8 threshold)
        if improvement_rate > 0:
            days_to_mastery = max(0, (0.8 - current_score) / improvement_rate * 30)
        else:
            days_to_mastery = float('inf')
        
        # Determine optimal difficulty
        if current_score > 0.7:
            optimal_difficulty = "advanced"
        elif current_score > 0.5:
            optimal_difficulty = "intermediate"
        else:
            optimal_difficulty = "beginner"
        
        # Identify risk factors
        risk_factors = []
        if analysis.performance_metrics.consistency < 0.4:
            risk_factors.append("inconsistent_performance")
        if analysis.performance_metrics.engagement_score < 0.5:
            risk_factors.append("low_engagement")
        if improvement_rate < 0:
            risk_factors.append("declining_performance")
        
        predictions = {
            "student_id": student_id,
            "prediction_horizon_days": prediction_horizon,
            "predictions": {
                "expected_score": predicted_score,
                "score_confidence": 0.75,
                "days_to_mastery": days_to_mastery if days_to_mastery != float('inf') else None,
                "optimal_difficulty": optimal_difficulty,
                "performance_trend": "improving" if improvement_rate > 0 else "stable" if improvement_rate == 0 else "declining"
            },
            "risk_factors": risk_factors,
            "recommendations": [
                "Maintain current learning pace" if improvement_rate > 0 else "Consider adjusting study approach",
                f"Focus on {optimal_difficulty} level content",
                "Monitor consistency and engagement" if risk_factors else "Continue current approach"
            ],
            "model_info": {
                "type": "linear_trend",
                "accuracy": 0.75,
                "last_updated": datetime.utcnow()
            }
        }
        
        return predictions
        
    except Exception as e:
        logger.error(f"Error getting predictive analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get predictions")


@router.get("/utils/skill-domains", summary="Get available skill domains")
async def get_skill_domains():
    """Get list of available skill domains for assessment"""
    return {
        "skill_domains": progress_service.skill_domains,
        "descriptions": {
            "problem_solving": "Ability to analyze and solve complex problems",
            "conceptual_understanding": "Grasp of underlying concepts and principles",
            "implementation": "Skill in translating ideas into working code",
            "debugging": "Ability to identify and fix errors",
            "optimization": "Skill in improving performance and efficiency"
        }
    }


@router.get("/utils/learning-styles", summary="Get available learning styles")
async def get_learning_styles():
    """Get list of available learning styles"""
    return {
        "learning_styles": progress_service.learning_styles,
        "descriptions": {
            "visual": "Learns best through visual aids and diagrams",
            "auditory": "Learns best through listening and discussion",
            "kinesthetic": "Learns best through hands-on practice",
            "reading_writing": "Learns best through reading and writing"
        }
    } 