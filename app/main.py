from fastapi import FastAPI, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.database import get_db
from app.websocket.lesson_handler import lesson_websocket_endpoint
from app.api.analytics import router as analytics_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Tutor Backend",
    description="Real-time teaching pipeline with WebSocket support",
    version="0.1.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite React development server (default)
        "http://localhost:8080",  # Alternative Vite React development port
        "http://localhost:3000",  # Alternative React development port
        "http://localhost:8501",  # Streamlit (legacy)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(analytics_router)

@app.get("/")
async def root():
    return {"message": "AI Tutor Backend is running"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy", 
        "service": "ai-tutor-backend",
        "database": db_status,
        "websocket_endpoint": "/ws/lesson/{session_id}"
    }

@app.websocket("/ws/lesson/{session_id}")
async def websocket_lesson_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for lesson interactions"""
    await lesson_websocket_endpoint(websocket, session_id)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 