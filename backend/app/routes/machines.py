"""
Machine management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from pydantic import BaseModel, field_validator, ConfigDict
import structlog
from datetime import datetime
from app.core.validators import NetworkValidators, StringValidators
from app.core.serializers import ModelSerializer, DateTimeSerializer

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_operator, log_user_activity
from app.models.user import User
from app.models.machine import Machine, MachineStatus, BootMode
from app.models.target import Target
from app.models.session import Session, SessionStatus
from app.models.audit import AuditAction
from app.core.exceptions import ValidationError, NotFoundError, ConflictError

router = APIRouter()
logger = structlog.get_logger()


# Pydantic models
class MachineResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    mac_address: str
    ip_address: Optional[str]
    hostname: Optional[str]
    boot_mode: BootMode
    secure_boot_enabled: bool
    status: MachineStatus
    is_online: bool
    location: Optional[str]
    room: Optional[str]
    asset_tag: Optional[str]
    created_at: datetime
    last_seen: Optional[datetime]
    last_boot: Optional[datetime]
    boot_count: int
    
    model_config = ConfigDict(from_attributes=True)


class MachineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    mac_address: str
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    boot_mode: BootMode = BootMode.UEFI
    secure_boot_enabled: bool = True
    location: Optional[str] = None
    room: Optional[str] = None
    asset_tag: Optional[str] = None
    
    @field_validator('mac_address')
    @classmethod
    def validate_mac_address(cls, v):
        if not v:
            raise ValueError('MAC address cannot be empty')
            
        # Remove common separators and convert to standard format
        import re
        mac = re.sub(r'[:-]', '', v.upper())
        
        # Validate MAC address format
        if not re.match(r'^[0-9A-F]{12}$', mac):
            raise ValueError('Invalid MAC address format. Expected 12 hexadecimal characters')
        
        # Convert to standard format with colons
        return ':'.join(mac[i:i+2] for i in range(0, 12, 2))
    
    @field_validator('ip_address')
    @classmethod
    def validate_ip_address(cls, v):
        if v is None:
            return v
            
        try:
            # Use ipaddress module for proper validation
            import ipaddress
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('Invalid IP address format')
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        
        if len(v.strip()) > 100:
            raise ValueError('Name cannot exceed 100 characters')
        
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is None:
            return v
        
        if len(v) > 500:
            raise ValueError('Description cannot exceed 500 characters')
        
        return v.strip() if v.strip() else None


class MachineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    boot_mode: Optional[BootMode] = None
    secure_boot_enabled: Optional[bool] = None
    status: Optional[MachineStatus] = None
    location: Optional[str] = None
    room: Optional[str] = None
    asset_tag: Optional[str] = None
    
    @field_validator('ip_address')
    @classmethod
    def validate_ip_address(cls, v):
        if v is None:
            return v
            
        try:
            # Use ipaddress module for proper validation
            import ipaddress
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('Invalid IP address format')


@router.post("", response_model=MachineResponse, status_code=201)
async def create_machine(
    machine_data: MachineCreate,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Create a new machine"""
    
    # Check if MAC address already exists
    result = await db.execute(
        select(Machine).where(Machine.mac_address == machine_data.mac_address)
    )
    if result.scalar_one_or_none():
        raise ConflictError(f"Machine with MAC address '{machine_data.mac_address}' already exists")
    
    # Check if name already exists
    result = await db.execute(
        select(Machine).where(Machine.name == machine_data.name)
    )
    if result.scalar_one_or_none():
        raise ConflictError(f"Machine with name '{machine_data.name}' already exists")
    
    # Create machine
    machine = Machine(
        name=machine_data.name,
        description=machine_data.description,
        mac_address=machine_data.mac_address,
        ip_address=machine_data.ip_address,
        hostname=machine_data.hostname,
        boot_mode=machine_data.boot_mode,
        secure_boot_enabled=machine_data.secure_boot_enabled,
        location=machine_data.location,
        room=machine_data.room,
        asset_tag=machine_data.asset_tag,
        created_by=current_user.id
    )
    
    db.add(machine)
    await db.commit()
    await db.refresh(machine)
    
    # Log activity
    await log_user_activity(
        action=AuditAction.MACHINE_CREATED,
        message=f"Machine '{machine.name}' created",
        request=request,
        user=current_user,
        resource_type="machine",
        resource_id=machine.id,
        resource_name=machine.name,
        db=db
    )
    
    logger.info(
        "Machine created",
        machine_id=machine.id,
        name=machine.name,
        mac_address=machine.mac_address,
        user_id=current_user.id
    )
    
    return ModelSerializer.serialize_model(machine, MachineResponse)


