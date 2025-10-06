"""
iSCSI target management endpoints
"""

import os
import subprocess
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, ConfigDict
import structlog
import json
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_operator, log_user_activity
from app.models.user import User
from app.models.target import Target, TargetStatus
from app.models.machine import Machine
from app.models.image import Image, ImageStatus
from app.models.audit import AuditAction
from app.core.exceptions import ValidationError, NotFoundError

router = APIRouter()
logger = structlog.get_logger()

# Configuration
ISCSI_BASE_IQN = "iqn.2024.ggnet.local"
TARGET_BASE_DIR = Path("/opt/ggnet/targets")
TARGET_BASE_DIR.mkdir(parents=True, exist_ok=True)


class TargetCreate(BaseModel):
    name: str
    machine_id: int
    image_id: int
    lun: int = 1
    portal: str = "0.0.0.0:3260"
    auth_required: bool = False
    username: Optional[str] = None
    password: Optional[str] = None


class TargetResponse(BaseModel):
    id: int
    name: str
    iqn: str
    machine_id: int
    machine_name: str
    image_id: int
    image_name: str
    lun: int
    portal: str
    status: TargetStatus
    auth_required: bool
    created_at: datetime
    last_accessed: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class TargetStats(BaseModel):
    total_targets: int
    active_targets: int
    inactive_targets: int
    total_luns: int
    connected_sessions: int


