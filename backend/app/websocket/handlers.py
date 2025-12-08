"""
WebSocket handlers for client connections
"""

import json
from typing import Dict, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.models.client import Client, ClientStatus
from app.models.machine import Machine
from app.websocket.connection_manager import get_connection_manager

logger = structlog.get_logger()


class ClientError(Exception):
    """Client error"""
    pass


async def handle_client_connection(websocket: WebSocket, client_id: str, db: AsyncSession) -> None:
    """
    Handle client WebSocket connection
    
    Args:
        websocket: WebSocket connection
        client_id: Client identifier
        db: Async database session
    """
    connection_manager = get_connection_manager()
    
    try:
        # Accept connection
        if not await connection_manager.connect(websocket, client_id):
            return
        
        # Register or update client in database
        stmt = select(Client).where(Client.client_id == client_id)
        result = await db.execute(stmt)
        client = result.scalar_one_or_none()
        
        if not client:
            # Create new client record
            client = Client(
                client_id=client_id,
                status=ClientStatus.ONLINE,
                last_seen=datetime.utcnow(),
            )
            db.add(client)
        else:
            # Update existing client
            client.status = ClientStatus.ONLINE
            client.last_seen = datetime.utcnow()
        
        await db.commit()
        await db.refresh(client)
        
        # Send welcome message
        await connection_manager.send_personal_message({
            "type": "welcome",
            "client_id": client_id,
            "message": "Connected to GGnet server",
        }, client_id)
        
        # Handle messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_json()
                
                # Handle different message types
                message_type = data.get("type")
                
                if message_type == "register":
                    # Client registration
                    await handle_client_register(db, client_id, data)
                
                elif message_type == "heartbeat":
                    # Heartbeat/keepalive
                    await handle_heartbeat(db, client_id, data)
                
                elif message_type == "status_update":
                    # Status update from client
                    await handle_status_update(db, client_id, data)
                
                elif message_type == "machine_info":
                    # Machine information update
                    await handle_machine_info(db, client_id, data)
                
                else:
                    logger.warning("Unknown message type", message_type=message_type, client_id=client_id)
                
            except WebSocketDisconnect:
                logger.info("Client disconnected", client_id=client_id)
                break
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON", client_id=client_id, error=str(e))
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format",
                })
            except Exception as e:
                logger.error("Error handling message", client_id=client_id, error=str(e))
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                })
    
    except Exception as e:
        logger.error("Error in client connection handler", client_id=client_id, error=str(e))
    finally:
        # Update client status to offline
        stmt = select(Client).where(Client.client_id == client_id)
        result = await db.execute(stmt)
        client = result.scalar_one_or_none()
        
        if client:
            client.status = ClientStatus.OFFLINE
            client.last_seen = datetime.utcnow()
            await db.commit()
        
        # Disconnect
        connection_manager.disconnect(client_id)


async def handle_client_register(db: AsyncSession, client_id: str, data: Dict[str, Any]) -> None:
    """
    Handle client registration
    
    Args:
        db: Async database session
        client_id: Client identifier
        data: Registration data
    """
    connection_manager = get_connection_manager()
    
    try:
        stmt = select(Client).where(Client.client_id == client_id)
        result = await db.execute(stmt)
        client = result.scalar_one_or_none()
        
        if not client:
            raise ClientError(f"Client {client_id} not found")
        
        # Update client information
        if "hostname" in data:
            client.hostname = data["hostname"]
        if "ip_address" in data:
            client.ip_address = data["ip_address"]
        if "os_version" in data:
            client.os_version = data["os_version"]
        if "metadata" in data:
            client.client_metadata = data["metadata"]
        
        # Link to machine if MAC address provided
        if "mac_address" in data:
            stmt = select(Machine).where(Machine.mac_address == data["mac_address"])
            result = await db.execute(stmt)
            machine = result.scalar_one_or_none()
            if machine:
                client.machine_id = machine.id
        
        client.status = ClientStatus.ONLINE
        client.last_seen = datetime.utcnow()
        
        await db.commit()
        await db.refresh(client)
        
        # Update connection manager
        connection_manager.update_client_info(client_id, {
            "hostname": client.hostname,
            "ip_address": client.ip_address,
            "machine_id": client.machine_id,
        })
        
        # Send confirmation
        await connection_manager.send_personal_message({
            "type": "registered",
            "client_id": client_id,
            "message": "Registration successful",
        }, client_id)
        
        logger.info("Client registered", client_id=client_id)
    
    except Exception as e:
        logger.error("Failed to register client", client_id=client_id, error=str(e))
        await connection_manager.send_personal_message({
            "type": "error",
            "message": f"Registration failed: {e}",
        }, client_id)


async def handle_heartbeat(db: AsyncSession, client_id: str, data: Dict[str, Any]) -> None:
    """
    Handle client heartbeat
    
    Args:
        db: Async database session
        client_id: Client identifier
        data: Heartbeat data
    """
    connection_manager = get_connection_manager()
    
    try:
        stmt = select(Client).where(Client.client_id == client_id)
        result = await db.execute(stmt)
        client = result.scalar_one_or_none()
        
        if client:
            client.last_seen = datetime.utcnow()
            await db.commit()
        
        # Update connection manager
        connection_manager.update_client_info(client_id, {})
        
        # Send heartbeat response
        await connection_manager.send_personal_message({
            "type": "heartbeat_ack",
            "timestamp": datetime.utcnow().isoformat(),
        }, client_id)
    
    except Exception as e:
        logger.error("Failed to handle heartbeat", client_id=client_id, error=str(e))


async def handle_status_update(db: AsyncSession, client_id: str, data: Dict[str, Any]) -> None:
    """
    Handle client status update
    
    Args:
        db: Async database session
        client_id: Client identifier
        data: Status update data
    """
    connection_manager = get_connection_manager()
    
    try:
        stmt = select(Client).where(Client.client_id == client_id)
        result = await db.execute(stmt)
        client = result.scalar_one_or_none()
        
        if client:
            if "status" in data:
                try:
                    client.status = ClientStatus(data["status"])
                except ValueError:
                    pass
            client.last_seen = datetime.utcnow()
            await db.commit()
        
        # Update connection manager
        connection_manager.update_client_info(client_id, {
            "status": data.get("status", "online"),
        })
        
        logger.debug("Status updated", client_id=client_id, status=data.get("status"))
    
    except Exception as e:
        logger.error("Failed to handle status update", client_id=client_id, error=str(e))


async def handle_machine_info(db: AsyncSession, client_id: str, data: Dict[str, Any]) -> None:
    """
    Handle machine information update from client
    
    Args:
        db: Async database session
        client_id: Client identifier
        data: Machine information data
    """
    try:
        stmt = select(Client).where(Client.client_id == client_id)
        result = await db.execute(stmt)
        client = result.scalar_one_or_none()
        
        if not client or not client.machine_id:
            return
        
        stmt = select(Machine).where(Machine.id == client.machine_id)
        result = await db.execute(stmt)
        machine = result.scalar_one_or_none()
        
        if not machine:
            return
        
        # Update machine information
        if "hostname" in data:
            machine.hostname = data["hostname"]
        if "ip_address" in data:
            machine.ip_address = data["ip_address"]
        
        machine.is_online = True
        machine.last_seen = datetime.utcnow()
        
        await db.commit()
        
        logger.info("Machine info updated", machine_id=machine.id, machine_name=machine.name, client_id=client_id)
    
    except Exception as e:
        logger.error("Failed to handle machine info", client_id=client_id, error=str(e))

