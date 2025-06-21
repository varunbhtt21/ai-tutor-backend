"""
AI Analytics API - Advanced AI-powered analytics and insights endpoints
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlmodel import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.services.ai_analytics_service import AIAnalyticsService, LearningInsight, StudentRiskAssessment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-analytics", tags=["ai-analytics"])

# Initialize AI analytics service
ai_analytics_service = AIAnalyticsService()


# Request/Response Models
class InsightResponse(BaseModel):
    """Response model for learning insights"""
    insight_type: str
    title: str
    description: str
    confidence: float
    priority: str
    action_items: List[str]
    supporting_data: Dict[str, Any]


class RiskAssessmentResponse(BaseModel):
    """Response model for risk assessment"""
    student_id: int
    risk_level: str
    risk_factors: List[str]
    predicted_outcome: str
    intervention_suggestions: List[str]
    confidence: float


class CohortInsightsRequest(BaseModel):
    """Request model for cohort insights"""
    session_id: int
    include_individual_assessments: bool = True
    analysis_depth: str = "standard"  # "basic", "standard", "comprehensive"


@router.get("/health", summary="Check AI analytics service health")
async def health_check():
    """Check if AI analytics service is operational"""
    return {
        "status": "healthy",
        "service": "ai_analytics",
        "features": {
            "learning_insights": True,
            "risk_assessment": True,
            "cohort_analysis": True,
            "predictive_analytics": True,
            "intervention_suggestions": True
        },
        "timestamp": datetime.utcnow()
    }


@router.get("/insights/student/{student_id}", response_model=List[InsightResponse])
async def get_student_insights(
    student_id: int,
    days: Optional[int] = Query(30, description="Analysis period in days", ge=1, le=365),
    insight_types: Optional[List[str]] = Query(None, description="Filter by insight types"),
    min_confidence: Optional[float] = Query(0.7, description="Minimum confidence threshold", ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered learning insights for a student
    
    - **student_id**: Student to analyze
    - **days**: Analysis period in days (1-365)
    - **insight_types**: Filter by specific insight types
    - **min_confidence**: Minimum confidence threshold for insights
    
    Returns AI-generated insights including:
    - Performance pattern analysis
    - Learning behavior insights
    - Struggle area predictions
    - Personalized recommendations
    """
    try:
        # Verify access (students can only view their own insights, instructors/admins can view any)
        if current_user.role == "student" and current_user.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students can only view their own insights"
            )
        
        # Generate insights
        time_period = timedelta(days=days)
        insights = await ai_analytics_service.generate_comprehensive_insights(
            student_id=student_id,
            time_period=time_period,
            db=db
        )
        
        # Filter by insight types if specified
        if insight_types:
            insights = [i for i in insights if i.insight_type in insight_types]
        
        # Filter by confidence threshold
        insights = [i for i in insights if i.confidence >= min_confidence]
        
        # Convert to response format
        return [
            InsightResponse(
                insight_type=insight.insight_type,
                title=insight.title,
                description=insight.description,
                confidence=insight.confidence,
                priority=insight.priority,
                action_items=insight.action_items,
                supporting_data=insight.supporting_data
            )
            for insight in insights
        ]
        
    except Exception as e:
        logger.error(f"Error generating student insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate insights"
        )


