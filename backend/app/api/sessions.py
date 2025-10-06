"""
Session Orchestration API endpoints
Provides REST API for session management with network boot orchestration
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

import structlog

from app.core.dependencies import get_db, get_current_user, require_operator, log_user_activity
from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.models.session import Session, SessionStatus, SessionType
from app.models.machine import Machine, MachineStatus
from app.models.target import Target, TargetStatus
from app.models.image import Image, ImageStatus
from app.models.audit import AuditAction, AuditSeverity
from app.adapters.targetcli import create_target_for_machine, delete_target_for_machine
from app.adapters.ipxe import iPXEScriptGenerator, save_boot_script_for_machine
from app.adapters.dhcp import add_machine_to_dhcp, remove_machine_from_dhcp
from app.adapters.tftp import save_boot_script_to_tftp

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["Session Orchestration"])


# Pydantic models for request/response
class SessionStartRequest(BaseModel):
    """Request model for starting a new session"""
    machine_id: int = Field(..., description="Machine ID to start session for")
    image_id: int = Field(..., description="Image ID to use for session")
    session_type: SessionType = Field(SessionType.DISKLESS_BOOT, description="Type of session")
    description: Optional[str] = Field(None, description="Session description")


class SessionResponse(BaseModel):
    """Response model for session information"""
    id: int
    machine_id: int
    target_id: int
    image_id: int
    session_type: SessionType
    status: SessionStatus
    description: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    created_by: int
    
    model_config = ConfigDict(from_attributes=True)


class SessionStartResponse(BaseModel):
    """Response model for session start"""
    session: SessionResponse
    target_info: dict
    boot_script: str
    ipxe_script_url: str
    iscsi_details: dict


class SessionListResponse(BaseModel):
    """Response model for session list"""
    sessions: List[SessionResponse]
    total: int
    page: int
    per_page: int


class BootScriptResponse(BaseModel):
    """Response model for boot script"""
    machine_id: int
    script_content: str
    script_url: str
    iscsi_details: dict


@router.post("/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    request: Request,
    session_data: SessionStartRequest,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new diskless boot session
    
    This endpoint orchestrates the complete session startup process:
    1. Validates machine and image
    2. Creates iSCSI target for the machine
    3. Generates iPXE boot script
    4. Updates DHCP configuration
    5. Creates session record
    6. Returns boot information
    """
    logger.info(
        "Starting diskless boot session",
        machine_id=session_data.machine_id,
        image_id=session_data.image_id,
        user_id=current_user.id
    )
    
    try:
        # 1. Validate machine exists and is active
        machine_result = await db.execute(
            select(Machine).where(Machine.id == session_data.machine_id)
        )
        machine = machine_result.scalar_one_or_none()
        if not machine:
            raise NotFoundError(f"Machine with ID {session_data.machine_id} not found")
        
        if machine.status != MachineStatus.ACTIVE:
            raise ValidationError(f"Machine must be active to start session. Current status: {machine.status}")
        
        # 2. Validate image exists and is ready
        image_result = await db.execute(
            select(Image).where(Image.id == session_data.image_id)
        )
        image = image_result.scalar_one_or_none()
        if not image:
            raise NotFoundError(f"Image with ID {session_data.image_id} not found")
        
        if image.status != ImageStatus.READY:
            raise ValidationError(f"Image must be in READY status. Current status: {image.status}")
        
        # 3. Check if machine already has an active session
        active_session_result = await db.execute(
            select(Session).where(
                Session.machine_id == session_data.machine_id,
                Session.status == SessionStatus.ACTIVE
            )
        )
        if active_session_result.scalar_one_or_none():
            raise ValidationError(f"Machine {session_data.machine_id} already has an active session")
        
        # 4. Create iSCSI target for the machine
        logger.info(f"Creating iSCSI target for machine {machine.id}")
        target_info = await create_target_for_machine(
            machine_id=machine.id,
            machine_mac=machine.mac_address,
            image_path=image.file_path,
            description=f"Session target for {machine.name}"
        )
        
        # 5. Create target record in database
        target = Target(
            target_id=target_info["target_id"],
            iqn=target_info["iqn"],
            machine_id=machine.id,
            image_id=image.id,
            image_path=image.file_path,
            initiator_iqn=target_info["initiator_iqn"],
            lun_id=0,
            status=TargetStatus.ACTIVE,
            description=f"Session target for {machine.name}",
            created_by=current_user.id
        )
        
        db.add(target)
        await db.commit()
        await db.refresh(target)
        
        # 6. Generate iPXE boot script
        logger.info(f"Generating iPXE boot script for machine {machine.id}")
        ipxe_generator = iPXEScriptGenerator()
        boot_script = ipxe_generator.generate_machine_boot_script(machine, target, image)
        
        # 7. Save boot script to TFTP
        script_filename = ipxe_generator.get_machine_script_filename(machine)
        await save_boot_script_to_tftp(boot_script, script_filename)
        
        # 8. Update DHCP configuration
        logger.info(f"Updating DHCP configuration for machine {machine.id}")
        await add_machine_to_dhcp(machine)
        
        # 9. Create session record
        session = Session(
            machine_id=machine.id,
            target_id=target.id,
            image_id=image.id,
            session_type=session_data.session_type,
            status=SessionStatus.ACTIVE,
            description=session_data.description,
            started_at=datetime.utcnow(),
            created_by=current_user.id
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        # 10. Prepare response
        from app.core.config import get_settings
        settings = get_settings()
        
        ipxe_script_url = f"http://{settings.ISCSI_PORTAL_IP}/tftp/{script_filename}"
        
        iscsi_details = {
            "target_iqn": target.iqn,
            "initiator_iqn": target.initiator_iqn,
            "portal_ip": settings.ISCSI_PORTAL_IP,
            "portal_port": settings.ISCSI_PORTAL_PORT,
            "lun_id": target.lun_id
        }
        
        # 11. Log audit event
        await log_user_activity(
            action=AuditAction.SESSION_STARTED,
            message=f"Started diskless boot session for machine {machine.name}",
            request=request,
            user=current_user,
            resource_type="session",
            resource_id=session.id,
            resource_name=f"Session-{session.id}",
            db=db
        )
        
        logger.info(
            "Session started successfully",
            session_id=session.id,
            machine_id=machine.id,
            target_id=target.id
        )
        
        return SessionStartResponse(
            session=SessionResponse.model_validate(session),
            target_info=target_info,
            boot_script=boot_script,
            ipxe_script_url=ipxe_script_url,
            iscsi_details=iscsi_details
        )
        
    except (NotFoundError, ValidationError) as e:
        logger.warning(f"Session start failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during session start: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{session_id}/stop", response_model=dict)
async def stop_session(
    session_id: int,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """
    Stop an active session
    
    This endpoint orchestrates the complete session shutdown process:
    1. Validates session exists and is active
    2. Deletes iSCSI target
    3. Removes DHCP configuration
    4. Cleans up boot scripts
    5. Updates session status
    """
    logger.info("Stopping session", session_id=session_id, user_id=current_user.id)
    
    try:
        # 1. Get session
        session_result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise NotFoundError(f"Session with ID {session_id} not found")
        
        if session.status != SessionStatus.ACTIVE:
            raise ValidationError(f"Session must be active to stop. Current status: {session.status}")
        
        # 2. Get machine and target
        machine_result = await db.execute(
            select(Machine).where(Machine.id == session.machine_id)
        )
        machine = machine_result.scalar_one()
        
        target_result = await db.execute(
            select(Target).where(Target.id == session.target_id)
        )
        target = target_result.scalar_one()
        
        # 3. Delete iSCSI target
        logger.info(f"Deleting iSCSI target for session {session_id}")
        await delete_target_for_machine(machine.id)
        
        # 4. Remove DHCP configuration
        logger.info(f"Removing DHCP configuration for machine {machine.id}")
        await remove_machine_from_dhcp(machine)
        
        # 5. Clean up boot script
        ipxe_generator = iPXEScriptGenerator()
        script_filename = ipxe_generator.get_machine_script_filename(machine)
        from app.adapters.tftp import TFTPAdapter
        tftp_adapter = TFTPAdapter()
        await tftp_adapter.remove_boot_script(script_filename)
        
        # 6. Update session status
        session.status = SessionStatus.STOPPED
        session.ended_at = datetime.utcnow()
        await db.commit()
        
        # 7. Delete target record
        await db.delete(target)
        await db.commit()
        
        # 8. Log audit event
        await log_user_activity(
            action=AuditAction.SESSION_STARTED,  # Using closest available action
            message=f"Stopped session for machine {machine.name}",
            request=request,
            user=current_user,
            resource_type="session",
            resource_id=session_id,
            resource_name=f"Session-{session_id}",
            db=db
        )
        
        logger.info("Session stopped successfully", session_id=session_id)
        
        return {
            "message": "Session stopped successfully",
            "session_id": session_id,
            "machine_id": machine.id
        }
        
    except (NotFoundError, ValidationError) as e:
        logger.warning(f"Session stop failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during session stop: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[SessionStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all sessions with optional filtering
    """
    logger.info("Listing sessions", user_id=current_user.id, status=status)
    
    # Build query
    query = select(Session)
    if status:
        query = query.where(Session.status == status)
    
    # Get total count
    count_query = select(func.count(Session.id))
    if status:
        count_query = count_query.where(Session.status == status)
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    # Get sessions with pagination
    result = await db.execute(
        query
        .offset(skip)
        .limit(limit)
        .order_by(Session.started_at.desc())
    )
    sessions = result.scalars().all()
    
    # Log audit event
    await log_user_activity(
        action=AuditAction.SESSION_STARTED,  # Using closest available action
        message=f"Listed {len(sessions)} sessions",
        request=None,
        user=current_user,
        resource_type="session",
        resource_id=None,
        resource_name="session_list",
        db=db
    )
    
    return SessionListResponse(
        sessions=[SessionResponse.model_validate(session) for session in sessions],
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get specific session by ID
    """
    logger.info("Getting session", session_id=session_id, user_id=current_user.id)
    
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise NotFoundError(f"Session with ID {session_id} not found")
    
    return SessionResponse.model_validate(session)


@router.get("/machine/{machine_id}/boot-script", response_model=BootScriptResponse)
async def get_machine_boot_script(
    machine_id: int,
    mac_address: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get boot script for a machine (used by iPXE chain loading)
    """
    logger.info("Getting boot script for machine", machine_id=machine_id, user_id=current_user.id)
    
    try:
        # Get machine
        machine_result = await db.execute(
            select(Machine).where(Machine.id == machine_id)
        )
        machine = machine_result.scalar_one_or_none()
        if not machine:
            raise NotFoundError(f"Machine with ID {machine_id} not found")
        
        # Get active session for machine
        session_result = await db.execute(
            select(Session).where(
                Session.machine_id == machine_id,
                Session.status == SessionStatus.ACTIVE
            )
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise NotFoundError(f"No active session found for machine {machine_id}")
        
        # Get target and image
        target_result = await db.execute(
            select(Target).where(Target.id == session.target_id)
        )
        target = target_result.scalar_one()
        
        image_result = await db.execute(
            select(Image).where(Image.id == session.image_id)
        )
        image = image_result.scalar_one()
        
        # Generate boot script
        ipxe_generator = iPXEScriptGenerator()
        boot_script = ipxe_generator.generate_machine_boot_script(machine, target, image)
        
        # Prepare response
        from app.core.config import get_settings
        settings = get_settings()
        
        script_filename = ipxe_generator.get_machine_script_filename(machine)
        script_url = f"http://{settings.ISCSI_PORTAL_IP}/tftp/{script_filename}"
        
        iscsi_details = {
            "target_iqn": target.iqn,
            "initiator_iqn": target.initiator_iqn,
            "portal_ip": settings.ISCSI_PORTAL_IP,
            "portal_port": settings.ISCSI_PORTAL_PORT,
            "lun_id": target.lun_id
        }
        
        return BootScriptResponse(
            machine_id=machine_id,
            script_content=boot_script,
            script_url=script_url,
            iscsi_details=iscsi_details
        )
        
    except NotFoundError as e:
        logger.warning(f"Boot script request failed: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during boot script generation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/machine/{machine_id}/active", response_model=SessionResponse)
async def get_active_session_for_machine(
    machine_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get active session for a specific machine
    """
    logger.info("Getting active session for machine", machine_id=machine_id, user_id=current_user.id)
    
    result = await db.execute(
        select(Session).where(
            Session.machine_id == machine_id,
            Session.status == SessionStatus.ACTIVE
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise NotFoundError(f"No active session found for machine {machine_id}")
    
    return SessionResponse.model_validate(session)


@router.get("/stats", response_model=dict)
async def get_session_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get session statistics
    """
    logger.info("Getting session statistics", user_id=current_user.id)
    
    # Get counts by status
    status_counts = {}
    for status in SessionStatus:
        count_result = await db.execute(
            select(func.count(Session.id)).where(Session.status == status)
        )
        status_counts[status.value] = count_result.scalar()
    
    # Get total sessions
    total_result = await db.execute(select(func.count(Session.id)))
    total_sessions = total_result.scalar()
    
    # Get active sessions
    active_result = await db.execute(
        select(func.count(Session.id)).where(Session.status == SessionStatus.ACTIVE)
    )
    active_sessions = active_result.scalar()
    
    return {
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "status_counts": status_counts
    }
