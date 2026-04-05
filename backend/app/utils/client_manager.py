"""
Client management module - High-level client operations
Async version
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import structlog

from app.models.client import Client, ClientStatus
from app.models.machine import Machine
from app.websocket.connection_manager import get_connection_manager

logger = structlog.get_logger()


class ClientError(Exception):
    """Client management error"""
    pass


class ClientManager:
    """
    Client manager for high-level client operations
    Async version
    """
    
    def __init__(self):
        """Initialize client manager"""
        self.connection_manager = get_connection_manager()
    
    async def get_client_info(
        self,
        db: AsyncSession,
        client_id: str,
    ) -> Dict[str, Any]:
        """
        Get client information including connection status
        
        Args:
            db: Async database session
            client_id: Client identifier
            
        Returns:
            Client information dictionary
            
        Raises:
            ClientError: If client not found
        """
        stmt = select(Client).where(Client.client_id == client_id)
        result = await db.execute(stmt)
        client = result.scalar_one_or_none()
        
        if not client:
            raise ClientError(f"Client with ID {client_id} not found")
        
        # Build info dictionary
        info = {
            "id": client.id,
            "client_id": client.client_id,
            "hostname": client.hostname,
            "ip_address": client.ip_address,
            "os_version": client.os_version,
            "status": client.status.value,
            "last_seen": client.last_seen.isoformat() if client.last_seen else None,
            "created_at": client.created_at.isoformat() if client.created_at else None,
            "updated_at": client.updated_at.isoformat() if client.updated_at else None,
            "metadata": client.client_metadata,
            "is_connected": self.connection_manager.is_connected(client_id),
        }
        
        # Add machine info if linked
        if client.machine_id:
            stmt = select(Machine).where(Machine.id == client.machine_id)
            result = await db.execute(stmt)
            machine = result.scalar_one_or_none()
            if machine:
                info["machine"] = {
                    "id": machine.id,
                    "name": machine.name,
                    "mac_address": machine.mac_address,
                    "ip_address": machine.ip_address,
                }
        
        # Add connection info if connected
        if self.connection_manager.is_connected(client_id):
            conn_info = self.connection_manager.get_client_info(client_id)
            if conn_info:
                info["connection_info"] = conn_info
        
        return info
    
    async def send_message_to_client(
        self,
        client_id: str,
        message: Dict[str, Any],
    ) -> bool:
        """
        Send message to specific client
        
        Args:
            client_id: Client identifier
            message: Message dictionary
            
        Returns:
            True if message sent, False otherwise
        """
        return await self.connection_manager.send_personal_message(message, client_id)
    
    async def broadcast_message(
        self,
        message: Dict[str, Any],
        exclude: Optional[List[str]] = None,
    ) -> int:
        """
        Broadcast message to all connected clients
        
        Args:
            message: Message dictionary
            exclude: Optional list of client IDs to exclude
            
        Returns:
            Number of clients that received the message
        """
        exclude_set = set(exclude) if exclude else None
        return await self.connection_manager.broadcast(message, exclude=exclude_set)
    
    def get_connected_clients(self) -> List[str]:
        """
        Get list of connected client IDs
        
        Returns:
            List of client IDs
        """
        return list(self.connection_manager.get_connected_clients())
    
    async def update_client_status(
        self,
        db: AsyncSession,
        client_id: str,
        status: ClientStatus,
    ) -> Client:
        """
        Update client status
        
        Args:
            db: Async database session
            client_id: Client identifier
            status: New status
            
        Returns:
            Updated Client model
        """
        stmt = select(Client).where(Client.client_id == client_id)
        result = await db.execute(stmt)
        client = result.scalar_one_or_none()
        
        if not client:
            raise ClientError(f"Client with ID {client_id} not found")
        
        try:
            client.status = status
            client.last_seen = datetime.utcnow()
            await db.commit()
            await db.refresh(client)
            
            logger.info("Updated client status", client_id=client_id, status=status.value)
            return client
        except Exception as e:
            await db.rollback()
            raise ClientError(f"Failed to update client status: {e}") from e