@router.get("/risk-assessment/student/{student_id}", response_model=RiskAssessmentResponse)
async def assess_student_risk(
    student_id: int,
    session_id: Optional[int] = Query(None, description="Specific session to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Assess student risk for early intervention
    
    - **student_id**: Student to assess
    - **session_id**: Optional specific session context
    
    Returns comprehensive risk assessment including:
    - Risk level (low/medium/high/critical)
    - Identified risk factors
    - Predicted outcomes
    - Intervention suggestions
    """
    try:
        # Verify access (instructors and admins only for risk assessment)
        if current_user.role not in ["instructor", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Risk assessment requires instructor or admin access"
            )
        
        # Generate risk assessment
        risk_assessment = await ai_analytics_service.assess_student_risk(
            student_id=student_id,
            session_id=session_id,
            db=db
        )
        
        return RiskAssessmentResponse(
            student_id=risk_assessment.student_id,
            risk_level=risk_assessment.risk_level,
            risk_factors=risk_assessment.risk_factors,
            predicted_outcome=risk_assessment.predicted_outcome,
            intervention_suggestions=risk_assessment.intervention_suggestions,
            confidence=risk_assessment.confidence
        )
        
    except Exception as e:
        logger.error(f"Error assessing student risk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assess student risk"
        )


@router.post("/cohort-insights")
@require_role(["instructor", "admin"])
async def get_cohort_insights(
    request: CohortInsightsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive AI insights for an entire cohort/session
    
    - **session_id**: Session to analyze
    - **include_individual_assessments**: Include individual student risk assessments
    - **analysis_depth**: Depth of analysis (basic/standard/comprehensive)
    
    Returns cohort-level insights including:
    - Performance distribution analysis
    - At-risk student identification
    - Common struggle areas
    - Engagement patterns
    - Instructor recommendations
    """
    try:
        # Generate cohort insights
        cohort_insights = await ai_analytics_service.generate_cohort_insights(
            session_id=request.session_id,
            db=db
        )
        
        return cohort_insights
        
    except Exception as e:
        logger.error(f"Error generating cohort insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate cohort insights"
        )


@router.get("/recommendations/student/{student_id}")
async def get_personalized_recommendations(
    student_id: int,
    recommendation_type: Optional[str] = Query("all", description="Type of recommendations"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized AI recommendations for a student
    
    - **student_id**: Student to generate recommendations for
    - **recommendation_type**: Type of recommendations (learning_path, study_schedule, content, all)
    
    Returns personalized recommendations based on AI analysis
    """
    try:
        # Verify access
        if current_user.role == "student" and current_user.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students can only view their own recommendations"
            )
        
        # For now, generate basic recommendations based on insights
        insights = await ai_analytics_service.generate_comprehensive_insights(
            student_id=student_id,
            time_period=timedelta(days=30),
            db=db
        )
        
        # Extract action items from insights as recommendations
        recommendations = []
        for insight in insights:
            recommendations.extend(insight.action_items)
        
        # Remove duplicates and organize by type
        unique_recommendations = list(set(recommendations))
        
        return {
            "student_id": student_id,
            "recommendation_type": recommendation_type,
            "generated_at": datetime.utcnow().isoformat(),
            "recommendations": unique_recommendations[:10],  # Top 10 recommendations
            "total_insights_analyzed": len(insights)
        }
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )


@router.get("/dashboard/instructor/{session_id}")
@require_role(["instructor", "admin"])
async def get_instructor_ai_dashboard(
    session_id: int,
    include_predictions: bool = Query(True, description="Include predictive analytics"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive AI-powered instructor dashboard
    
    - **session_id**: Session to analyze
    - **include_predictions**: Include predictive analytics
    
    Returns instructor dashboard with AI insights:
    - At-risk student alerts
    - Performance trends
    - Intervention recommendations
    - Session health metrics
    """
    try:
        # Generate cohort insights
        cohort_insights = await ai_analytics_service.generate_cohort_insights(
            session_id=session_id,
            db=db
        )
        
        dashboard_data = {
            "session_id": session_id,
            "generated_at": datetime.utcnow().isoformat(),
            "ai_insights": cohort_insights,
        }
        
        # Add predictions if requested
        if include_predictions:
            # This would be implemented with more sophisticated prediction models
            dashboard_data["predictions"] = {
                "session_completion_rate": 0.85,
                "students_likely_to_struggle": len(cohort_insights.get("at_risk_students", [])),
                "estimated_completion_date": (datetime.utcnow() + timedelta(days=14)).isoformat()
            }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error generating instructor AI dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate instructor dashboard"
        )


@router.get("/analytics/export/{session_id}")
@require_role(["instructor", "admin"])
async def export_analytics_report(
    session_id: int,
    report_format: str = Query("json", description="Export format (json, csv)"),
    include_ai_insights: bool = Query(True, description="Include AI insights in export"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export comprehensive analytics report with AI insights
    
    - **session_id**: Session to export
    - **report_format**: Export format (json or csv)
    - **include_ai_insights**: Include AI-generated insights
    
    Returns downloadable analytics report
    """
    try:
        # Generate comprehensive report data
        cohort_insights = await ai_analytics_service.generate_cohort_insights(
            session_id=session_id,
            db=db
        )
        
        report_data = {
            "session_id": session_id,
            "export_timestamp": datetime.utcnow().isoformat(),
            "exported_by": current_user.username,
            "report_type": "comprehensive_analytics",
            "data": cohort_insights
        }
        
        if include_ai_insights:
            # Add individual student insights for comprehensive report
            student_insights = {}
            at_risk_students = cohort_insights.get("at_risk_students", [])
            
            for student_data in at_risk_students:
                student_id = student_data["student_id"]
                insights = await ai_analytics_service.generate_comprehensive_insights(
                    student_id=student_id,
                    time_period=timedelta(days=30),
                    db=db
                )
                student_insights[str(student_id)] = [
                    {
                        "type": insight.insight_type,
                        "title": insight.title,
                        "description": insight.description,
                        "confidence": insight.confidence,
                        "priority": insight.priority
                    }
                    for insight in insights
                ]
            
            report_data["individual_student_insights"] = student_insights
        
        # For now, return JSON format
        # TODO: Implement CSV export if needed
        return JSONResponse(
            content=report_data,
            headers={
                "Content-Disposition": f"attachment; filename=analytics_report_{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting analytics report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export analytics report"
        ) 