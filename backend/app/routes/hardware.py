"""
Hardware detection and reporting endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.core.dependencies import get_db, require_operator
from app.models.user import User
from app.models.machine import Machine, MachineStatus
from app.models.audit import log_user_activity, AuditAction

router = APIRouter(prefix="/api/hardware", tags=["hardware"])


class NetworkCard(BaseModel):
    """Network card information"""
    name: str
    mac: str
    vendor: Optional[str] = None
    speed: Optional[str] = None


class HardwareInfo(BaseModel):
    """Hardware detection information"""
    mac_address: str = Field(..., description="Primary MAC address")
    manufacturer: Optional[str] = Field(None, description="System manufacturer")
    model: Optional[str] = Field(None, description="System model")
    serial_number: Optional[str] = Field(None, description="System serial number")
    bios_version: Optional[str] = Field(None, description="BIOS version")
    cpu_model: str = Field(..., description="CPU model")
    cpu_cores: int = Field(..., description="CPU core count")
    ram_gb: int = Field(..., description="RAM size in GB")
    network_cards: List[NetworkCard] = Field(default_factory=list)
    boot_mode: Optional[str] = Field(None, description="UEFI or BIOS")
    secureboot_enabled: Optional[bool] = Field(None, description="SecureBoot status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mac_address": "00:11:22:33:44:55",
                "manufacturer": "Dell Inc.",
                "model": "OptiPlex 7080",
                "serial_number": "ABC123456",
                "bios_version": "2.15.0",
                "cpu_model": "Intel Core i7-10700",
                "cpu_cores": 8,
                "ram_gb": 16,
                "network_cards": [
                    {
                        "name": "Intel I219-LM",
                        "mac": "00:11:22:33:44:55",
                        "vendor": "Intel Corporation",
                        "speed": "1000 Mbps"
                    }
                ],
                "boot_mode": "UEFI",
                "secureboot_enabled": True
            }
        }


class HardwareReportResponse(BaseModel):
    """Hardware report response"""
    status: str
    machine_id: Optional[int] = None
    message: str
    auto_created: bool = False


@router.post("/report", response_model=HardwareReportResponse)
async def report_hardware(
    hardware: HardwareInfo,
    db: AsyncSession = Depends(get_db)
):
    """
    Report hardware information from client machine.
    
    This endpoint is called during PXE boot to automatically detect
    and register/update machine hardware information.
    
    If machine with MAC address exists, it updates the hardware info.
    If machine doesn't exist, it creates a new one (auto-discovery).
    """
    
    # Find existing machine by MAC
    result = await db.execute(
        select(Machine).where(Machine.mac_address == hardware.mac_address)
    )
    machine = result.scalar_one_or_none()
    
    if machine:
        # Update existing machine
        machine.cpu = hardware.cpu_model
        machine.ram = hardware.ram_gb
        machine.description = f"{hardware.manufacturer or 'Unknown'} {hardware.model or 'Machine'}"
        machine.updated_at = datetime.utcnow()
        
        # Store extended hardware info in notes
        hw_details = f"""
Hardware Info (Auto-detected):
- Manufacturer: {hardware.manufacturer or 'N/A'}
- Model: {hardware.model or 'N/A'}
- Serial: {hardware.serial_number or 'N/A'}
- BIOS: {hardware.bios_version or 'N/A'}
- CPU: {hardware.cpu_model} ({hardware.cpu_cores} cores)
- RAM: {hardware.ram_gb} GB
- Boot Mode: {hardware.boot_mode or 'N/A'}
- SecureBoot: {'Enabled' if hardware.secureboot_enabled else 'Disabled' if hardware.secureboot_enabled is not None else 'N/A'}
- Network Cards: {len(hardware.network_cards)}
"""
        machine.notes = hw_details
        
        await db.commit()
        await db.refresh(machine)
        
        return HardwareReportResponse(
            status="updated",
            machine_id=machine.id,
            message=f"Hardware information updated for machine: {machine.name}",
            auto_created=False
        )
    
    else:
        # Auto-create new machine
        hostname = f"auto-{hardware.serial_number or hardware.mac_address.replace(':', '')[:8]}"
        machine_name = f"{hardware.manufacturer or 'Auto'} {hardware.model or 'Machine'}"
        
        new_machine = Machine(
            name=machine_name,
            mac_address=hardware.mac_address,
            hostname=hostname,
            ip_address=None,  # Will be assigned by DHCP
            cpu=hardware.cpu_model,
            ram=hardware.ram_gb,
            description=f"Auto-detected: {hardware.manufacturer or 'Unknown'} {hardware.model or 'Machine'}",
            status=MachineStatus.INACTIVE,
            notes=f"""
Hardware Info (Auto-detected on {datetime.utcnow().isoformat()}):
- Manufacturer: {hardware.manufacturer or 'N/A'}
- Model: {hardware.model or 'N/A'}
- Serial: {hardware.serial_number or 'N/A'}
- BIOS: {hardware.bios_version or 'N/A'}
- CPU: {hardware.cpu_model} ({hardware.cpu_cores} cores)
- RAM: {hardware.ram_gb} GB
- Boot Mode: {hardware.boot_mode or 'N/A'}
- SecureBoot: {'Enabled' if hardware.secureboot_enabled else 'Disabled' if hardware.secureboot_enabled is not None else 'N/A'}
- Network Cards: {len(hardware.network_cards)}
""",
            wake_on_lan=False,
            boot_order="network,disk"
        )
        
        db.add(new_machine)
        await db.commit()
        await db.refresh(new_machine)
        
        # Log auto-discovery
        await log_user_activity(
            action=AuditAction.CREATE,
            message=f"Machine auto-discovered via hardware detection: {machine_name}",
            resource_type="machines",
            resource_id=new_machine.id,
            db=db
        )
        
        return HardwareReportResponse(
            status="created",
            machine_id=new_machine.id,
            message=f"New machine auto-created: {machine_name}",
            auto_created=True
        )


@router.get("/detect/{machine_id}")
async def get_hardware_info(
    machine_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detected hardware information for a machine.
    """
    result = await db.execute(
        select(Machine).where(Machine.id == machine_id)
    )
    machine = result.scalar_one_or_none()
    
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    # Parse hardware info from notes
    # (In production, you'd store this in a proper JSON field or separate table)
    
    return {
        "machine_id": machine.id,
        "name": machine.name,
        "mac_address": machine.mac_address,
        "cpu": machine.cpu,
        "ram": machine.ram,
        "description": machine.description,
        "notes": machine.notes,
        "last_updated": machine.updated_at
    }


@router.get("/discovered")
async def list_discovered_machines(
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """
    List all auto-discovered machines.
    """
    result = await db.execute(
        select(Machine).where(Machine.notes.contains("Auto-detected"))
    )
    machines = result.scalars().all()
    
    return {
        "count": len(machines),
        "machines": [
            {
                "id": m.id,
                "name": m.name,
                "mac_address": m.mac_address,
                "cpu": m.cpu,
                "ram": m.ram,
                "status": m.status,
                "created_at": m.created_at
            }
            for m in machines
        ]
    }

