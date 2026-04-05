"""
VNC Console Management API
Provides remote console access to machines via noVNC
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict
from datetime import datetime
import structlog
import subprocess
import json
import os
from pathlib import Path

from app.core.dependencies import get_db, get_current_user, require_operator
from app.core.config import get_settings
from app.models.user import User
from app.models.machine import Machine
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/vnc", tags=["vnc-console"])
logger = structlog.get_logger()
settings = get_settings()


class VNCConnectionInfo(BaseModel):
    """VNC connection information"""
    machine_id: int
    machine_name: str
    vnc_host: str
    vnc_port: int
    vnc_password: Optional[str] = None
    websocket_url: str
    no_vnc_url: str
    status: str  # "active", "inactive", "error"
    created_at: datetime


class VNCConnectionResponse(BaseModel):
    """Response model for VNC connection"""
    connection_id: str
    machine_id: int
    machine_name: str
    vnc_host: str
    vnc_port: int
    websocket_url: str
    no_vnc_url: str
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class VNCConnectionCreate(BaseModel):
    """Request model for creating VNC connection"""
    machine_id: int
    vnc_host: Optional[str] = None  # Defaults to machine IP or server IP
    vnc_port: Optional[int] = None  # Defaults to 5900 + machine_id
    vnc_password: Optional[str] = None


# In-memory storage for VNC connections (in production, use database)
_vnc_connections: Dict[int, Dict[str, Any]] = {}


def generate_vnc_password() -> str:
    """Generate a random VNC password"""
    import secrets
    import string
    # VNC passwords are 8 characters max
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(8))


def get_vnc_port(machine_id: int) -> int:
    """Get VNC port for machine (5900 + machine_id, max 5999)"""
    base_port = 5900
    port = base_port + (machine_id % 100)  # Keep within valid VNC port range
    return port


@router.post("/connect", response_model=VNCConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_vnc_connection(
    connection_data: VNCConnectionCreate,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Create a VNC connection for a machine"""
    # Get machine
    result = await db.execute(
        select(Machine).where(Machine.id == connection_data.machine_id)
    )
    machine = result.scalar_one_or_none()
    
    if not machine:
        raise NotFoundError(f"Machine with ID {connection_data.machine_id} not found")
    
    # Determine VNC host and port
    vnc_host = connection_data.vnc_host or machine.ip_address or settings.ISCSI_PORTAL_IP
    vnc_port = connection_data.vnc_port or get_vnc_port(machine.id)
    vnc_password = connection_data.vnc_password or generate_vnc_password()
    
    # Generate connection ID
    connection_id = f"vnc-{machine.id}-{int(datetime.utcnow().timestamp())}"
    
    # Create connection record
    connection_info = {
        "connection_id": connection_id,
        "machine_id": machine.id,
        "machine_name": machine.name,
        "vnc_host": vnc_host,
        "vnc_port": vnc_port,
        "vnc_password": vnc_password,
        "websocket_url": f"ws://{vnc_host}:{vnc_port}",
        "no_vnc_url": f"/vnc/console/{connection_id}",
        "status": "active",
        "created_at": datetime.utcnow(),
        "created_by": current_user.id
    }
    
    _vnc_connections[machine.id] = connection_info
    
    logger.info(
        "VNC connection created",
        connection_id=connection_id,
        machine_id=machine.id,
        vnc_host=vnc_host,
        vnc_port=vnc_port
    )
    
    return VNCConnectionResponse(
        connection_id=connection_id,
        machine_id=machine.id,
        machine_name=machine.name,
        vnc_host=vnc_host,
        vnc_port=vnc_port,
        websocket_url=connection_info["websocket_url"],
        no_vnc_url=connection_info["no_vnc_url"],
        status="active",
        created_at=connection_info["created_at"]
    )


