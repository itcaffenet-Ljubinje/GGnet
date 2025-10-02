"""
Session management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import structlog
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_operator, log_user_activity, get_client_ip
from app.models.user import User
from app.models.session import Session, SessionStatus, SessionType
from app.models.target import Target
from app.models.machine import Machine
from app.models.audit import AuditAction
from app.core.exceptions import ValidationError, NotFoundError, SessionError

router = APIRouter()
logger = structlog.get_logger()


# Pydantic models
class SessionResponse(BaseModel):
    id: int
    session_id: str
    session_type: SessionType
    status: SessionStatus
    machine_id: int
    machine_name: str
    target_id: int
    target_name: str
    client_ip: Optional[str]
    server_ip: str
    boot_method: Optional[str]
    started_at: str
    ended_at: Optional[str]
    duration_seconds: Optional[int]
    iscsi_info: Optional[dict]
    
    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    target_id: int
    session_type: SessionType = SessionType.DISKLESS_BOOT
    boot_method: Optional[str] = "uefi"


class SessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    boot_time: Optional[datetime] = None
    os_load_time: Optional[datetime] = None
    ready_time: Optional[datetime] = None


@router.post("/start", response_model=SessionResponse)
async def start_session(
    session_data: SessionCreate,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Start a new diskless boot session"""
    
    # Validate target exists and is ready
    target_result = await db.execute(select(Target).where(Target.id == session_data.target_id))
    target = target_result.scalar_one_or_none()
    
    if not target:
        raise NotFoundError(f"Target with ID {session_data.target_id} not found")
    
    if not target.is_ready:
        raise SessionError(f"Target '{target.name}' is not ready for sessions")
    
    # Get machine
    machine_result = await db.execute(select(Machine).where(Machine.id == target.machine_id))
    machine = machine_result.scalar_one()
    
    # Check if machine already has an active session
    active_session_result = await db.execute(
        select(Session).where(
            Session.machine_id == machine.id,
            Session.status.in_([SessionStatus.STARTING, SessionStatus.ACTIVE])
        )
    )
    active_session = active_session_result.scalar_one_or_none()
    
    if active_session:
        raise SessionError(f"Machine '{machine.name}' already has an active session")
    
    # Generate unique session ID
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    
    # Create session
    session = Session(
        session_id=session_id,
        session_type=session_data.session_type,
        machine_id=machine.id,
        target_id=target.id,
        client_ip=get_client_ip(request),
        server_ip=target.portal_ip,
        boot_method=session_data.boot_method,
        initiated_by=current_user.username
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    # TODO: Actually create iSCSI target and start services
    # For now, we'll simulate the process
    
    # Update session status to active
    session.status = SessionStatus.ACTIVE
    session.boot_time = datetime.utcnow()
    
    # Update target connection count
    target.connection_count += 1
    target.last_connected = datetime.utcnow()
    
    await db.commit()
    
    # Log activity
    await log_user_activity(
        action=AuditAction.SESSION_STARTED,
        message=f"Session '{session.session_id}' started for machine '{machine.name}'",
        request=request,
        user=current_user,
        resource_type="session",
        resource_id=session.id,
        resource_name=session.session_id,
        db=db
    )
    
    logger.info(
        "Session started",
        session_id=session.session_id,
        machine_id=machine.id,
        target_id=target.id,
        user_id=current_user.id
    )
    
    # Build response
    response = SessionResponse.from_orm(session)
    response.machine_name = machine.name
    response.target_name = target.name
    response.iscsi_info = {
        "portal": f"{target.portal_ip}:{target.portal_port}",
        "iqn": target.iqn,
        "lun_mapping": target.get_lun_mapping()
    }
    
    return response


@router.post("/{session_id}/stop")
async def stop_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Stop a running session"""
    
    result = await db.execute(select(Session).where(Session.session_id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise NotFoundError(f"Session with ID {session_id} not found")
    
    if session.status not in [SessionStatus.STARTING, SessionStatus.ACTIVE]:
        raise SessionError(f"Session '{session_id}' is not running")
    
    # Update session status
    session.status = SessionStatus.STOPPING
    session.ended_at = datetime.utcnow()
    
    # Update target connection count
    target_result = await db.execute(select(Target).where(Target.id == session.target_id))
    target = target_result.scalar_one()
    target.connection_count = max(0, target.connection_count - 1)
    
    await db.commit()
    
    # TODO: Actually stop iSCSI target and cleanup
    
    # Update final status
    session.status = SessionStatus.STOPPED
    await db.commit()
    
    # Log activity
    await log_user_activity(
        action=AuditAction.SESSION_STOPPED,
        message=f"Session '{session.session_id}' stopped",
        request=request,
        user=current_user,
        resource_type="session",
        resource_id=session.id,
        resource_name=session.session_id,
        db=db
    )
    
    logger.info("Session stopped", session_id=session.session_id, user_id=current_user.id)
    
    return {"message": f"Session '{session_id}' stopped successfully"}


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[SessionStatus] = None,
    machine_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all sessions"""
    
    # Build query
    query = select(Session)
    
    # Add filters
    if status:
        query = query.where(Session.status == status)
    if machine_id:
        query = query.where(Session.machine_id == machine_id)
    
    # Add pagination
    query = query.offset(skip).limit(limit).order_by(Session.started_at.desc())
    
    # Execute query
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    # Build response with related data
    response_sessions = []
    for session in sessions:
        # Get machine
        machine_result = await db.execute(select(Machine).where(Machine.id == session.machine_id))
        machine = machine_result.scalar_one()
        
        # Get target
        target_result = await db.execute(select(Target).where(Target.id == session.target_id))
        target = target_result.scalar_one()
        
        response = SessionResponse.from_orm(session)
        response.machine_name = machine.name
        response.target_name = target.name
        
        if session.is_active:
            response.iscsi_info = {
                "portal": f"{target.portal_ip}:{target.portal_port}",
                "iqn": target.iqn,
                "lun_mapping": target.get_lun_mapping()
            }
        
        response_sessions.append(response)
    
    return response_sessions


@router.get("/{session_id}/status", response_model=SessionResponse)
async def get_session_status(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get session status"""
    
    result = await db.execute(select(Session).where(Session.session_id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise NotFoundError(f"Session with ID {session_id} not found")
    
    # Get related data
    machine_result = await db.execute(select(Machine).where(Machine.id == session.machine_id))
    machine = machine_result.scalar_one()
    
    target_result = await db.execute(select(Target).where(Target.id == session.target_id))
    target = target_result.scalar_one()
    
    response = SessionResponse.from_orm(session)
    response.machine_name = machine.name
    response.target_name = target.name
    
    if session.is_active:
        response.iscsi_info = {
            "portal": f"{target.portal_ip}:{target.portal_port}",
            "iqn": target.iqn,
            "lun_mapping": target.get_lun_mapping()
        }
    
    return response

