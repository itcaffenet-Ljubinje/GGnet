"""
Session management endpoints with enhanced security
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel, ConfigDict
import structlog
import uuid
import asyncio
import subprocess
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_operator, log_user_activity, get_client_ip
from app.core.security import revoke_token, revoke_user_sessions, get_active_sessions
from app.models.user import User
from app.models.session import Session, SessionStatus, SessionType
from app.models.target import Target, TargetStatus
from app.models.machine import Machine
from app.models.image import Image
from app.models.audit import AuditAction
from app.core.exceptions import ValidationError, NotFoundError

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
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    iscsi_info: Optional[dict]
    
    model_config = ConfigDict(from_attributes=True)


class SessionCreate(BaseModel):
    target_id: int
    session_type: SessionType = SessionType.DISKLESS_BOOT
    boot_method: Optional[str] = None


class SessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    client_ip: Optional[str] = None
    boot_method: Optional[str] = None


class SessionStats(BaseModel):
    total_sessions: int
    active_sessions: int
    completed_sessions: int
    failed_sessions: int
    total_uptime_hours: float
    average_session_duration: float
    sessions_today: int
    sessions_this_week: int


class ActiveSessionInfo(BaseModel):
    id: int
    session_id: str
    machine_name: str
    machine_mac: str
    client_ip: str
    target_name: str
    image_name: str
    started_at: datetime
    duration_minutes: int
    status: SessionStatus
    iscsi_connection: bool
    boot_progress: Optional[str]


class SessionSecurityInfo(BaseModel):
    user_id: int
    username: str
    active_sessions: int
    last_login: Optional[datetime]
    session_ips: List[str]
    suspicious_activity: bool


@router.post("", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Create a new session"""
    
    # Get target
    result = await db.execute(select(Target).where(Target.id == session_data.target_id))
    target = result.scalar_one_or_none()
    
    if not target:
        raise NotFoundError("Target not found")
    
    # Check if target is available
    if target.status != TargetStatus.ACTIVE:
        raise ValidationError("Target is not active")
    
    # Check for existing active session for this target
    existing_result = await db.execute(
        select(Session).where(
            Session.target_id == session_data.target_id,
            Session.status == SessionStatus.ACTIVE
        )
    )
    if existing_result.scalar_one_or_none():
        raise ValidationError("Target already has an active session")
    
    try:
        # Create session
        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=session_data.session_type,
            target_id=session_data.target_id,
            machine_id=target.machine_id,
            client_ip=get_client_ip(request),
            server_ip="127.0.0.1",  # Will be updated with actual server IP
            boot_method=session_data.boot_method,
            status=SessionStatus.STARTING,
            created_by=current_user.id
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        # Log activity
        await log_user_activity(
            action=AuditAction.CREATE,
            message=f"Created session: {session.session_id}",
            request=request,
            user=current_user,
            resource_type="sessions"
        )
        
        logger.info("Session created successfully", 
                   session_id=session.session_id, 
                   target_id=session_data.target_id,
                   user_id=current_user.id)
        
        return SessionResponse(
            id=session.id,
            session_id=session.session_id,
            session_type=session.session_type,
            status=session.status,
            machine_id=session.machine_id,
            machine_name=target.machine.name,
            target_id=session.target_id,
            target_name=target.name,
            client_ip=session.client_ip,
            server_ip=session.server_ip,
            boot_method=session.boot_method,
            started_at=session.started_at.isoformat(),
            ended_at=session.ended_at.isoformat() if session.ended_at else None,
            duration_seconds=session.duration_seconds,
            iscsi_info=None
        )
        
    except Exception as e:
        logger.error("Session creation failed", error=str(e), target_id=session_data.target_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session creation failed: {str(e)}"
        )


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    status: Optional[SessionStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all sessions with filtering"""
    
    query = select(Session).join(Target).join(Machine)
    
    if status:
        query = query.where(Session.status == status)
    
    query = query.offset(skip).limit(limit).order_by(Session.started_at.desc())
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    # Log activity
    await log_user_activity(
        action=AuditAction.SESSION_STARTED,  # Using closest available action
        message=f"Listed {len(sessions)} sessions",
        request=request,
        user=current_user,
        resource_type="sessions",
        db=db
    )
    
    return [
        SessionResponse(
            id=session.id,
            session_id=session.session_id,
            session_type=session.session_type,
            status=session.status,
            machine_id=session.machine_id,
            machine_name=session.target.machine.name,
            target_id=session.target_id,
            target_name=session.target.name,
            client_ip=session.client_ip,
            server_ip=session.server_ip,
            boot_method=session.boot_method,
            started_at=session.started_at.isoformat(),
            ended_at=session.ended_at.isoformat() if session.ended_at else None,
            duration_seconds=session.duration_seconds,
            iscsi_info=None
        )
        for session in sessions
    ]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific session"""
    
    result = await db.execute(
        select(Session).join(Target).join(Machine).where(Session.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise NotFoundError("Session not found")
    
    # Build iSCSI info if session is active
    iscsi_info = None
    if session.is_active:
        iscsi_info = {
            "portal": f"{session.target.portal_ip}:{session.target.portal_port}",
            "iqn": session.target.iqn,
            "lun_mapping": session.target.get_lun_mapping()
        }
    
    return SessionResponse(
        id=session.id,
        session_id=session.session_id,
        session_type=session.session_type,
        status=session.status,
        machine_id=session.machine_id,
        machine_name=session.target.machine.name,
        target_id=session.target_id,
        target_name=session.target.name,
        client_ip=session.client_ip,
        server_ip=session.server_ip,
        boot_method=session.boot_method,
        started_at=session.started_at.isoformat(),
        ended_at=session.ended_at.isoformat() if session.ended_at else None,
        duration_seconds=session.duration_seconds,
        iscsi_info=iscsi_info
    )


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    session_data: SessionUpdate,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Update session"""
    
    result = await db.execute(select(Session).where(Session.session_id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise NotFoundError("Session not found")
    
    try:
        # Update session fields
        if session_data.status is not None:
            session.status = session_data.status
            
            # Update timestamps based on status
            if session_data.status == SessionStatus.ACTIVE and not session.started_at:
                session.started_at = datetime.now()
            elif session_data.status in [SessionStatus.STOPPED, SessionStatus.ERROR] and not session.ended_at:
                session.ended_at = datetime.now()
                if session.started_at:
                    session.duration_seconds = int((session.ended_at - session.started_at).total_seconds())
        
        if session_data.client_ip is not None:
            session.client_ip = session_data.client_ip
        
        if session_data.boot_method is not None:
            session.boot_method = session_data.boot_method
        
        await db.commit()
        await db.refresh(session)
        
        # Log activity
        await log_user_activity(
            action=AuditAction.UPDATE,
            message=f"Updated session: {session_id}",
            request=request,
            user=current_user,
            resource_type="sessions"
        )
        
        logger.info("Session updated successfully", 
                   session_id=session_id, 
                   status=session_data.status,
                   user_id=current_user.id)
        
        return SessionResponse(
            id=session.id,
            session_id=session.session_id,
            session_type=session.session_type,
            status=session.status,
            machine_id=session.machine_id,
            machine_name=session.target.machine.name,
            target_id=session.target_id,
            target_name=session.target.name,
            client_ip=session.client_ip,
            server_ip=session.server_ip,
            boot_method=session.boot_method,
            started_at=session.started_at.isoformat(),
            ended_at=session.ended_at.isoformat() if session.ended_at else None,
            duration_seconds=session.duration_seconds,
            iscsi_info=None
        )
        
    except Exception as e:
        logger.error("Session update failed", error=str(e), session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session update failed: {str(e)}"
        )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Delete session"""
    
    result = await db.execute(select(Session).where(Session.session_id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise NotFoundError("Session not found")
    
    # Check if session is active
    if session.status == SessionStatus.ACTIVE:
        raise ValidationError("Cannot delete active session")
    
    try:
        await db.delete(session)
        await db.commit()
        
        # Log activity
        await log_user_activity(
            action=AuditAction.DELETE,
            message=f"Deleted session: {session_id}",
            request=request,
            user=current_user,
            resource_type="sessions"
        )
        
        logger.info("Session deleted successfully", 
                   session_id=session_id,
                   user_id=current_user.id)
        
        return {"message": "Session deleted successfully"}
        
    except Exception as e:
        logger.error("Session deletion failed", error=str(e), session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session deletion failed: {str(e)}"
        )


@router.post("/{session_id}/end")
async def end_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """End an active session"""
    
    result = await db.execute(select(Session).where(Session.session_id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise NotFoundError("Session not found")
    
    if session.status != SessionStatus.ACTIVE:
        raise ValidationError("Session is not active")

    # Update session status
    session.status = SessionStatus.STOPPED
    session.ended_at = datetime.now()
    if session.started_at:
        session.duration_seconds = int((session.ended_at - session.started_at).total_seconds())
    
    await db.commit()
    
    # Log activity
    await log_user_activity(
        action=AuditAction.UPDATE,
        message=f"Ended session: {session_id}",
        request=request,
        user=current_user,
        resource_type="sessions"
    )
    
    logger.info("Session ended successfully", 
               session_id=session_id,
               duration=session.duration_seconds,
               user_id=current_user.id)
    
    return {"message": "Session ended successfully"}


@router.get("/stats/overview", response_model=SessionStats)
async def get_session_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive session statistics"""
    
    # Total sessions
    total_result = await db.execute(select(func.count(Session.id)))
    total_sessions = total_result.scalar()
    
    # Active sessions
    active_result = await db.execute(
        select(func.count(Session.id)).where(Session.status == SessionStatus.ACTIVE)
    )
    active_sessions = active_result.scalar()
    
    # Completed sessions
    completed_result = await db.execute(
        select(func.count(Session.id)).where(Session.status == SessionStatus.STOPPED)
    )
    completed_sessions = completed_result.scalar()
    
    # Failed sessions
    failed_result = await db.execute(
        select(func.count(Session.id)).where(Session.status == SessionStatus.ERROR)
    )
    failed_sessions = failed_result.scalar()
    
    # Total uptime (calculate duration from started_at and ended_at)
    uptime_result = await db.execute(
        select(func.sum(
            func.extract('epoch', Session.ended_at - Session.started_at)
        )).where(
            Session.status == SessionStatus.STOPPED,
            Session.ended_at.isnot(None),
            Session.started_at.isnot(None)
        )
    )
    total_uptime_seconds = uptime_result.scalar() or 0
    total_uptime_hours = total_uptime_seconds / 3600
    
    # Average session duration
    avg_result = await db.execute(
        select(func.avg(
            func.extract('epoch', Session.ended_at - Session.started_at)
        )).where(
            Session.status == SessionStatus.STOPPED,
            Session.ended_at.isnot(None),
            Session.started_at.isnot(None)
        )
    )
    average_duration_seconds = avg_result.scalar() or 0
    average_session_duration = average_duration_seconds / 60  # Convert to minutes
    
    # Sessions today
    today = datetime.now().date()
    today_result = await db.execute(
        select(func.count(Session.id)).where(
            func.date(Session.started_at) == today
        )
    )
    sessions_today = today_result.scalar()
    
    # Sessions this week
    week_start = today - timedelta(days=today.weekday())
    week_result = await db.execute(
        select(func.count(Session.id)).where(
            func.date(Session.started_at) >= week_start
        )
    )
    sessions_this_week = week_result.scalar()
    
    return SessionStats(
        total_sessions=total_sessions,
        active_sessions=active_sessions,
        completed_sessions=completed_sessions,
        failed_sessions=failed_sessions,
        total_uptime_hours=round(total_uptime_hours, 2),
        average_session_duration=round(average_session_duration, 2),
        sessions_today=sessions_today,
        sessions_this_week=sessions_this_week
    )


@router.get("/active", response_model=List[ActiveSessionInfo])
async def get_active_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all currently active sessions with detailed information"""
    
    # Get active sessions with related data
    query = select(Session).join(Machine).join(Target).join(Image).where(
        Session.status == SessionStatus.ACTIVE
    )
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    active_sessions = []
    for session in sessions:
        # Calculate duration
        duration_minutes = int((datetime.now() - session.started_at).total_seconds() / 60)
        
        # Check iSCSI connection status
        iscsi_connected = await check_iscsi_connection(session.client_ip, session.target.iqn)
        
        # Get boot progress (mock for now)
        boot_progress = await get_boot_progress(session.machine.mac_address)
        
        active_sessions.append(ActiveSessionInfo(
            id=session.id,
            session_id=session.session_id,
            machine_name=session.machine.name,
            machine_mac=session.machine.mac_address,
            client_ip=session.client_ip or "Unknown",
            target_name=session.target.name,
            image_name=session.target.image.name,
            started_at=session.started_at,
            duration_minutes=duration_minutes,
            status=session.status,
            iscsi_connection=iscsi_connected,
            boot_progress=boot_progress
        ))
    
    return active_sessions


@router.get("/security/{user_id}", response_model=SessionSecurityInfo)
async def get_user_session_security(
    user_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Get security information for a user's sessions"""
    
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("User not found")
    
    # Get active sessions count
    active_sessions_count = await get_active_sessions(str(user_id))
    
    # Get recent sessions for IP analysis
    recent_result = await db.execute(
        select(Session).where(
            Session.created_by == user_id,
            Session.started_at >= datetime.now() - timedelta(days=7)
        ).order_by(Session.started_at.desc()).limit(50)
    )
    recent_sessions = recent_result.scalars().all()
    
    # Extract unique IPs
    session_ips = list(set([s.client_ip for s in recent_sessions if s.client_ip]))
    
    # Check for suspicious activity (multiple IPs, rapid sessions)
    suspicious_activity = len(session_ips) > 3 or len(recent_sessions) > 20
    
    # Get last login (from most recent session)
    last_login = recent_sessions[0].started_at if recent_sessions else None
    
    return SessionSecurityInfo(
        user_id=user.id,
        username=user.username,
        active_sessions=len(active_sessions_count),
        last_login=last_login,
        session_ips=session_ips,
        suspicious_activity=suspicious_activity
    )


@router.post("/revoke-user-sessions/{user_id}")
async def revoke_user_sessions_endpoint(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Revoke all active sessions for a user"""
    
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("User not found")
    
    try:
        # Revoke sessions in Redis
        revoked_count = await revoke_user_sessions(str(user_id))
        
        # Update database sessions
        db_result = await db.execute(
            select(Session).where(
                Session.created_by == user_id,
                Session.status == SessionStatus.ACTIVE
            )
        )
        active_sessions = db_result.scalars().all()
        
        for session in active_sessions:
            session.status = SessionStatus.ERROR
            session.ended_at = datetime.now()
            if session.started_at:
                session.duration_seconds = int((session.ended_at - session.started_at).total_seconds())
        
        await db.commit()
        
        # Log activity
        await log_user_activity(
            action=AuditAction.UPDATE,
            message=f"Revoked all sessions for user: {user.username}",
            request=request,
            user=current_user,
            resource_type="sessions"
        )
        
        logger.info("User sessions revoked", 
                   user_id=user_id, 
                   username=user.username,
                   revoked_count=len(active_sessions),
                   revoked_by=current_user.id)
        
        return {
            "message": f"Revoked {len(active_sessions)} sessions for user {user.username}",
            "revoked_count": len(active_sessions)
        }
        
    except Exception as e:
        logger.error("Failed to revoke user sessions", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke user sessions: {str(e)}"
        )


async def check_iscsi_connection(client_ip: str, target_iqn: str) -> bool:
    """Check if iSCSI connection is active"""
    try:
        # Use iscsiadm to check connection
        cmd = ["iscsiadm", "-m", "session", "-P", "3"]
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            output = stdout.decode()
            # Check if target IQN is in the active sessions
            return target_iqn in output
        return False
        
    except Exception as e:
        logger.warning("Failed to check iSCSI connection", error=str(e), client_ip=client_ip)
        return False


async def get_boot_progress(mac_address: str) -> Optional[str]:
    """Get boot progress for a machine (mock implementation)"""
    try:
        # In a real implementation, this would check DHCP logs, PXE status, etc.
        # For now, return mock progress based on MAC address
        progress_stages = [
            "DHCP Request",
            "PXE Boot",
            "Loading iPXE",
            "iSCSI Connect",
            "Loading OS",
            "Boot Complete"
        ]
        
        # Simple hash-based progress (for demo purposes)
        hash_val = hash(mac_address) % 100
        if hash_val < 20:
            return progress_stages[0]
        elif hash_val < 40:
            return progress_stages[1]
        elif hash_val < 60:
            return progress_stages[2]
        elif hash_val < 80:
            return progress_stages[3]
        elif hash_val < 95:
            return progress_stages[4]
        else:
            return progress_stages[5]
            
    except Exception as e:
        logger.warning("Failed to get boot progress", error=str(e), mac_address=mac_address)
        return None