@router.post("", response_model=TargetResponse)
async def create_target(
    target_data: TargetCreate,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Create new iSCSI target"""
    
    # Validate machine exists
    machine_result = await db.execute(
        select(Machine).where(Machine.id == target_data.machine_id)
    )
    machine = machine_result.scalar_one_or_none()
    if not machine:
        raise NotFoundError("Machine not found")
    
    # Validate image exists
    image_result = await db.execute(
        select(Image).where(Image.id == target_data.image_id)
    )
    image = image_result.scalar_one_or_none()
    if not image:
        raise NotFoundError("Image not found")
    
    # Check if image is ready
    if image.status != ImageStatus.READY:
        raise ValidationError("Image is not ready for use")
    
    # Generate IQN
    iqn = f"{ISCSI_BASE_IQN}:{target_data.name}"
    
    # Check if IQN already exists
    existing_result = await db.execute(
        select(Target).where(Target.iqn == iqn)
    )
    if existing_result.scalar_one_or_none():
        raise ValidationError(f"Target with IQN {iqn} already exists")
    
    try:
        # Create target directory
        target_dir = TARGET_BASE_DIR / target_data.name
        target_dir.mkdir(exist_ok=True)
        
        # Create target in targetcli
        await create_targetcli_target(iqn, target_data.portal, target_data.lun, image.file_path)
        
        # Create database record
        target = Target(
            name=target_data.name,
            iqn=iqn,
            machine_id=target_data.machine_id,
            image_id=target_data.image_id,
            lun=target_data.lun,
            portal=target_data.portal,
            status=TargetStatus.ACTIVE,
            auth_required=target_data.auth_required,
            username=target_data.username,
            password=target_data.password,
            created_by=current_user.id
        )
        
        db.add(target)
        await db.commit()
        await db.refresh(target)
        
        # Log activity
        await log_user_activity(
            action=AuditAction.CREATE,
            message=f"Created iSCSI target: {target_data.name}",
            request=request,
            user=current_user,
            resource_type="targets"
        )
        
        logger.info("iSCSI target created successfully", 
                   target_id=target.id, 
                   iqn=iqn,
                   machine_id=target_data.machine_id,
                   user_id=current_user.id)
        
        return TargetResponse(
            id=target.id,
            name=target.name,
            iqn=target.iqn,
            machine_id=target.machine_id,
            machine_name=machine.name,
            image_id=target.image_id,
            image_name=image.name,
            lun=target.lun,
            portal=target.portal,
            status=target.status,
            auth_required=target.auth_required,
            created_at=target.created_at,
            last_accessed=target.last_accessed
        )
        
    except Exception as e:
        logger.error("iSCSI target creation failed", error=str(e), iqn=iqn)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Target creation failed: {str(e)}"
        )


async def create_targetcli_target(iqn: str, portal: str, lun: int, image_path: str):
    """Create iSCSI target using targetcli"""
    
    try:
        # Create target
        cmd = ["targetcli", "/iscsi", "create", iqn]
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            raise Exception(f"Failed to create target: {stderr.decode()}")
        
        # Create portal
        cmd = ["targetcli", f"/iscsi/{iqn}/tpg1/portals", "create", portal]
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            raise Exception(f"Failed to create portal: {stderr.decode()}")
        
        # Create LUN
        cmd = ["targetcli", f"/iscsi/{iqn}/tpg1/luns", "create", f"/backstores/fileio/{iqn}_lun{lun}", f"lun={lun}"]
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            raise Exception(f"Failed to create LUN: {stderr.decode()}")
        
        # Create backstore
        cmd = ["targetcli", "/backstores/fileio", "create", f"{iqn}_lun{lun}", image_path]
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            raise Exception(f"Failed to create backstore: {stderr.decode()}")
        
        # Enable target
        cmd = ["targetcli", f"/iscsi/{iqn}/tpg1", "set", "attribute", "generate_node_acls=1", "cache_dynamic_acls=1"]
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            raise Exception(f"Failed to enable target: {stderr.decode()}")
        
        logger.info("targetcli target created successfully", iqn=iqn, portal=portal, lun=lun)
        
    except Exception as e:
        logger.error("targetcli target creation failed", error=str(e), iqn=iqn)
        raise


@router.get("", response_model=List[TargetResponse])
async def list_targets(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    status: Optional[TargetStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all iSCSI targets"""
    
    query = select(Target).join(Machine).join(Image)
    
    if status:
        query = query.where(Target.status == status)
    
    query = query.offset(skip).limit(limit).order_by(Target.created_at.desc())
    
    result = await db.execute(query)
    targets = result.scalars().all()
    
    # Log activity
    await log_user_activity(
        action=AuditAction.TARGET_CREATED,  # Using closest available action
        message=f"Listed {len(targets)} iSCSI targets",
        request=request,
        user=current_user,
        resource_type="targets",
        db=db
    )
    
    return [
        TargetResponse(
            id=target.id,
            name=target.name,
            iqn=target.iqn,
            machine_id=target.machine_id,
            machine_name=target.machine.name,
            image_id=target.image_id,
            image_name=target.image.name,
            lun=target.lun,
            portal=target.portal,
            status=target.status,
            auth_required=target.auth_required,
            created_at=target.created_at,
            last_accessed=target.last_accessed
        )
        for target in targets
    ]


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific iSCSI target"""
    
    result = await db.execute(
        select(Target).join(Machine).join(Image).where(Target.id == target_id)
    )
    target = result.scalar_one_or_none()
    
    if not target:
        raise NotFoundError("Target not found")
    
    return TargetResponse(
        id=target.id,
        name=target.name,
        iqn=target.iqn,
        machine_id=target.machine_id,
        machine_name=target.machine.name,
        image_id=target.image_id,
        image_name=target.image.name,
        lun=target.lun,
        portal=target.portal,
        status=target.status,
        auth_required=target.auth_required,
        created_at=target.created_at,
        last_accessed=target.last_accessed
    )


@router.delete("/{target_id}")
async def delete_target(
    target_id: int,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Delete iSCSI target"""
    
    # Get target
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    
    if not target:
        raise NotFoundError("Target not found")
    
    # Check if target is in use
    from app.models.session import Session, SessionStatus
    result = await db.execute(
        select(Session).where(
            Session.target_id == target_id,
            Session.status.in_([SessionStatus.ACTIVE, SessionStatus.STARTING])
        )
    )
    if result.scalar_one_or_none():
        raise ValidationError("Cannot delete target that is currently in use")
    
    try:
        # Delete target from targetcli
        await delete_targetcli_target(target.iqn)
        
        # Delete database record
        await db.delete(target)
        await db.commit()
        
        # Log activity
        await log_user_activity(
            action=AuditAction.DELETE,
            message=f"Deleted iSCSI target: {target.name}",
            request=request,
            user=current_user,
            resource_type="targets"
        )
        
        logger.info("iSCSI target deleted successfully", 
                   target_id=target_id, 
                   iqn=target.iqn,
                   user_id=current_user.id)
        
        return {"message": "Target deleted successfully"}
        
    except Exception as e:
        logger.error("iSCSI target deletion failed", error=str(e), target_id=target_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Target deletion failed: {str(e)}"
        )


async def delete_targetcli_target(iqn: str):
    """Delete iSCSI target using targetcli"""
    
    try:
        # Delete target
        cmd = ["targetcli", "/iscsi", "delete", iqn]
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            raise Exception(f"Failed to delete target: {stderr.decode()}")
        
        # Delete backstore
        cmd = ["targetcli", "/backstores/fileio", "delete", f"{iqn}_lun1"]
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            # Ignore backstore deletion errors
            logger.warning("Failed to delete backstore", iqn=iqn, error=stderr.decode())
        
        logger.info("targetcli target deleted successfully", iqn=iqn)
        
    except Exception as e:
        logger.error("targetcli target deletion failed", error=str(e), iqn=iqn)
        raise


@router.post("/{target_id}/start")
async def start_target(
    target_id: int,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Start iSCSI target"""
    
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    
    if not target:
        raise NotFoundError("Target not found")
    
    try:
        # Start target using targetcli
        cmd = ["targetcli", f"/iscsi/{target.iqn}/tpg1", "set", "attribute", "enable=1"]
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            raise Exception(f"Failed to start target: {stderr.decode()}")
        
        # Update database
        target.status = TargetStatus.ACTIVE
        await db.commit()
        
        # Log activity
        await log_user_activity(
            action=AuditAction.UPDATE,
            message=f"Started iSCSI target: {target.name}",
            request=request,
            user=current_user,
            resource_type="targets"
        )
        
        return {"message": "Target started successfully"}
        
    except Exception as e:
        logger.error("Failed to start target", error=str(e), target_id=target_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start target: {str(e)}"
        )


@router.post("/{target_id}/stop")
async def stop_target(
    target_id: int,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Stop iSCSI target"""
    
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    
    if not target:
        raise NotFoundError("Target not found")
    
    try:
        # Stop target using targetcli
        cmd = ["targetcli", f"/iscsi/{target.iqn}/tpg1", "set", "attribute", "enable=0"]
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            raise Exception(f"Failed to stop target: {stderr.decode()}")
        
        # Update database
        target.status = TargetStatus.INACTIVE
        await db.commit()
        
        # Log activity
        await log_user_activity(
            action=AuditAction.UPDATE,
            message=f"Stopped iSCSI target: {target.name}",
            request=request,
            user=current_user,
            resource_type="targets"
        )
        
        return {"message": "Target stopped successfully"}
        
    except Exception as e:
        logger.error("Failed to stop target", error=str(e), target_id=target_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop target: {str(e)}"
        )


@router.get("/stats/overview", response_model=TargetStats)
async def get_target_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get iSCSI target statistics"""
    
    # Get target counts
    total_result = await db.execute(select(func.count(Target.id)))
    total_targets = total_result.scalar()
    
    active_result = await db.execute(
        select(func.count(Target.id)).where(Target.status == TargetStatus.ACTIVE)
    )
    active_targets = active_result.scalar()
    
    inactive_result = await db.execute(
        select(func.count(Target.id)).where(Target.status == TargetStatus.INACTIVE)
    )
    inactive_targets = inactive_result.scalar()
    
    # Get total LUNs
    lun_result = await db.execute(select(func.sum(Target.lun)))
    total_luns = lun_result.scalar() or 0
    
    # Get connected sessions
    from app.models.session import Session, SessionStatus
    session_result = await db.execute(
        select(func.count(Session.id)).where(Session.status == SessionStatus.ACTIVE)
    )
    connected_sessions = session_result.scalar()
    
    return TargetStats(
        total_targets=total_targets,
        active_targets=active_targets,
        inactive_targets=inactive_targets,
        total_luns=total_luns,
        connected_sessions=connected_sessions
    )
