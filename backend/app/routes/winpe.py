"""
WinPE deployment endpoints for fresh Windows installation.

NOTE: This is a STUB implementation. Full WinPE deployment requires:
1. Windows ADK installed on build machine
2. Custom WinPE image created
3. Driver packs prepared
4. wimboot loader configured

See: scripts/winpe/README.md for complete implementation guide
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.core.dependencies import get_db, require_operator
from app.models.user import User
from app.models.machine import Machine

router = APIRouter(prefix="/winpe", tags=["winpe"])

# WinPE files directory
WINPE_DIR = Path("/opt/ggnet/winpe")


class DiskPartition(BaseModel):
    """Disk partition configuration"""
    type: str  # efi, msr, primary
    size: str  # 500MB, 128MB, remaining
    label: Optional[str] = None


class DiskConfig(BaseModel):
    """Disk configuration for partitioning"""
    disk: int  # Disk number (0, 1, etc.)
    partitions: List[DiskPartition]


class DeploymentInfo(BaseModel):
    """Deployment configuration for WinPE client"""
    image_url: str
    disk_config: DiskConfig
    drivers_url: Optional[str] = None
    hostname: str
    timezone: str = "UTC"
    locale: str = "en-US"


@router.get("/wimboot")
async def get_wimboot():
    """
    Download wimboot loader for WinPE boot.
    
    TODO: Download wimboot from https://git.ipxe.org/releases/wimboot/wimboot-latest.zip
    Extract wimboot file and serve it here.
    """
    wimboot_path = WINPE_DIR / "wimboot"
    
    if not wimboot_path.exists():
        raise HTTPException(
            status_code=404,
            detail="wimboot not found. Please download from https://git.ipxe.org/releases/wimboot/"
        )
    
    return FileResponse(wimboot_path, media_type="application/octet-stream")


@router.get("/boot.wim")
async def get_boot_wim():
    """
    Download WinPE boot.wim image.
    
    TODO: Create custom WinPE image using Windows ADK.
    See scripts/winpe/README.md for build instructions.
    """
    boot_wim_path = WINPE_DIR / "boot.wim"
    
    if not boot_wim_path.exists():
        raise HTTPException(
            status_code=404,
            detail="boot.wim not found. Please create WinPE image using Windows ADK."
        )
    
    return FileResponse(boot_wim_path, media_type="application/octet-stream")


@router.get("/deployment-info", response_model=DeploymentInfo)
async def get_deployment_info(
    mac: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get deployment configuration for WinPE client.
    
    Called by WinPE during boot to get:
    - Windows image URL
    - Disk partitioning config
    - Driver pack URL
    - Machine hostname/settings
    
    TODO: Implement deployment configuration in Machine model.
    Add deployment_config JSON field or separate DeploymentConfig table.
    """
    
    # Find machine by MAC
    result = await db.execute(
        select(Machine).where(Machine.mac_address == mac)
    )
    machine = result.scalar_one_or_none()
    
    if not machine:
        raise HTTPException(
            status_code=404,
            detail=f"Machine not found with MAC: {mac}. Please register machine first."
        )
    
    # TODO: Get deployment config from machine.deployment_config
    # For now, return stub configuration
    
    return DeploymentInfo(
        image_url=f"http://192.168.1.10:8000/api/images/1/download",  # TODO: Dynamic
        disk_config=DiskConfig(
            disk=0,
            partitions=[
                DiskPartition(type="efi", size="500MB"),
                DiskPartition(type="msr", size="128MB"),
                DiskPartition(type="primary", size="remaining", label="Windows")
            ]
        ),
        drivers_url=None,  # TODO: Implement driver packs
        hostname=machine.hostname or f"ggnet-{machine.id}",
        timezone="UTC",
        locale="en-US"
    )


@router.post("/deployment/start")
async def start_deployment(
    machine_id: int,
    image_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """
    Configure machine for WinPE deployment.
    
    This sets up deployment configuration so WinPE knows what to install.
    
    TODO: Implement deployment configuration storage.
    """
    
    # Get machine
    result = await db.execute(
        select(Machine).where(Machine.id == machine_id)
    )
    machine = result.scalar_one_or_none()
    
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    # TODO: Store deployment config in machine.deployment_config
    # For now, return success stub
    
    return {
        "status": "configured",
        "machine_id": machine_id,
        "image_id": image_id,
        "message": "Machine configured for WinPE deployment. Boot client to start installation.",
        "next_steps": [
            "1. Boot client machine",
            "2. Select 'Deploy Fresh Windows (WinPE)' from menu",
            "3. WinPE will download and install Windows automatically"
        ]
    }


@router.get("/status/{machine_id}")
async def get_deployment_status(
    machine_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """
    Get WinPE deployment status for a machine.
    
    TODO: Track deployment progress (downloading, partitioning, installing, configuring, done).
    """
    
    return {
        "machine_id": machine_id,
        "status": "not_started",
        "message": "WinPE deployment tracking not yet implemented"
    }

