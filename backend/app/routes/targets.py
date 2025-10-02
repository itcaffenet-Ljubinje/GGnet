"""
iSCSI Target management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import structlog

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_operator, log_user_activity
from app.models.user import User
from app.models.target import Target, TargetStatus, TargetType
from app.models.machine import Machine
from app.models.image import Image
from app.models.audit import AuditAction
from app.core.exceptions import ValidationError, NotFoundError

router = APIRouter()
logger = structlog.get_logger()


# Pydantic models
class TargetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    iqn: str
    portal_ip: str
    portal_port: int
    target_type: TargetType
    status: TargetStatus
    machine_id: int
    machine_name: str
    system_image_id: int
    system_image_name: str
    extra_disk_image_id: Optional[int]
    extra_disk_image_name: Optional[str]
    extra_disk_mountpoint: Optional[str]
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True


class TargetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    machine_id: int
    system_image_id: int
    extra_disk_image_id: Optional[int] = None
    extra_disk_mountpoint: str = "D:"
    target_type: TargetType = TargetType.SYSTEM


class TargetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    extra_disk_image_id: Optional[int] = None
    extra_disk_mountpoint: Optional[str] = None
    status: Optional[TargetStatus] = None


@router.post("", response_model=TargetResponse)
async def create_target(
    target_data: TargetCreate,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Create a new iSCSI target"""
    
    # Validate machine exists
    machine_result = await db.execute(select(Machine).where(Machine.id == target_data.machine_id))
    machine = machine_result.scalar_one_or_none()
    if not machine:
        raise NotFoundError(f"Machine with ID {target_data.machine_id} not found")
    
    # Validate system image exists
    system_image_result = await db.execute(select(Image).where(Image.id == target_data.system_image_id))
    system_image = system_image_result.scalar_one_or_none()
    if not system_image:
        raise NotFoundError(f"System image with ID {target_data.system_image_id} not found")
    
    # Validate extra disk image if provided
    extra_disk_image = None
    if target_data.extra_disk_image_id:
        extra_disk_result = await db.execute(select(Image).where(Image.id == target_data.extra_disk_image_id))
        extra_disk_image = extra_disk_result.scalar_one_or_none()
        if not extra_disk_image:
            raise NotFoundError(f"Extra disk image with ID {target_data.extra_disk_image_id} not found")
    
    # Generate IQN
    from app.core.config import get_settings
    settings = get_settings()
    iqn = f"{settings.ISCSI_TARGET_PREFIX}:{machine.name.lower().replace(' ', '-')}"
    
    # Create target
    target = Target(
        name=target_data.name,
        description=target_data.description,
        iqn=iqn,
        portal_ip=settings.ISCSI_PORTAL_IP,
        portal_port=settings.ISCSI_PORTAL_PORT,
        target_type=target_data.target_type,
        machine_id=target_data.machine_id,
        system_image_id=target_data.system_image_id,
        extra_disk_image_id=target_data.extra_disk_image_id,
        extra_disk_mountpoint=target_data.extra_disk_mountpoint
    )
    
    db.add(target)
    await db.commit()
    await db.refresh(target)
    
    # Log activity
    await log_user_activity(
        action=AuditAction.TARGET_CREATED,
        message=f"Target '{target.name}' created for machine '{machine.name}'",
        request=request,
        user=current_user,
        resource_type="target",
        resource_id=target.id,
        resource_name=target.name,
        db=db
    )
    
    logger.info(
        "Target created",
        target_id=target.id,
        name=target.name,
        iqn=target.iqn,
        machine_id=machine.id,
        user_id=current_user.id
    )
    
    # Build response
    response = TargetResponse.from_orm(target)
    response.machine_name = machine.name
    response.system_image_name = system_image.name
    response.extra_disk_image_name = extra_disk_image.name if extra_disk_image else None
    
    return response


@router.get("", response_model=List[TargetResponse])
async def list_targets(
    skip: int = 0,
    limit: int = 100,
    machine_id: Optional[int] = None,
    status: Optional[TargetStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all targets"""
    
    # Build query with joins
    query = select(Target).join(Machine).join(Image, Target.system_image_id == Image.id)
    
    # Add filters
    if machine_id:
        query = query.where(Target.machine_id == machine_id)
    if status:
        query = query.where(Target.status == status)
    
    # Add pagination
    query = query.offset(skip).limit(limit).order_by(Target.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    targets = result.scalars().all()
    
    # Build response with related data
    response_targets = []
    for target in targets:
        # Get machine
        machine_result = await db.execute(select(Machine).where(Machine.id == target.machine_id))
        machine = machine_result.scalar_one()
        
        # Get system image
        system_image_result = await db.execute(select(Image).where(Image.id == target.system_image_id))
        system_image = system_image_result.scalar_one()
        
        # Get extra disk image if exists
        extra_disk_image = None
        if target.extra_disk_image_id:
            extra_disk_result = await db.execute(select(Image).where(Image.id == target.extra_disk_image_id))
            extra_disk_image = extra_disk_result.scalar_one_or_none()
        
        response = TargetResponse.from_orm(target)
        response.machine_name = machine.name
        response.system_image_name = system_image.name
        response.extra_disk_image_name = extra_disk_image.name if extra_disk_image else None
        
        response_targets.append(response)
    
    return response_targets


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get target by ID"""
    
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    
    if not target:
        raise NotFoundError(f"Target with ID {target_id} not found")
    
    # Get related data
    machine_result = await db.execute(select(Machine).where(Machine.id == target.machine_id))
    machine = machine_result.scalar_one()
    
    system_image_result = await db.execute(select(Image).where(Image.id == target.system_image_id))
    system_image = system_image_result.scalar_one()
    
    extra_disk_image = None
    if target.extra_disk_image_id:
        extra_disk_result = await db.execute(select(Image).where(Image.id == target.extra_disk_image_id))
        extra_disk_image = extra_disk_result.scalar_one_or_none()
    
    response = TargetResponse.from_orm(target)
    response.machine_name = machine.name
    response.system_image_name = system_image.name
    response.extra_disk_image_name = extra_disk_image.name if extra_disk_image else None
    
    return response


@router.delete("/{target_id}")
async def delete_target(
    target_id: int,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Delete a target"""
    
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    
    if not target:
        raise NotFoundError(f"Target with ID {target_id} not found")
    
    # Check if target has active sessions
    # TODO: Add check for active sessions
    
    # Set status to deleting (will be handled by background task)
    target.status = TargetStatus.DELETING
    
    await db.commit()
    
    # Log activity
    await log_user_activity(
        action=AuditAction.TARGET_DELETED,
        message=f"Target '{target.name}' deleted",
        request=request,
        user=current_user,
        resource_type="target",
        resource_id=target.id,
        resource_name=target.name,
        db=db
    )
    
    logger.info("Target deleted", target_id=target_id, name=target.name, user_id=current_user.id)
    
    return {"message": f"Target '{target.name}' deleted successfully"}

