"""
WebSocket connection manager for real-time updates
"""

import json
import asyncio
from typing import Dict, List, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger()


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_groups: Dict[str, Set[str]] = {
            "all": set(),
            "admins": set(),
            "operators": set(),
            "viewers": set()
        }
    
    async def connect(self, websocket: WebSocket, token: Optional[str] = None):
        """Accept a new WebSocket connection"""
        # Generate a unique connection ID
        connection_id = f"conn_{len(self.active_connections)}_{asyncio.get_event_loop().time()}"
        self.active_connections[connection_id] = websocket
        
        # Add to "all" group by default
        self.connection_groups["all"].add(connection_id)
        
        logger.info("WebSocket connection established", connection_id=connection_id)
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "message": "Connected to real-time updates",
            "connection_id": connection_id
        }, connection_id)
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            
            # Remove from all groups
            for group in self.connection_groups.values():
                group.discard(connection_id)
            
            logger.info("WebSocket connection closed", connection_id=connection_id)
    
    async def disconnect_all(self):
        """Close all WebSocket connections"""
        for connection_id in list(self.active_connections.keys()):
            await self.disconnect(connection_id)
    
    async def send_personal_message(self, message: dict, connection_id: str):
        """Send a message to a specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error("Failed to send personal message", 
                           connection_id=connection_id, error=str(e))
                await self.disconnect(connection_id)
    
    async def broadcast_to_group(self, message: dict, group: str):
        """Broadcast a message to all connections in a group"""
        if group in self.connection_groups:
            for connection_id in list(self.connection_groups[group]):
                await self.send_personal_message(message, connection_id)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected clients"""
        await self.broadcast_to_group(message, "all")
    
    async def handle_client_message(self, connection_id: str, message: dict):
        """Handle incoming messages from clients"""
        message_type = message.get("type")
        
        if message_type == "ping":
            await self.send_personal_message({"type": "pong"}, connection_id)
        elif message_type == "subscribe":
            # Handle subscription to specific groups
            groups = message.get("groups", [])
            for group in groups:
                if group in self.connection_groups:
                    self.connection_groups[group].add(connection_id)
                    logger.info("Client subscribed to group", 
                              connection_id=connection_id, group=group)
        elif message_type == "unsubscribe":
            # Handle unsubscription from specific groups
            groups = message.get("groups", [])
            for group in groups:
                if group in self.connection_groups:
                    self.connection_groups[group].discard(connection_id)
                    logger.info("Client unsubscribed from group", 
                              connection_id=connection_id, group=group)
        else:
            logger.warning("Unknown message type received", 
                         connection_id=connection_id, message_type=message_type)
    
    async def send_system_update(self, update_type: str, data: dict):
        """Send a system update to all connected clients"""
        message = {
            "type": update_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast_to_all(message)
        logger.info("System update broadcasted", update_type=update_type)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
