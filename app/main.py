"""
AI Tutor Backend - Main FastAPI Application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn

from app.core.config import settings
from app.core.database import create_db_and_tables, test_connection

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format,
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Interactive learning platform with bubble graph navigation",
    debug=settings.debug,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Test database connection
    if not test_connection():
        logger.error("Failed to connect to database")
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    # Create tables (in production, use Alembic migrations)
    if settings.debug:
        create_db_and_tables()
        logger.info("Database tables created/verified")
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down application")


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_status = test_connection()
        return {
            "status": "healthy" if db_status else "unhealthy",
            "database": "connected" if db_status else "disconnected",
            "version": settings.app_version
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "version": settings.app_version
            }
        )


# Include API routers
from app.api import auth_router, courses_router, sessions_router, analytics_router, ai_tutor_router, progress_tracking_router, users_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(courses_router, prefix="/api/v1")  
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(ai_tutor_router, prefix="/api/v1")
app.include_router(progress_tracking_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    ) 