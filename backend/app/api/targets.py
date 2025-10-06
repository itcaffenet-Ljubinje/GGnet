"""
iSCSI Target Management API endpoints
Provides REST API for creating, managing, and monitoring iSCSI targets
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

import structlog

from app.core.dependencies import get_db, get_current_user, require_operator, log_user_activity
from app.core.exceptions import NotFoundError, ValidationError, TargetCLIError
from app.models.user import User
from app.models.target import Target, TargetStatus
from app.models.audit import AuditAction, AuditSeverity
from app.adapters.targetcli import TargetCLIAdapter, create_target_for_machine, delete_target_for_machine

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["iSCSI Targets"])


# Pydantic models for request/response
class TargetCreateRequest(BaseModel):
    """Request model for creating a new iSCSI target"""
    machine_id: int = Field(..., description="Machine ID to associate with this target")
    image_id: int = Field(..., description="Image ID to use for this target")
    description: Optional[str] = Field(None, description="Target description")
    lun_id: int = Field(0, description="LUN ID (default: 0)")


class TargetResponse(BaseModel):
    """Response model for iSCSI target information"""
    id: int
    target_id: str
    iqn: str
    machine_id: int
    image_id: int
    image_path: str
    initiator_iqn: str
    lun_id: int
    status: TargetStatus
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: int
    
    model_config = ConfigDict(from_attributes=True)


class TargetStatusResponse(BaseModel):
    """Response model for target status information"""
    target_id: str
    iqn: str
    status: str
    luns: List[str]
    acls: List[str]
    portals: List[str]
    error: Optional[str] = None


class TargetListResponse(BaseModel):
    """Response model for target list"""
    targets: List[TargetResponse]
    total: int
    page: int
    per_page: int


@router.post("/", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    request: Request,
    target_data: TargetCreateRequest,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new iSCSI target for a machine
    
    This endpoint creates a complete iSCSI target including:
    - Fileio backstore from the specified image
    - iSCSI target with unique IQN
    - LUN mapping
    - ACL for the machine's initiator
    - Portal configuration
    """
    logger.info(
        "Creating iSCSI target",
        machine_id=target_data.machine_id,
        image_id=target_data.image_id,
        user_id=current_user.id
    )
    
    try:
        # Verify machine exists
        from app.models.machine import Machine
        machine_result = await db.execute(
            select(Machine).where(Machine.id == target_data.machine_id)
        )
        machine = machine_result.scalar_one_or_none()
        if not machine:
            raise NotFoundError(f"Machine with ID {target_data.machine_id} not found")
        
        # Verify image exists and is ready
        from app.models.image import Image, ImageStatus
        image_result = await db.execute(
            select(Image).where(Image.id == target_data.image_id)
        )
        image = image_result.scalar_one_or_none()
        if not image:
            raise NotFoundError(f"Image with ID {target_data.image_id} not found")
        
        if image.status != ImageStatus.READY:
            raise ValidationError(f"Image must be in READY status. Current status: {image.status}")
        
        # Check if target already exists for this machine
        existing_target = await db.execute(
            select(Target).where(Target.machine_id == target_data.machine_id)
        )
        if existing_target.scalar_one_or_none():
            raise ValidationError(f"Target already exists for machine {target_data.machine_id}")
        
        # Create iSCSI target using targetcli adapter
        target_adapter = TargetCLIAdapter()
        
        target_info = await create_target_for_machine(
            machine_id=target_data.machine_id,
            machine_mac=machine.mac_address,
            image_path=image.file_path,
            description=target_data.description
        )
        
        # Create database record
        target = Target(
            target_id=target_info["target_id"],
            iqn=target_info["iqn"],
            machine_id=target_data.machine_id,
            image_id=target_data.image_id,
            image_path=image.file_path,
            initiator_iqn=target_info["initiator_iqn"],
            lun_id=target_data.lun_id,
            status=TargetStatus.ACTIVE,
            description=target_data.description,
            created_by=current_user.id
        )
        
        db.add(target)
        await db.commit()
        await db.refresh(target)
        
        # Log audit event
        await log_user_activity(
            action=AuditAction.TARGET_CREATED,
            message=f"iSCSI target '{target.target_id}' created for machine {target_data.machine_id}",
            request=request,
            user=current_user,
            resource_type="target",
            resource_id=target.id,
            resource_name=target.target_id,
            db=db
        )
        
        logger.info(
            "iSCSI target created successfully",
            target_id=target.target_id,
            iqn=target.iqn,
            machine_id=target_data.machine_id
        )
        
        return TargetResponse.model_validate(target)
        
    except (NotFoundError, ValidationError) as e:
        logger.warning(f"Target creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except TargetCLIError as e:
        logger.error(f"targetcli error during target creation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Target creation failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during target creation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/", response_model=TargetListResponse)
async def list_targets(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all iSCSI targets with pagination
    """
    logger.info("Listing iSCSI targets", user_id=current_user.id)
    
    # Get total count
    count_result = await db.execute(select(func.count(Target.id)))
    total = count_result.scalar()
    
    # Get targets with pagination
    result = await db.execute(
        select(Target)
        .offset(skip)
        .limit(limit)
        .order_by(Target.created_at.desc())
    )
    targets = result.scalars().all()
    
    # Log audit event
    await log_user_activity(
        action=AuditAction.TARGET_CREATED,  # Using closest available action
        message=f"Listed {len(targets)} iSCSI targets",
        request=None,
        user=current_user,
        resource_type="target",
        resource_id=None,
        resource_name="target_list",
        db=db
    )
    
    return TargetListResponse(
        targets=[TargetResponse.model_validate(target) for target in targets],
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get specific iSCSI target by ID
    """
    logger.info("Getting iSCSI target", target_id=target_id, user_id=current_user.id)
    
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    
    if not target:
        raise NotFoundError(f"Target with ID {target_id} not found")
    
    return TargetResponse.model_validate(target)


@router.get("/{target_id}/status", response_model=TargetStatusResponse)
async def get_target_status(
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get real-time status of an iSCSI target from targetcli
    """
    logger.info("Getting target status", target_id=target_id, user_id=current_user.id)
    
    # Get target from database
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    
    if not target:
        raise NotFoundError(f"Target with ID {target_id} not found")
    
    try:
        # Get status from targetcli
        target_adapter = TargetCLIAdapter()
        status_info = await target_adapter.get_target_status(target.target_id)
        
        return TargetStatusResponse(
            target_id=status_info["target_id"],
            iqn=status_info["iqn"],
            status=status_info["status"],
            luns=status_info.get("luns", []),
            acls=status_info.get("acls", []),
            portals=status_info.get("portals", []),
            error=status_info.get("error")
        )
        
    except Exception as e:
        logger.error(f"Failed to get target status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get target status: {e}"
        )


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: int,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an iSCSI target and its associated resources
    """
    logger.info("Deleting iSCSI target", target_id=target_id, user_id=current_user.id)
    
    # Get target from database
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    
    if not target:
        raise NotFoundError(f"Target with ID {target_id} not found")
    
    try:
        # Delete target using targetcli adapter
        target_adapter = TargetCLIAdapter()
        success = await target_adapter.delete_target(target.target_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete target from targetcli"
            )
        
        # Delete from database
        await db.delete(target)
        await db.commit()
        
        # Log audit event
        await log_user_activity(
            action=AuditAction.TARGET_CREATED,  # Using closest available action
            message=f"iSCSI target '{target.target_id}' deleted",
            request=request,
            user=current_user,
            resource_type="target",
            resource_id=target_id,
            resource_name=target.target_id,
            db=db
        )
        
        logger.info("iSCSI target deleted successfully", target_id=target_id)
        
    except TargetCLIError as e:
        logger.error(f"targetcli error during target deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Target deletion failed: {e}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during target deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/machine/{machine_id}", response_model=TargetResponse)
async def get_target_by_machine(
    machine_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get iSCSI target associated with a specific machine
    """
    logger.info("Getting target by machine", machine_id=machine_id, user_id=current_user.id)
    
    result = await db.execute(
        select(Target).where(Target.machine_id == machine_id)
    )
    target = result.scalar_one_or_none()
    
    if not target:
        raise NotFoundError(f"No target found for machine {machine_id}")
    
    return TargetResponse.model_validate(target)


@router.post("/{target_id}/restart", response_model=dict)
async def restart_target(
    target_id: int,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """
    Restart an iSCSI target (delete and recreate)
    """
    logger.info("Restarting iSCSI target", target_id=target_id, user_id=current_user.id)
    
    # Get target from database
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    
    if not target:
        raise NotFoundError(f"Target with ID {target_id} not found")
    
    try:
        # Delete existing target
        target_adapter = TargetCLIAdapter()
        await target_adapter.delete_target(target.target_id)
        
        # Recreate target
        target_info = await create_target_for_machine(
            machine_id=target.machine_id,
            machine_mac=target.initiator_iqn.split('-')[-1],  # Extract MAC from initiator IQN
            image_path=target.image_path,
            description=target.description
        )
        
        # Update database record
        target.iqn = target_info["iqn"]
        target.initiator_iqn = target_info["initiator_iqn"]
        target.status = TargetStatus.ACTIVE
        target.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # Log audit event
        await log_user_activity(
            action=AuditAction.TARGET_CREATED,  # Using closest available action
            message=f"iSCSI target '{target.target_id}' restarted",
            request=request,
            user=current_user,
            resource_type="target",
            resource_id=target_id,
            resource_name=target.target_id,
            db=db
        )
        
        logger.info("iSCSI target restarted successfully", target_id=target_id)
        
        return {
            "message": "Target restarted successfully",
            "target_id": target.target_id,
            "iqn": target.iqn
        }
        
    except Exception as e:
        logger.error(f"Failed to restart target: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart target: {e}"
        )
