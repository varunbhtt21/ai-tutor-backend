"""
API routes for AI Tutor Backend
"""

from .auth import router as auth_router
from .courses import router as courses_router
from .sessions import router as sessions_router
from .analytics import router as analytics_router
from .ai_tutor import router as ai_tutor_router
from .progress_tracking import router as progress_tracking_router
from .users import router as users_router

__all__ = ["auth_router", "courses_router", "sessions_router", "analytics_router", "ai_tutor_router", "progress_tracking_router", "users_router"] 