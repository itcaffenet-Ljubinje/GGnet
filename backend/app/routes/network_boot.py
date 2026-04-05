"""
Network Boot Management API Routes
Handles boot events, network services, and boot statistics
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, ConfigDict
import structlog

from app.core.dependencies import get_db, require_operator, get_current_user
from app.models.user import User
from app.models.boot_event import BootEvent, BootEventType, BootEventStatus
from app.models.machine import Machine
from app.models.session import Session
from app.adapters.dhcp import DHCPAdapter
from app.adapters.tftp import TFTPAdapter
from app.adapters.ipxe import iPXEScriptGenerator

logger = structlog.get_logger()

# Router for monitoring endpoints
monitoring_router = APIRouter(prefix="/monitoring", tags=["network-boot-monitoring"])

# Router for network boot management endpoints
network_boot_router = APIRouter(prefix="/network-boot", tags=["network-boot"])


# Pydantic models
class BootEventResponse(BaseModel):
    id: int
    machine_id: Optional[int]
    session_id: Optional[int]
    event_type: str
    status: str
    message: str
    details: Optional[dict]
    client_ip: Optional[str]
    server_ip: Optional[str]
    mac_address: Optional[str]
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BootEventCreate(BaseModel):
    machine_id: Optional[int] = None
    session_id: Optional[int] = None
    event_type: BootEventType
    status: BootEventStatus
    message: str
    details: Optional[dict] = None
    client_ip: Optional[str] = None
    server_ip: Optional[str] = None
    mac_address: Optional[str] = None


class NetworkServiceStatus(BaseModel):
    service: str  # "dhcp" or "tftp"
    status: str  # "running", "stopped", "error"
    message: Optional[str] = None
    last_check: datetime


class NetworkServicesResponse(BaseModel):
    dhcp: NetworkServiceStatus
    tftp: NetworkServiceStatus


class BootStatistics(BaseModel):
    total_boots: int
    successful_boots: int
    failed_boots: int
    timeout_boots: int
    success_rate: float
    average_boot_time_seconds: Optional[float]
    last_24h_boots: int
    last_7d_boots: int
    last_30d_boots: int


class MachineBootStatus(BaseModel):
    machine_id: int
    machine_name: str
    last_boot_event: Optional[BootEventResponse]
    last_boot_time: Optional[datetime]
    boot_status: str  # "never_booted", "booting", "booted", "failed"
    boot_count: int
    last_successful_boot: Optional[datetime]


# Boot Events Routes
@monitoring_router.post("/boot-events", response_model=BootEventResponse, status_code=status.HTTP_201_CREATED)
async def create_boot_event(
    event: BootEventCreate,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Create a new boot event"""
    try:
        boot_event = BootEvent(
            machine_id=event.machine_id,
            session_id=event.session_id,
            event_type=event.event_type,
            status=event.status,
            message=event.message,
            details=event.details,
            client_ip=event.client_ip,
            server_ip=event.server_ip,
            mac_address=event.mac_address
        )
        
        db.add(boot_event)
        await db.commit()
        await db.refresh(boot_event)
        
        logger.info(
            "Boot event created",
            event_id=boot_event.id,
            event_type=event.event_type.value,
            machine_id=event.machine_id
        )
        
        return BootEventResponse.model_validate(boot_event)
        
    except Exception as e:
        await db.rollback()
        logger.error("Failed to create boot event", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create boot event: {str(e)}"
        )


