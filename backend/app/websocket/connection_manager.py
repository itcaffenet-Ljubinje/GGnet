"""
WebSocket connection manager for real-time client communication
"""

import json
from typing import Dict, Any, Optional, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.models.client import Client, ClientStatus
from app.models.machine import Machine

logger = structlog.get_logger()


class ConnectionManager:
    """
    Manages WebSocket connections for clients
    """
    
    def __init__(self):
        """Initialize connection manager"""
        # Active connections: {client_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Client info: {client_id: {machine_id, hostname, ip, ...}}
        self.client_info: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """
        Accept new WebSocket connection
        
        Args:
            websocket: WebSocket connection
            client_id: Client identifier
            
        Returns:
            True if connection accepted, False otherwise
        """
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            logger.info("Client connected", client_id=client_id)
            return True
        except Exception as e:
            logger.error("Failed to accept connection", client_id=client_id, error=str(e))
            return False
    
    def disconnect(self, client_id: str) -> None:
        """
        Remove WebSocket connection
        
        Args:
            client_id: Client identifier
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info("Client disconnected", client_id=client_id)
        
        if client_id in self.client_info:
            del self.client_info[client_id]
    
    async def send_personal_message(self, message: Dict[str, Any], client_id: str) -> bool:
        """
        Send message to specific client
        
        Args:
            message: Message dictionary
            client_id: Client identifier
            
        Returns:
            True if message sent, False otherwise
        """
        if client_id not in self.active_connections:
            logger.warning("Client not connected", client_id=client_id)
            return False
        
        try:
            websocket = self.active_connections[client_id]
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error("Failed to send message", client_id=client_id, error=str(e))
            self.disconnect(client_id)
            return False
    
    async def broadcast(self, message: Dict[str, Any], exclude: Optional[Set[str]] = None) -> int:
        """
        Broadcast message to all connected clients
        
        Args:
            message: Message dictionary
            exclude: Optional set of client IDs to exclude
            
        Returns:
            Number of clients that received the message
        """
        exclude = exclude or set()
        count = 0
        
        disconnected = []
        for client_id, websocket in self.active_connections.items():
            if client_id in exclude:
                continue
            
            try:
                await websocket.send_json(message)
                count += 1
            except Exception as e:
                logger.error("Failed to send message", client_id=client_id, error=str(e))
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
        
        return count
    
    def is_connected(self, client_id: str) -> bool:
        """
        Check if client is connected
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if connected, False otherwise
        """
        return client_id in self.active_connections
    
    def get_connected_clients(self) -> Set[str]:
        """
        Get set of connected client IDs
        
        Returns:
            Set of client IDs
        """
        return set(self.active_connections.keys())
    
    def update_client_info(self, client_id: str, info: Dict[str, Any]) -> None:
        """
        Update client information
        
        Args:
            client_id: Client identifier
            info: Client information dictionary
        """
        if client_id not in self.client_info:
            self.client_info[client_id] = {}
        
        self.client_info[client_id].update(info)
        self.client_info[client_id]["last_seen"] = datetime.utcnow().isoformat()
    
    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get client information
        
        Args:
            client_id: Client identifier
            
        Returns:
            Client information dictionary or None
        """
        return self.client_info.get(client_id)


# Global connection manager instance
connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get global connection manager instance"""
    return connection_manager




