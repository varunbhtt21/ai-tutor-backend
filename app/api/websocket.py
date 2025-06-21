"""
WebSocket API for real-time student tracking and instructor monitoring
Provides live updates for instructor dashboard and struggle alerts
"""

import json
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User
from app.services.student_tracking_service import StudentTrackingService

logger = logging.getLogger(__name__)

router = APIRouter()


async def authenticate_websocket_user(token: str) -> Optional[User]:
    """Authenticate user from WebSocket token"""
    if not token:
        return None
    
    try:
        token_data = verify_token(token)
        if not token_data:
            return None
        
        # Create user object from token data
        user = User(
            id=token_data.user_id or 1,
            username=token_data.username or "test_user",
            email=f"{token_data.username or 'test'}@example.com", 
            full_name=token_data.username or "Test User",
            role=token_data.role or "student"
        )
        return user
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        return None


class ConnectionManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self):
        # Instructor connections: {session_id: {instructor_id: websocket}}
        self.instructor_connections: Dict[int, Dict[int, WebSocket]] = {}
        
        # Student connections: {session_id: {student_id: websocket}}
        self.student_connections: Dict[int, Dict[int, WebSocket]] = {}
        
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        
        self.tracking_service = StudentTrackingService()

    async def connect_instructor(
        self, 
        websocket: WebSocket, 
        session_id: int, 
        instructor_id: int,
        instructor_name: str
    ):
        """Connect instructor to session monitoring"""
        await websocket.accept()
        
        if session_id not in self.instructor_connections:
            self.instructor_connections[session_id] = {}
        
        self.instructor_connections[session_id][instructor_id] = websocket
        
        # Store metadata
        self.connection_metadata[websocket] = {
            "type": "instructor",
            "session_id": session_id,
            "user_id": instructor_id,
            "user_name": instructor_name,
            "connected_at": datetime.utcnow()
        }
        
        logger.info(f"Instructor {instructor_name} connected to session {session_id}")
        
        # Send initial session state
        await self.send_session_overview(websocket, session_id)

    async def connect_student(
        self, 
        websocket: WebSocket, 
        session_id: int, 
        student_id: int,
        student_name: str
    ):
        """Connect student for real-time progress updates"""
        await websocket.accept()
        
        if session_id not in self.student_connections:
            self.student_connections[session_id] = {}
        
        self.student_connections[session_id][student_id] = websocket
        
        # Store metadata
        self.connection_metadata[websocket] = {
            "type": "student",
            "session_id": session_id,
            "user_id": student_id,
            "user_name": student_name,
            "connected_at": datetime.utcnow()
        }
        
        logger.info(f"Student {student_name} connected to session {session_id}")
        
        # Notify instructors of student connection
        await self.notify_instructors_student_joined(session_id, student_id, student_name)

    def disconnect(self, websocket: WebSocket):
        """Handle disconnection"""
        if websocket not in self.connection_metadata:
            return
        
        metadata = self.connection_metadata[websocket]
        session_id = metadata["session_id"]
        user_id = metadata["user_id"]
        user_type = metadata["type"]
        user_name = metadata["user_name"]
        
        # Remove from appropriate connections
        if user_type == "instructor":
            if session_id in self.instructor_connections:
                self.instructor_connections[session_id].pop(user_id, None)
                if not self.instructor_connections[session_id]:
                    del self.instructor_connections[session_id]
        else:  # student
            if session_id in self.student_connections:
                self.student_connections[session_id].pop(user_id, None)
                if not self.student_connections[session_id]:
                    del self.student_connections[session_id]
        
        # Clean up metadata
        del self.connection_metadata[websocket]
        
        logger.info(f"{user_type.title()} {user_name} disconnected from session {session_id}")

    async def send_struggle_alert(self, session_id: int, struggle_data: Dict[str, Any]):
        """Send struggle alert to all instructors monitoring the session"""
        if session_id not in self.instructor_connections:
            return
        
        message = {
            "type": "struggle_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": struggle_data
        }
        
        # Send to all instructors monitoring this session
        disconnected_connections = []
        for instructor_id, websocket in self.instructor_connections[session_id].items():
            try:
                await websocket.send_json(message)
                logger.info(f"Struggle alert sent to instructor {instructor_id} for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to send struggle alert to instructor {instructor_id}: {e}")
                disconnected_connections.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected_connections:
            self.disconnect(websocket)

    async def send_student_activity_update(
        self, 
        session_id: int, 
        student_id: int, 
        activity_data: Dict[str, Any]
    ):
        """Send real-time student activity updates to instructors"""
        if session_id not in self.instructor_connections:
            return
        
        message = {
            "type": "student_activity_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "student_id": student_id,
                "updates": activity_data
            }
        }
        
        # Send to all instructors
        for instructor_id, websocket in self.instructor_connections[session_id].items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send activity update to instructor {instructor_id}: {e}")

    async def send_progress_update(
        self, 
        session_id: int, 
        student_id: int, 
        progress_data: Dict[str, Any]
    ):
        """Send progress updates to both instructors and the student"""
        # Send to instructors
        await self.send_student_activity_update(session_id, student_id, progress_data)
        
        # Send to the student
        if (session_id in self.student_connections and 
            student_id in self.student_connections[session_id]):
            
            message = {
                "type": "progress_update",
                "timestamp": datetime.utcnow().isoformat(),
                "data": progress_data
            }
            
            try:
                websocket = self.student_connections[session_id][student_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send progress update to student {student_id}: {e}")

    async def send_session_overview(self, websocket: WebSocket, session_id: int):
        """Send current session overview to newly connected instructor"""
        try:
            # Get current session state from tracking service
            overview = await self.tracking_service.get_session_overview(session_id)
            
            message = {
                "type": "session_overview",
                "timestamp": datetime.utcnow().isoformat(),
                "data": overview
            }
            
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send session overview: {e}")

    async def notify_instructors_student_joined(
        self, 
        session_id: int, 
        student_id: int, 
        student_name: str
    ):
        """Notify instructors when a student joins the session"""
        if session_id not in self.instructor_connections:
            return
        
        message = {
            "type": "student_joined",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "student_id": student_id,
                "student_name": student_name
            }
        }
        
        for instructor_id, websocket in self.instructor_connections[session_id].items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to notify instructor {instructor_id} of student join: {e}")

    def get_connected_students(self, session_id: int) -> List[int]:
        """Get list of currently connected students for a session"""
        if session_id not in self.student_connections:
            return []
        return list(self.student_connections[session_id].keys())

    def get_connected_instructors(self, session_id: int) -> List[int]:
        """Get list of currently connected instructors for a session"""
        if session_id not in self.instructor_connections:
            return []
        return list(self.instructor_connections[session_id].keys())


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws/instructor/{session_id}")
async def instructor_websocket(
    websocket: WebSocket, 
    session_id: int,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for instructor real-time monitoring"""
    user = None
    try:
        # Authenticate user via query parameters
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        # Verify token and get user
        user = await authenticate_websocket_user(token)
        if not user:
            await websocket.close(code=4001, reason="Invalid authentication token")
            return
        
        # Check if user is authorized to be an instructor
        if user.role not in ["instructor", "admin"]:
            await websocket.close(code=4003, reason="Unauthorized: Instructor access required")
            return
        
        # Connect instructor
        await manager.connect_instructor(
            websocket, 
            session_id, 
            user.id,
            user.full_name or user.username
        )
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_json()
                await handle_instructor_message(data, session_id, websocket, db)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling instructor message: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"Instructor WebSocket disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"Instructor WebSocket error: {e}")
    finally:
        if websocket:
            manager.disconnect(websocket)


@router.websocket("/ws/student/{session_id}")
async def student_websocket(
    websocket: WebSocket, 
    session_id: int,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for student real-time updates"""
    user = None
    try:
        # Authenticate student
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        # Verify token and get user
        user = await authenticate_websocket_user(token)
        if not user:
            await websocket.close(code=4001, reason="Invalid authentication token")
            return
        
        # Connect student
        await manager.connect_student(
            websocket, 
            session_id, 
            user.id,
            user.full_name or user.username
        )
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_json()
                await handle_student_message(data, session_id, websocket, db)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling student message: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"Student WebSocket disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"Student WebSocket error: {e}")
    finally:
        if websocket:
            manager.disconnect(websocket)


async def handle_instructor_message(
    data: Dict[str, Any], 
    session_id: int, 
    websocket: WebSocket, 
    db: Session
):
    """Handle incoming messages from instructors"""
    message_type = data.get("type")
    
    if message_type == "request_student_data":
        student_id = data.get("student_id")
        if student_id:
            # Send detailed student analytics
            student_data = await manager.tracking_service.get_detailed_student_analytics(
                student_id, session_id, db
            )
            
            response = {
                "type": "student_analytics",
                "data": student_data
            }
            await websocket.send_json(response)
    
    elif message_type == "intervention_acknowledged":
        # Mark intervention as acknowledged
        struggle_id = data.get("struggle_id")
        if struggle_id:
            await manager.tracking_service.acknowledge_struggle_intervention(
                struggle_id, db
            )


async def handle_student_message(
    data: Dict[str, Any], 
    session_id: int, 
    websocket: WebSocket, 
    db: Session
):
    """Handle incoming messages from students"""
    message_type = data.get("type")
    
    if message_type == "ping":
        # Keep-alive ping
        await websocket.send_json({"type": "pong"})
    
    elif message_type == "request_hints":
        # Student requesting hints
        node_id = data.get("node_id")
        # Handle hint request logic here


# Export the manager for use in other services
__all__ = ["router", "manager"] 