@router.get("/machine/{machine_id}", response_model=VNCConnectionResponse)
async def get_vnc_connection(
    machine_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get VNC connection for a machine"""
    if machine_id not in _vnc_connections:
        raise NotFoundError(f"No VNC connection found for machine {machine_id}")
    
    connection = _vnc_connections[machine_id]
    
    return VNCConnectionResponse(
        connection_id=connection["connection_id"],
        machine_id=connection["machine_id"],
        machine_name=connection["machine_name"],
        vnc_host=connection["vnc_host"],
        vnc_port=connection["vnc_port"],
        websocket_url=connection["websocket_url"],
        no_vnc_url=connection["no_vnc_url"],
        status=connection["status"],
        created_at=connection["created_at"]
    )


@router.get("", response_model=List[VNCConnectionResponse])
async def list_vnc_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all active VNC connections"""
    connections = []
    for machine_id, connection in _vnc_connections.items():
        connections.append(VNCConnectionResponse(
            connection_id=connection["connection_id"],
            machine_id=connection["machine_id"],
            machine_name=connection["machine_name"],
            vnc_host=connection["vnc_host"],
            vnc_port=connection["vnc_port"],
            websocket_url=connection["websocket_url"],
            no_vnc_url=connection["no_vnc_url"],
            status=connection["status"],
            created_at=connection["created_at"]
        ))
    
    return connections


@router.delete("/machine/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_vnc(
    machine_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect VNC connection for a machine"""
    if machine_id not in _vnc_connections:
        raise NotFoundError(f"No VNC connection found for machine {machine_id}")
    
    connection = _vnc_connections.pop(machine_id)
    
    logger.info(
        "VNC connection disconnected",
        connection_id=connection["connection_id"],
        machine_id=machine_id
    )


@router.get("/console/{connection_id}")
async def vnc_console_page(
    connection_id: str,
    current_user: User = Depends(get_current_user)
):
    """Serve noVNC console page"""
    # Find connection
    connection = None
    for conn in _vnc_connections.values():
        if conn["connection_id"] == connection_id:
            connection = conn
            break
    
    if not connection:
        raise NotFoundError(f"VNC connection {connection_id} not found")
    
    # Generate noVNC HTML page
    # Escape HTML to prevent XSS
    machine_name_escaped = connection['machine_name'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    vnc_password_escaped = connection.get('vnc_password', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", "&#x27;")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>VNC Console - {machine_name_escaped}</title>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/@novnc/core@1.4.0/lib/rfb.min.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: #1a1a1a;
                font-family: Arial, sans-serif;
            }}
            #noVNC_control_bar {{
                background: #2d2d2d;
                padding: 10px;
                color: white;
            }}
            #noVNC_screen {{
                width: 100%;
                height: calc(100vh - 60px);
                background: #000;
            }}
            .vnc-controls {{
                margin: 10px 0;
            }}
            .vnc-controls button {{
                background: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                margin: 0 5px;
                cursor: pointer;
                border-radius: 4px;
            }}
            .vnc-controls button:hover {{
                background: #45a049;
            }}
        </style>
    </head>
    <body>
        <div id="noVNC_control_bar">
            <h3>VNC Console: {machine_name_escaped}</h3>
            <div class="vnc-controls">
                <button onclick="connectVNC()">Connect</button>
                <button onclick="disconnectVNC()">Disconnect</button>
                <button onclick="sendCtrlAltDel()">Send Ctrl+Alt+Del</button>
            </div>
        </div>
        <div id="noVNC_screen"></div>
        
        <script>
            let rfb;
            const vncHost = '{connection['vnc_host']}';
            const vncPort = {connection['vnc_port']};
            const vncPassword = '{vnc_password_escaped}';
            
            function connectVNC() {{
                const target = document.getElementById('noVNC_screen');
                rfb = new RFB({{
                    target: target,
                    encrypt: false,
                    credentials: {{
                        password: vncPassword
                    }}
                }});
                
                rfb.connect(vncHost, vncPort);
                
                rfb.addEventListener("connect", () => {{
                    console.log("VNC connected");
                }});
                
                rfb.addEventListener("disconnect", (e) => {{
                    console.log("VNC disconnected:", e.detail.clean ? "clean" : "unclean");
                }});
            }}
            
            function disconnectVNC() {{
                if (rfb) {{
                    rfb.disconnect();
                }}
            }}
            
            function sendCtrlAltDel() {{
                if (rfb) {{
                    rfb.sendCtrlAltDel();
                }}
            }}
            
            // Auto-connect on load
            window.addEventListener('load', () => {{
                connectVNC();
            }});
        </script>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)


@router.websocket("/ws/{connection_id}")
async def vnc_websocket(
    websocket: WebSocket,
    connection_id: str,
    current_user: User = Depends(get_current_user)
):
    """WebSocket endpoint for VNC proxy (if needed)"""
    await websocket.accept()
    
    # Find connection
    connection = None
    for conn in _vnc_connections.values():
        if conn["connection_id"] == connection_id:
            connection = conn
            break
    
    if not connection:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        while True:
            data = await websocket.receive_text()
            # Proxy VNC data through WebSocket
            # This is a simplified version - full implementation would
            # connect to actual VNC server and proxy the data
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        logger.info("VNC WebSocket disconnected", connection_id=connection_id)

