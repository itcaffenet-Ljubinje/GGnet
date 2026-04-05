"""
Clients API endpoints
Client management and WebSocket connections
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
import structlog

from app.core.dependencies import get_db, require_operator, get_current_user
from app.models.user import User
from app.models.client import Client, ClientStatus
from app.models.machine import Machine
from app.utils.client_manager import ClientManager, ClientError
from app.websocket.connection_manager import get_connection_manager
from app.websocket.handlers import handle_client_connection

router = APIRouter(prefix="/clients", tags=["clients"])
logger = structlog.get_logger()

client_manager = ClientManager()


class ClientRegisterRequest(BaseModel):
    """Client registration request"""
    client_id: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    os_version: Optional[str] = None
    mac_address: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ClientMessageRequest(BaseModel):
    """Client message request"""
    message: Dict[str, Any]


@router.get("", response_model=List[Dict[str, Any]])
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[ClientStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List all clients"""
    try:
        connection_manager = get_connection_manager()
        
        stmt = select(Client)
        
        if status_filter:
            stmt = stmt.where(Client.status == status_filter)
        
        stmt = stmt.order_by(Client.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        clients = result.scalars().all()
        
        return [
            {
                "id": c.id,
                "client_id": c.client_id,
                "hostname": c.hostname,
                "ip_address": c.ip_address,
                "os_version": c.os_version,
                "status": c.status.value,
                "is_connected": connection_manager.is_connected(c.client_id),
                "last_seen": c.last_seen.isoformat() if c.last_seen else None,
            }
            for c in clients
        ]
    except Exception as e:
        logger.error("Failed to list clients", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list clients: {str(e)}"
        )


@router.get("/connected/list", response_model=List[str])
async def list_connected_clients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[str]:
    """List all connected client IDs"""
    try:
        return client_manager.get_connected_clients()
    except Exception as e:
        logger.error("Failed to list connected clients", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list connected clients: {str(e)}"
        )


@router.get("/{client_id}", response_model=Dict[str, Any])
async def get_client(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get client by ID with detailed information"""
    try:
        return await client_manager.get_client_info(db, client_id)
    except ClientError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Failed to get client", client_id=client_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client: {str(e)}"
        )


@router.post("/register", response_model=Dict[str, Any])
async def register_client(
    request: ClientRegisterRequest,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Register new client"""
    try:
        # Check if client already exists
        stmt = select(Client).where(Client.client_id == request.client_id)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing client
            if request.hostname:
                existing.hostname = request.hostname
            if request.ip_address:
                existing.ip_address = request.ip_address
            if request.os_version:
                existing.os_version = request.os_version
            if request.metadata:
                existing.client_metadata = request.metadata
            
            # Link to machine if MAC address provided
            if request.mac_address:
                stmt = select(Machine).where(Machine.mac_address == request.mac_address)
                result = await db.execute(stmt)
                machine = result.scalar_one_or_none()
                if machine:
                    existing.machine_id = machine.id
            
            existing.status = ClientStatus.ONLINE
            existing.last_seen = datetime.utcnow()
            
            await db.commit()
            await db.refresh(existing)
            
            return {
                "id": existing.id,
                "client_id": existing.client_id,
                "hostname": existing.hostname,
                "ip_address": existing.ip_address,
                "status": existing.status.value,
                "message": "Client updated successfully",
            }
        
        # Create new client
        client = Client(
            client_id=request.client_id,
            hostname=request.hostname,
            ip_address=request.ip_address,
            os_version=request.os_version,
            client_metadata=request.metadata,
            status=ClientStatus.ONLINE,
            last_seen=datetime.utcnow(),
        )
        
        # Link to machine if MAC address provided
        if request.mac_address:
            stmt = select(Machine).where(Machine.mac_address == request.mac_address)
            result = await db.execute(stmt)
            machine = result.scalar_one_or_none()
            if machine:
                client.machine_id = machine.id
        
        db.add(client)
        await db.commit()
        await db.refresh(client)
        
        return {
            "id": client.id,
            "client_id": client.client_id,
            "hostname": client.hostname,
            "ip_address": client.ip_address,
            "status": client.status.value,
            "message": "Client registered successfully",
        }
    except Exception as e:
        await db.rollback()
        logger.error("Failed to register client", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register client: {str(e)}"
        )


@router.get("/{client_id}/status", response_model=Dict[str, Any])
async def get_client_status(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get client connection status"""
    try:
        connection_manager = get_connection_manager()
        
        stmt = select(Client).where(Client.client_id == client_id)
        result = await db.execute(stmt)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {client_id} not found"
            )
        
        return {
            "client_id": client_id,
            "status": client.status.value,
            "is_connected": connection_manager.is_connected(client_id),
            "last_seen": client.last_seen.isoformat() if client.last_seen else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get client status", client_id=client_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client status: {str(e)}"
        )


@router.post("/{client_id}/message", response_model=Dict[str, str])
async def send_message_to_client(
    client_id: str,
    request: ClientMessageRequest = Body(...),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Send message to specific client"""
    try:
        sent = await client_manager.send_message_to_client(client_id, request.message)
        if sent:
            return {"message": f"Message sent to client {client_id}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Client {client_id} is not connected"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to send message", client_id=client_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.post("/broadcast", response_model=Dict[str, Any])
async def broadcast_message(
    request: ClientMessageRequest = Body(...),
    exclude: Optional[List[str]] = Query(None, description="List of client IDs to exclude"),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Broadcast message to all connected clients"""
    try:
        count = await client_manager.broadcast_message(request.message, exclude=exclude)
        return {
            "message": "Message broadcasted",
            "recipients": count,
        }
    except Exception as e:
        logger.error("Failed to broadcast message", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to broadcast message: {str(e)}"
        )


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for client connections"""
    from app.core.database import get_async_session_local
    
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as db:
        try:
            await handle_client_connection(websocket, client_id, db)
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected", client_id=client_id)
        except Exception as e:
            logger.error("WebSocket error", client_id=client_id, error=str(e))