@router.get("", response_model=List[MachineResponse])
async def list_machines(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status: Optional[MachineStatus] = None,
    location: Optional[str] = None,
    room: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all machines with filtering and search"""
    
    # Build query
    query = select(Machine)
    
    # Add filters
    filters = []
    if status:
        filters.append(Machine.status == status)
    if location:
        filters.append(Machine.location == location)
    if room:
        filters.append(Machine.room == room)
    
    # Add search functionality
    if search:
        search_filters = [
            Machine.name.ilike(f"%{search}%"),
            Machine.mac_address.ilike(f"%{search}%"),
            Machine.hostname.ilike(f"%{search}%"),
            Machine.location.ilike(f"%{search}%"),
            Machine.asset_tag.ilike(f"%{search}%")
        ]
        filters.append(and_(*search_filters))
    
    if filters:
        query = query.where(and_(*filters))
    
    # Add pagination
    query = query.offset(skip).limit(limit).order_by(Machine.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    machines = result.scalars().all()
    
    # Log activity
    await log_user_activity(
        action=AuditAction.MACHINE_UPDATED,  # Using closest available action
        message=f"Listed {len(machines)} machines",
        request=request,
        user=current_user,
        resource_type="machines",
        db=db
    )
    
    return ModelSerializer.serialize_model_list(machines, MachineResponse)


@router.get("/{machine_id}", response_model=MachineResponse)
async def get_machine(
    machine_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get machine by ID"""
    
    result = await db.execute(select(Machine).where(Machine.id == machine_id))
    machine = result.scalar_one_or_none()
    
    if not machine:
        raise NotFoundError(f"Machine with ID {machine_id} not found")
    
    return ModelSerializer.serialize_model(machine, MachineResponse)


@router.put("/{machine_id}", response_model=MachineResponse)
async def update_machine(
    machine_id: int,
    machine_update: MachineUpdate,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Update machine"""
    
    result = await db.execute(select(Machine).where(Machine.id == machine_id))
    machine = result.scalar_one_or_none()
    
    if not machine:
        raise NotFoundError(f"Machine with ID {machine_id} not found")
    
    # Store old values for audit
    old_values = {
        "name": machine.name,
        "description": machine.description,
        "ip_address": machine.ip_address,
        "hostname": machine.hostname,
        "boot_mode": machine.boot_mode,
        "secure_boot_enabled": machine.secure_boot_enabled,
        "status": machine.status,
        "location": machine.location,
        "room": machine.room,
        "asset_tag": machine.asset_tag
    }
    
    # Update fields
    if machine_update.name is not None:
        # Check if new name already exists
        result = await db.execute(
            select(Machine).where(and_(Machine.name == machine_update.name, Machine.id != machine_id))
        )
        if result.scalar_one_or_none():
            raise ConflictError(f"Machine with name '{machine_update.name}' already exists")
        machine.name = machine_update.name
    
    if machine_update.description is not None:
        machine.description = machine_update.description
    
    if machine_update.ip_address is not None:
        machine.ip_address = machine_update.ip_address
    
    if machine_update.hostname is not None:
        machine.hostname = machine_update.hostname
    
    if machine_update.boot_mode is not None:
        machine.boot_mode = machine_update.boot_mode
    
    if machine_update.secure_boot_enabled is not None:
        machine.secure_boot_enabled = machine_update.secure_boot_enabled
    
    if machine_update.status is not None:
        machine.status = machine_update.status
    
    if machine_update.location is not None:
        machine.location = machine_update.location
    
    if machine_update.room is not None:
        machine.room = machine_update.room
    
    if machine_update.asset_tag is not None:
        machine.asset_tag = machine_update.asset_tag
    
    await db.commit()
    await db.refresh(machine)
    
    # Log activity
    new_values = {
        "name": machine.name,
        "description": machine.description,
        "ip_address": machine.ip_address,
        "hostname": machine.hostname,
        "boot_mode": machine.boot_mode,
        "secure_boot_enabled": machine.secure_boot_enabled,
        "status": machine.status,
        "location": machine.location,
        "room": machine.room,
        "asset_tag": machine.asset_tag
    }
    
    await log_user_activity(
        action=AuditAction.MACHINE_UPDATED,
        message=f"Machine '{machine.name}' updated",
        request=request,
        user=current_user,
        resource_type="machine",
        resource_id=machine.id,
        resource_name=machine.name,
        db=db
    )
    
    logger.info("Machine updated", machine_id=machine_id, user_id=current_user.id)
    
    return machine


@router.delete("/{machine_id}")
async def delete_machine(
    machine_id: int,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Delete a machine"""
    
    result = await db.execute(select(Machine).where(Machine.id == machine_id))
    machine = result.scalar_one_or_none()
    
    if not machine:
        raise NotFoundError(f"Machine with ID {machine_id} not found")
    
    # Check if machine has active sessions or targets
    # Check for active sessions and targets
    active_sessions_result = await db.execute(
        select(Session).where(
            Session.machine_id == machine_id,
            Session.status.in_([SessionStatus.STARTING, SessionStatus.ACTIVE])
        )
    )
    active_sessions = active_sessions_result.scalars().all()
    
    if active_sessions:
        session_ids = [session.session_id for session in active_sessions]
        raise ValidationError(
            f"Cannot delete machine '{machine.name}' - it has active sessions: {', '.join(session_ids)}"
        )
    
    # Check for targets associated with this machine
    targets_result = await db.execute(
        select(Target).where(Target.machine_id == machine_id)
    )
    targets = targets_result.scalars().all()
    
    if targets:
        target_names = [target.name for target in targets]
        raise ValidationError(
            f"Cannot delete machine '{machine.name}' - it has associated targets: {', '.join(target_names)}"
        )
    
    # Soft delete - set status to retired
    machine.status = MachineStatus.RETIRED
    
    await db.commit()
    
    # Log activity
    await log_user_activity(
        action=AuditAction.MACHINE_DELETED,
        message=f"Machine '{machine.name}' deleted",
        request=request,
        user=current_user,
        resource_type="machine",
        resource_id=machine.id,
        resource_name=machine.name,
        db=db
    )
    
    logger.info("Machine deleted", machine_id=machine_id, name=machine.name, user_id=current_user.id)
    
    return {"message": f"Machine '{machine.name}' deleted successfully"}

