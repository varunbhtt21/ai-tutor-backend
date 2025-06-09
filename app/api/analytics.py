"""
Analytics API endpoints for AI Tutor dashboard
Provides learning analytics, performance metrics, and insights
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
import logging

from app.services.analytics_dashboard_service import AnalyticsDashboardService
from app.services.learning_analytics_service import LearningAnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Service instances
dashboard_service = AnalyticsDashboardService()
analytics_service = LearningAnalyticsService()

@router.get("/profile/{session_id}")
async def get_student_profile(
    session_id: str,
    user_id: str = Query(..., description="User ID for the student")
) -> Dict[str, Any]:
    """Get comprehensive student learning profile with insights and predictions"""
    try:
        profile = await analytics_service.analyze_student_profile(session_id, user_id)
        return {
            "status": "success",
            "data": profile
        }
    except Exception as e:
        logger.error(f"Error generating student profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate student profile: {str(e)}")

@router.get("/journey-map/{session_id}")
async def get_learning_journey_map(
    session_id: str,
    user_id: str = Query(..., description="User ID for the student")
) -> Dict[str, Any]:
    """Get interactive learning journey visualization data"""
    try:
        journey_data = await dashboard_service.get_learning_journey_map(session_id, user_id)
        return {
            "status": "success",
            "data": journey_data
        }
    except Exception as e:
        logger.error(f"Error generating journey map: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate journey map: {str(e)}")

@router.get("/performance/{session_id}")
async def get_performance_analytics(
    session_id: str,
    user_id: str = Query(..., description="User ID for the student")
) -> Dict[str, Any]:
    """Get comprehensive performance analytics and trends"""
    try:
        performance_data = await dashboard_service.get_performance_analytics(session_id, user_id)
        return {
            "status": "success",
            "data": performance_data
        }
    except Exception as e:
        logger.error(f"Error generating performance analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate performance analytics: {str(e)}")

@router.get("/heatmap/{session_id}")
async def get_concept_mastery_heatmap(
    session_id: str,
    user_id: str = Query(..., description="User ID for the student")
) -> Dict[str, Any]:
    """Get concept mastery heatmap for visualization"""
    try:
        heatmap_data = await dashboard_service.get_concept_mastery_heatmap(session_id, user_id)
        return {
            "status": "success",
            "data": heatmap_data
        }
    except Exception as e:
        logger.error(f"Error generating heatmap: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate heatmap: {str(e)}")

@router.get("/recommendations/{session_id}")
async def get_learning_recommendations(
    session_id: str,
    user_id: str = Query(..., description="User ID for the student")
) -> Dict[str, Any]:
    """Get AI-powered learning recommendations and next steps"""
    try:
        recommendations = await dashboard_service.get_learning_recommendations(session_id, user_id)
        return {
            "status": "success",
            "data": recommendations
        }
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")

@router.get("/engagement/{session_id}")
async def get_engagement_insights(
    session_id: str,
    user_id: str = Query(..., description="User ID for the student")
) -> Dict[str, Any]:
    """Get detailed engagement analysis and insights"""
    try:
        engagement_data = await dashboard_service.get_engagement_insights(session_id, user_id)
        return {
            "status": "success",
            "data": engagement_data
        }
    except Exception as e:
        logger.error(f"Error generating engagement insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate engagement insights: {str(e)}")

@router.get("/real-time/{session_id}")
async def get_real_time_insights(
    session_id: str,
    user_id: str = Query(..., description="User ID for the student"),
    current_concept: Optional[str] = Query(None, description="Current concept being discussed"),
    user_response: Optional[str] = Query(None, description="Latest user response")
) -> Dict[str, Any]:
    """Get real-time insights during conversation for immediate adaptation"""
    try:
        conversation_context = {
            "current_concept": current_concept,
            "user_response": user_response or ""
        }
        
        insights = await analytics_service.generate_real_time_insights(
            session_id, user_id, conversation_context
        )
        
        return {
            "status": "success",
            "data": insights
        }
    except Exception as e:
        logger.error(f"Error generating real-time insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate real-time insights: {str(e)}")

@router.get("/curriculum/summary")
async def get_curriculum_summary() -> Dict[str, Any]:
    """Get overall curriculum structure and statistics"""
    try:
        from app.services.learning_graph_service import LearningGraphService
        learning_graph = LearningGraphService()
        
        summary = await learning_graph.get_curriculum_summary()
        learning_graph.close()
        
        return {
            "status": "success",
            "data": summary
        }
    except Exception as e:
        logger.error(f"Error getting curriculum summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get curriculum summary: {str(e)}")

# Cleanup on shutdown
@router.on_event("shutdown")
async def cleanup_services():
    """Clean up service connections"""
    dashboard_service.close()
    analytics_service.close() 