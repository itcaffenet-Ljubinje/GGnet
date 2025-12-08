"""
VMs API endpoints
Virtual machine management
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import structlog

from app.core.dependencies import get_db, require_operator, get_current_user
from app.models.user import User
from app.models.vm import VM, VMStatus
from app.utils.vm_manager import VMManager, VMError

router = APIRouter(prefix="/vms", tags=["vms"])
logger = structlog.get_logger()


class VMCreateRequest(BaseModel):
    """VM creation request"""
    name: str
    image_id: int
    vcpus: int = 2
    ram_mb: int = 4096
    drives_connection: Optional[str] = "local"  # "local" or "network"
    mac_address: Optional[str] = None
    boot_mode: Optional[str] = "uefi"  # "uefi" or "legacy"
    description: Optional[str] = None


class VMUpdateResourcesRequest(BaseModel):
    """VM resources update request"""
    vcpus: Optional[int] = None
    ram_mb: Optional[int] = None


class VMResponse(BaseModel):
    """VM response model"""
    id: int
    name: str
    vm_id: str
    image_id: Optional[int] = None
    vcpus: int
    ram_mb: int
    status: str
    disk_path: Optional[str] = None
    zfs_clone: Optional[str] = None
    vnc_port: Optional[int] = None
    vnc_token: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


def get_vm_manager() -> VMManager:
    """Get VM manager instance"""
    try:
        return VMManager()
    except Exception as e:
        logger.warning("VM manager initialization failed", error=str(e))
        # Return manager anyway (it will handle libvirt unavailability gracefully)
        return VMManager()


@router.get("", response_model=List[Dict[str, Any]])
async def list_vms(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[VMStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List all VMs"""
    try:
        from sqlalchemy import select
        
        stmt = select(VM)
        
        if status_filter:
            stmt = stmt.where(VM.status == status_filter)
        
        stmt = stmt.order_by(VM.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        vms = result.scalars().all()
        
        return [
            {
                "id": vm.id,
                "name": vm.name,
                "vm_id": vm.vm_id,
                "status": vm.status.value,
                "vcpus": vm.vcpus,
                "ram_mb": vm.ram_mb,
                "image_id": vm.image_id,
                "created_at": vm.created_at.isoformat() if vm.created_at else None,
            }
            for vm in vms
        ]
    except Exception as e:
        logger.error("Failed to list VMs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list VMs: {str(e)}"
        )


@router.get("/{vm_id}", response_model=Dict[str, Any])
async def get_vm(
    vm_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get VM by ID with detailed information"""
    try:
        vm_manager = get_vm_manager()
        return await vm_manager.get_vm_info(db, vm_id)
    except VMError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Failed to get VM", vm_id=vm_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get VM: {str(e)}"
        )


@router.post("", response_model=VMResponse, status_code=status.HTTP_201_CREATED)
async def create_vm(
    request: VMCreateRequest,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
) -> VMResponse:
    """Create new virtual machine"""
    try:
        vm_manager = get_vm_manager()
        vm = await vm_manager.create_vm(
            db=db,
            name=request.name,
            image_id=request.image_id,
            vcpus=request.vcpus,
            ram_mb=request.ram_mb,
            drives_connection=request.drives_connection or "local",
            mac_address=request.mac_address,
            boot_mode=request.boot_mode or "uefi",
            created_by=current_user.id
        )
        
        return VMResponse(
            id=vm.id,
            name=vm.name,
            vm_id=vm.vm_id,
            image_id=vm.image_id,
            vcpus=vm.vcpus,
            ram_mb=vm.ram_mb,
            status=vm.status.value,
            disk_path=vm.disk_path,
            zfs_clone=vm.zfs_clone,
            vnc_port=vm.vnc_port,
            vnc_token=vm.vnc_token,
            created_at=vm.created_at.isoformat(),
            updated_at=vm.updated_at.isoformat()
        )
    except VMError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Failed to create VM", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create VM: {str(e)}"
        )


@router.delete("/{vm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vm(
    vm_id: int,
    force: bool = Query(False, description="Force deletion even if VM is running"),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Delete VM (with cleanup of clone and libvirt domain)"""
    try:
        vm_manager = get_vm_manager()
        await vm_manager.delete_vm(db, vm_id, force=force)
    except VMError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Failed to delete VM", vm_id=vm_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete VM: {str(e)}"
        )


@router.post("/{vm_id}/start", response_model=Dict[str, Any])
async def start_vm(
    vm_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Start VM"""
    try:
        vm_manager = get_vm_manager()
        vm = await vm_manager.start_vm(db, vm_id)
        return {
            "id": vm.id,
            "name": vm.name,
            "status": vm.status.value,
            "message": f"VM {vm.name} started successfully",
        }
    except VMError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Failed to start VM", vm_id=vm_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start VM: {str(e)}"
        )


@router.post("/{vm_id}/stop", response_model=Dict[str, Any])
async def stop_vm(
    vm_id: int,
    force: bool = Query(False, description="Force stop (destroy instead of shutdown)"),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Stop VM"""
    try:
        vm_manager = get_vm_manager()
        vm = await vm_manager.stop_vm(db, vm_id, force=force)
        return {
            "id": vm.id,
            "name": vm.name,
            "status": vm.status.value,
            "message": f"VM {vm.name} stopped successfully",
        }
    except VMError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Failed to stop VM", vm_id=vm_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop VM: {str(e)}"
        )


@router.get("/{vm_id}/vnc", response_model=Dict[str, Any])
async def get_vm_vnc(
    vm_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get VNC URL and connection details for VM"""
    try:
        from sqlalchemy import select
        
        stmt = select(VM).where(VM.id == vm_id)
        result = await db.execute(stmt)
        vm = result.scalar_one_or_none()
        
        if not vm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found")
        
        if not vm.vnc_token or not vm.vnc_port:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="VNC is not available for this VM"
            )
        
        return {
            "vnc_url": f"/vnc/console?token={vm.vnc_token}",
            "vnc_token": vm.vnc_token,
            "vnc_port": vm.vnc_port,
            "vnc_host": "127.0.0.1",
            "websocket_url": f"ws://127.0.0.1:6080/websockify?token={vm.vnc_token}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get VNC info", vm_id=vm_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get VNC info: {str(e)}"
        )