@monitoring_router.get("/boot-events", response_model=List[BootEventResponse])
async def list_boot_events(
    machine_id: Optional[int] = Query(None),
    session_id: Optional[int] = Query(None),
    event_type: Optional[BootEventType] = Query(None),
    status_filter: Optional[BootEventStatus] = Query(None, alias="status"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List boot events with filters"""
    try:
        stmt = select(BootEvent)
        
        # Apply filters
        conditions = []
        if machine_id:
            conditions.append(BootEvent.machine_id == machine_id)
        if session_id:
            conditions.append(BootEvent.session_id == session_id)
        if event_type:
            conditions.append(BootEvent.event_type == event_type)
        if status_filter:
            conditions.append(BootEvent.status == status_filter)
        if start_date:
            conditions.append(BootEvent.timestamp >= start_date)
        if end_date:
            conditions.append(BootEvent.timestamp <= end_date)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Order by timestamp descending
        stmt = stmt.order_by(desc(BootEvent.timestamp))
        
        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        events = result.scalars().all()
        
        return [BootEventResponse.model_validate(event) for event in events]
        
    except Exception as e:
        logger.error("Failed to list boot events", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list boot events: {str(e)}"
        )


@monitoring_router.get("/boot-statistics", response_model=BootStatistics)
async def get_boot_statistics(
    machine_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get boot statistics"""
    try:
        # Base query
        stmt = select(BootEvent).where(
            BootEvent.event_type.in_([
                BootEventType.BOOT_SUCCESS,
                BootEventType.BOOT_FAILED,
                BootEventType.BOOT_TIMEOUT
            ])
        )
        
        # Apply filters
        conditions = []
        if machine_id:
            conditions.append(BootEvent.machine_id == machine_id)
        if start_date:
            conditions.append(BootEvent.timestamp >= start_date)
        if end_date:
            conditions.append(BootEvent.timestamp <= end_date)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        result = await db.execute(stmt)
        events = result.scalars().all()
        
        # Calculate statistics
        total_boots = len(events)
        successful_boots = sum(1 for e in events if e.event_type == BootEventType.BOOT_SUCCESS)
        failed_boots = sum(1 for e in events if e.event_type == BootEventType.BOOT_FAILED)
        timeout_boots = sum(1 for e in events if e.event_type == BootEventType.BOOT_TIMEOUT)
        
        success_rate = (successful_boots / total_boots * 100) if total_boots > 0 else 0.0
        
        # Calculate time ranges
        now = datetime.utcnow()
        last_24h = now - timedelta(days=1)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        last_24h_boots = sum(1 for e in events if e.timestamp >= last_24h)
        last_7d_boots = sum(1 for e in events if e.timestamp >= last_7d)
        last_30d_boots = sum(1 for e in events if e.timestamp >= last_30d)
        
        # Calculate average boot time (if available in details)
        boot_times = []
        for event in events:
            if event.details and "boot_time_seconds" in event.details:
                boot_times.append(event.details["boot_time_seconds"])
        
        avg_boot_time = sum(boot_times) / len(boot_times) if boot_times else None
        
        return BootStatistics(
            total_boots=total_boots,
            successful_boots=successful_boots,
            failed_boots=failed_boots,
            timeout_boots=timeout_boots,
            success_rate=round(success_rate, 2),
            average_boot_time_seconds=round(avg_boot_time, 2) if avg_boot_time else None,
            last_24h_boots=last_24h_boots,
            last_7d_boots=last_7d_boots,
            last_30d_boots=last_30d_boots
        )
        
    except Exception as e:
        logger.error("Failed to get boot statistics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get boot statistics: {str(e)}"
        )


@monitoring_router.get("/machine-boot-status/{machine_id}", response_model=MachineBootStatus)
async def get_machine_boot_status(
    machine_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get boot status for a specific machine"""
    try:
        # Get machine
        machine_result = await db.execute(select(Machine).where(Machine.id == machine_id))
        machine = machine_result.scalar_one_or_none()
        
        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Machine with ID {machine_id} not found"
            )
        
        # Get last boot event
        last_event_stmt = select(BootEvent).where(
            BootEvent.machine_id == machine_id
        ).order_by(desc(BootEvent.timestamp)).limit(1)
        
        last_event_result = await db.execute(last_event_stmt)
        last_event = last_event_result.scalar_one_or_none()
        
        # Count boot events
        count_stmt = select(func.count(BootEvent.id)).where(
            BootEvent.machine_id == machine_id,
            BootEvent.event_type.in_([
                BootEventType.BOOT_SUCCESS,
                BootEventType.BOOT_FAILED,
                BootEventType.BOOT_TIMEOUT
            ])
        )
        boot_count_result = await db.execute(count_stmt)
        boot_count = boot_count_result.scalar_one() or 0
        
        # Get last successful boot
        success_stmt = select(BootEvent).where(
            BootEvent.machine_id == machine_id,
            BootEvent.event_type == BootEventType.BOOT_SUCCESS
        ).order_by(desc(BootEvent.timestamp)).limit(1)
        
        success_result = await db.execute(success_stmt)
        last_success = success_result.scalar_one_or_none()
        
        # Determine boot status
        if not last_event:
            boot_status = "never_booted"
        elif last_event.event_type == BootEventType.BOOT_SUCCESS:
            boot_status = "booted"
        elif last_event.event_type in [BootEventType.BOOT_FAILED, BootEventType.BOOT_TIMEOUT]:
            boot_status = "failed"
        elif last_event.status == BootEventStatus.IN_PROGRESS:
            boot_status = "booting"
        else:
            boot_status = "unknown"
        
        return MachineBootStatus(
            machine_id=machine.id,
            machine_name=machine.name,
            last_boot_event=BootEventResponse.model_validate(last_event) if last_event else None,
            last_boot_time=last_event.timestamp if last_event else None,
            boot_status=boot_status,
            boot_count=boot_count,
            last_successful_boot=last_success.timestamp if last_success else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get machine boot status", machine_id=machine_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get machine boot status: {str(e)}"
        )


@monitoring_router.get("/network-services", response_model=NetworkServicesResponse)
async def get_network_services_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get DHCP and TFTP service status"""
    try:
        dhcp_adapter = DHCPAdapter()
        tftp_adapter = TFTPAdapter()
        
        # Check DHCP status
        try:
            dhcp_status = await dhcp_adapter.get_dhcp_status()
            dhcp_running = dhcp_status.get("service_running", False)
            dhcp_message = "DHCP service is running" if dhcp_running else "DHCP service is not running"
            if not dhcp_status.get("config_file_exists", False):
                dhcp_message += " (config file missing)"
        except Exception as e:
            logger.warning("Failed to get DHCP status", error=str(e))
            dhcp_running = False
            dhcp_message = f"Error checking status: {str(e)}"
        
        # Check TFTP status
        try:
            tftp_status = await tftp_adapter.get_tftp_status()
            tftp_running = tftp_status.get("service_running", False)
            tftp_message = "TFTP service is running" if tftp_running else "TFTP service is not running"
            if not tftp_status.get("tftp_root_exists", False):
                tftp_message += " (TFTP root missing)"
        except Exception as e:
            logger.warning("Failed to get TFTP status", error=str(e))
            tftp_running = False
            tftp_message = f"Error checking status: {str(e)}"
        
        return NetworkServicesResponse(
            dhcp=NetworkServiceStatus(
                service="dhcp",
                status="running" if dhcp_running else "stopped",
                message=dhcp_message,
                last_check=datetime.utcnow()
            ),
            tftp=NetworkServiceStatus(
                service="tftp",
                status="running" if tftp_running else "stopped",
                message=tftp_message,
                last_check=datetime.utcnow()
            )
        )
        
    except Exception as e:
        logger.error("Failed to get network services status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get network services status: {str(e)}"
        )


# DHCP/TFTP Management Routes
@network_boot_router.get("/dhcp/status")
async def get_dhcp_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed DHCP server status"""
    try:
        dhcp_adapter = DHCPAdapter()
        status = await dhcp_adapter.get_dhcp_status()
        return status
    except Exception as e:
        logger.error("Failed to get DHCP status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get DHCP status: {str(e)}"
        )


@network_boot_router.get("/tftp/status")
async def get_tftp_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed TFTP server status"""
    try:
        tftp_adapter = TFTPAdapter()
        status = await tftp_adapter.get_tftp_status()
        return status
    except Exception as e:
        logger.error("Failed to get TFTP status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get TFTP status: {str(e)}"
        )


@network_boot_router.post("/dhcp/reload")
async def reload_dhcp(
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Reload DHCP server configuration"""
    try:
        dhcp_adapter = DHCPAdapter()
        success = await dhcp_adapter.reload_dhcp_server()
        
        if success:
            return {"message": "DHCP server reloaded successfully", "status": "success"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reload DHCP server"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to reload DHCP server", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload DHCP server: {str(e)}"
        )


# iPXE Script Generation Routes
@network_boot_router.get("/ipxe/{machine_id}")
async def get_machine_ipxe_script(
    machine_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get iPXE boot script for a machine"""
    try:
        # Get machine
        machine_result = await db.execute(select(Machine).where(Machine.id == machine_id))
        machine = machine_result.scalar_one_or_none()
        
        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Machine with ID {machine_id} not found"
            )
        
        # Get active target for machine
        from app.models.target import Target, TargetStatus
        target_result = await db.execute(
            select(Target).where(
                Target.machine_id == machine_id,
                Target.status == TargetStatus.ACTIVE
            ).limit(1)
        )
        target = target_result.scalar_one_or_none()
        
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active target found for machine {machine_id}"
            )
        
        # Get image
        from app.models.image import Image
        image_result = await db.execute(select(Image).where(Image.id == target.system_image_id))
        image = image_result.scalar_one_or_none()
        
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image not found for target {target.id}"
            )
        
        # Generate script
        script_generator = iPXEScriptGenerator()
        script = script_generator.generate_machine_boot_script(machine, target, image)
        
        return {
            "machine_id": machine_id,
            "machine_name": machine.name,
            "target_id": target.id,
            "image_id": image.id,
            "script": script
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate iPXE script", machine_id=machine_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate iPXE script: {str(e)}"
        )


@network_boot_router.post("/ipxe/generate")
async def generate_ipxe_script(
    machine_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Generate and save iPXE boot script for a machine"""
    try:
        # Get machine
        machine_result = await db.execute(select(Machine).where(Machine.id == machine_id))
        machine = machine_result.scalar_one_or_none()
        
        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Machine with ID {machine_id} not found"
            )
        
        # Get active target for machine
        from app.models.target import Target, TargetStatus
        target_result = await db.execute(
            select(Target).where(
                Target.machine_id == machine_id,
                Target.status == TargetStatus.ACTIVE
            ).limit(1)
        )
        target = target_result.scalar_one_or_none()
        
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active target found for machine {machine_id}"
            )
        
        # Get image
        from app.models.image import Image
        image_result = await db.execute(select(Image).where(Image.id == target.system_image_id))
        image = image_result.scalar_one_or_none()
        
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image not found for target {target.id}"
            )
        
        # Generate and save script
        script_generator = iPXEScriptGenerator()
        script = script_generator.generate_machine_boot_script(machine, target, image)
        
        # Save script via TFTP adapter
        tftp_adapter = TFTPAdapter()
        script_path = await tftp_adapter.save_boot_script(script, machine)
        
        logger.info(
            "iPXE script generated and saved",
            machine_id=machine_id,
            script_path=script_path
        )
        
        return {
            "message": "iPXE script generated and saved successfully",
            "machine_id": machine_id,
            "machine_name": machine.name,
            "target_id": target.id,
            "image_id": image.id,
            "script_path": script_path,
            "script": script
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate and save iPXE script", machine_id=machine_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate iPXE script: {str(e)}"
        )

