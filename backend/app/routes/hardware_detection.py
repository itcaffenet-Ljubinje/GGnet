"""
Hardware auto-detection API endpoints
Detects and stores hardware information from machines
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict
from datetime import datetime
import structlog

from app.core.dependencies import get_db, get_current_user, require_operator
from app.models.user import User
from app.models.machine import Machine
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/hardware", tags=["hardware-detection"])
logger = structlog.get_logger()


class HardwareInfo(BaseModel):
    """Hardware information model"""
    cpu_info: Optional[str] = None
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None
    cpu_frequency_mhz: Optional[float] = None
    memory_mb: Optional[int] = None
    memory_total_gb: Optional[float] = None
    disk_info: Optional[str] = None
    disk_count: Optional[int] = None
    disk_total_gb: Optional[float] = None
    gpu_info: Optional[str] = None
    gpu_count: Optional[int] = None
    motherboard: Optional[str] = None
    bios_version: Optional[str] = None
    network_adapters: Optional[List[Dict[str, Any]]] = None
    usb_devices: Optional[List[Dict[str, Any]]] = None
    pci_devices: Optional[List[Dict[str, Any]]] = None


class HardwareDetectionRequest(BaseModel):
    """Request model for hardware detection"""
    machine_id: Optional[int] = None
    mac_address: Optional[str] = None
    hardware: HardwareInfo
    detected_at: Optional[datetime] = None


class HardwareDetectionResponse(BaseModel):
    """Response model for hardware detection"""
    machine_id: int
    machine_name: str
    hardware: HardwareInfo
    last_detected: datetime
    detection_count: int
    
    model_config = ConfigDict(from_attributes=True)


@router.post("/detect", response_model=HardwareDetectionResponse)
async def detect_hardware(
    detection_data: HardwareDetectionRequest,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """
    Detect and store hardware information for a machine
    
    Can be called by:
    - Machine ID
    - MAC address (if machine_id not provided)
    """
    machine = None
    
    # Find machine by ID or MAC address
    if detection_data.machine_id:
        result = await db.execute(
            select(Machine).where(Machine.id == detection_data.machine_id)
        )
        machine = result.scalar_one_or_none()
        if not machine:
            raise NotFoundError(f"Machine with ID {detection_data.machine_id} not found")
    elif detection_data.mac_address:
        result = await db.execute(
            select(Machine).where(Machine.mac_address == detection_data.mac_address)
        )
        machine = result.scalar_one_or_none()
        if not machine:
            raise NotFoundError(f"Machine with MAC address {detection_data.mac_address} not found")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either machine_id or mac_address must be provided"
        )
    
    # Update machine hardware information
    hw = detection_data.hardware
    
    machine.cpu_info = hw.cpu_info
    machine.memory_mb = hw.memory_mb
    machine.disk_info = hw.disk_info
    machine.gpu_info = hw.gpu_info
    
    # Store additional hardware info in custom_config if needed
    if not machine.custom_config:
        machine.custom_config = {}
    
    machine.custom_config["hardware"] = {
        "cpu_cores": hw.cpu_cores,
        "cpu_threads": hw.cpu_threads,
        "cpu_frequency_mhz": hw.cpu_frequency_mhz,
        "memory_total_gb": hw.memory_total_gb,
        "disk_count": hw.disk_count,
        "disk_total_gb": hw.disk_total_gb,
        "gpu_count": hw.gpu_count,
        "motherboard": hw.motherboard,
        "bios_version": hw.bios_version,
        "network_adapters": hw.network_adapters,
        "usb_devices": hw.usb_devices,
        "pci_devices": hw.pci_devices,
        "last_detected": (detection_data.detected_at or datetime.utcnow()).isoformat()
    }
    
    # Increment detection count
    if "hardware_detection_count" not in machine.custom_config:
        machine.custom_config["hardware_detection_count"] = 0
    machine.custom_config["hardware_detection_count"] += 1
    
    await db.commit()
    await db.refresh(machine)
    
    logger.info(
        "Hardware detected",
        machine_id=machine.id,
        machine_name=machine.name,
        cpu_info=hw.cpu_info,
        memory_mb=hw.memory_mb
    )
    
    detection_count = machine.custom_config.get("hardware_detection_count", 1)
    last_detected = datetime.fromisoformat(
        machine.custom_config.get("hardware", {}).get("last_detected", datetime.utcnow().isoformat())
    )
    
    return HardwareDetectionResponse(
        machine_id=machine.id,
        machine_name=machine.name,
        hardware=hw,
        last_detected=last_detected,
        detection_count=detection_count
    )


@router.get("/machine/{machine_id}", response_model=HardwareDetectionResponse)
async def get_machine_hardware(
    machine_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get hardware information for a machine"""
    result = await db.execute(
        select(Machine).where(Machine.id == machine_id)
    )
    machine = result.scalar_one_or_none()
    
    if not machine:
        raise NotFoundError(f"Machine with ID {machine_id} not found")
    
    hw_data = machine.custom_config.get("hardware", {}) if machine.custom_config else {}
    
    hardware = HardwareInfo(
        cpu_info=machine.cpu_info,
        memory_mb=machine.memory_mb,
        disk_info=machine.disk_info,
        gpu_info=machine.gpu_info,
        cpu_cores=hw_data.get("cpu_cores"),
        cpu_threads=hw_data.get("cpu_threads"),
        cpu_frequency_mhz=hw_data.get("cpu_frequency_mhz"),
        memory_total_gb=hw_data.get("memory_total_gb"),
        disk_count=hw_data.get("disk_count"),
        disk_total_gb=hw_data.get("disk_total_gb"),
        gpu_count=hw_data.get("gpu_count"),
        motherboard=hw_data.get("motherboard"),
        bios_version=hw_data.get("bios_version"),
        network_adapters=hw_data.get("network_adapters"),
        usb_devices=hw_data.get("usb_devices"),
        pci_devices=hw_data.get("pci_devices")
    )
    
    detection_count = machine.custom_config.get("hardware_detection_count", 0) if machine.custom_config else 0
    last_detected_str = hw_data.get("last_detected")
    last_detected = datetime.fromisoformat(last_detected_str) if last_detected_str else datetime.utcnow()
    
    return HardwareDetectionResponse(
        machine_id=machine.id,
        machine_name=machine.name,
        hardware=hardware,
        last_detected=last_detected,
        detection_count=detection_count
    )


@router.get("/match", response_model=List[Dict[str, Any]])
async def match_machines_by_hardware(
    cpu_info: Optional[str] = None,
    memory_mb: Optional[int] = None,
    gpu_info: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Find machines matching hardware criteria
    
    Useful for finding machines with similar hardware for image compatibility
    """
    query = select(Machine)
    conditions = []
    
    if cpu_info:
        conditions.append(Machine.cpu_info.ilike(f"%{cpu_info}%"))
    
    if memory_mb:
        # Match within 10% of specified memory
        min_memory = int(memory_mb * 0.9)
        max_memory = int(memory_mb * 1.1)
        conditions.append(Machine.memory_mb.between(min_memory, max_memory))
    
    if gpu_info:
        conditions.append(Machine.gpu_info.ilike(f"%{gpu_info}%"))
    
    if conditions:
        from sqlalchemy import and_
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    machines = result.scalars().all()
    
    matches = []
    for machine in machines:
        matches.append({
            "machine_id": machine.id,
            "machine_name": machine.name,
            "mac_address": machine.mac_address,
            "cpu_info": machine.cpu_info,
            "memory_mb": machine.memory_mb,
            "gpu_info": machine.gpu_info,
            "status": machine.status.value
        })
    
    return matches

