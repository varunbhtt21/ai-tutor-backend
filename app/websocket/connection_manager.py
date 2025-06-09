from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for learning sessions"""
    
    def __init__(self):
        # Map of client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Map of session_id -> List[client_id] 
        self.session_connections: Dict[str, List[str]] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str, client_id: str):
        """Accept WebSocket connection and store it"""
        await websocket.accept()
        
        self.active_connections[client_id] = websocket
        
        if session_id not in self.session_connections:
            self.session_connections[session_id] = []
        self.session_connections[session_id].append(client_id)
        
        logger.info(f"Client {client_id} connected to session {session_id}")
        
    def disconnect(self, session_id: str, client_id: str):
        """Remove connection and clean up"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
        if session_id in self.session_connections:
            if client_id in self.session_connections[session_id]:
                self.session_connections[session_id].remove(client_id)
                
            # Clean up empty sessions
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]
                
        logger.info(f"Client {client_id} disconnected from session {session_id}")
        
    async def send_personal_message(self, client_id: str, message: dict):
        """Send message to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                
    async def send_to_session(self, session_id: str, message: dict):
        """Send message to all clients in a session"""
        if session_id in self.session_connections:
            for client_id in self.session_connections[session_id]:
                await self.send_personal_message(client_id, message)
                
    def get_session_clients(self, session_id: str) -> List[str]:
        """Get list of client IDs in a session"""
        return self.session_connections.get(session_id, [])
        
    def is_session_active(self, session_id: str) -> bool:
        """Check if session has any active connections"""
        return session_id in self.session_connections and len(self.session_connections[session_id]) > 0 