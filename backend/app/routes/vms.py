"""
VMs API endpoints
Virtual machine management
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator
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
    image_ids: List[int]  # List of image IDs (at least 1 required)
    vcpus: int = 2
    ram_mb: int = 4096
    drives_connection: Optional[str] = "local"  # "local" or "network"
    mac_address: Optional[str] = None
    boot_mode: Optional[str] = "uefi"  # "uefi" or "legacy"
    description: Optional[str] = None
    
    @field_validator('image_ids')
    @classmethod
    def validate_image_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one image ID is required')
        return v


class VMUpdateResourcesRequest(BaseModel):
    """VM resources update request"""
    vcpus: Optional[int] = None
    ram_mb: Optional[int] = None


class VMResponse(BaseModel):
    """VM response model"""
    id: int
    name: str
    vm_id: str
    image_id: Optional[int] = None  # Primary image (for backward compatibility)
    image_ids: List[int] = []  # List of all associated image IDs
    vcpus: int
    ram_mb: int
    status: str
    disk_path: Optional[str] = None
    zfs_clone: Optional[str] = None
    vnc_port: Optional[int] = None
    vnc_token: Optional[str] = None
    description: Optional[str] = None
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


def _domain_state_to_string(state: int) -> str:
    """Convert libvirt domain state to string"""
    state_map = {
        0: "nostate",
        1: "running",
        2: "blocked",
        3: "paused",
        4: "shutdown",
        5: "shutoff",
        6: "crashed",
        7: "pmsuspended"
    }
    return state_map.get(state, "unknown")


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
        
        # Load images relationship for each VM
        vm_list = []
        for vm in vms:
            await db.refresh(vm, ["images"])
            vm_list.append({
                "id": vm.id,
                "name": vm.name,
                "vm_id": vm.vm_id,
                "status": vm.status.value,
                "vcpus": vm.vcpus,
                "ram_mb": vm.ram_mb,
                "image_id": vm.image_id,  # Primary image (backward compatibility)
                "image_ids": [img.id for img in vm.images] if vm.images else [],
                "created_at": vm.created_at.isoformat() if vm.created_at else None,
            })
        
        return vm_list
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
            image_ids=request.image_ids,
            vcpus=request.vcpus,
            ram_mb=request.ram_mb,
            drives_connection=request.drives_connection or "local",
            mac_address=request.mac_address,
            boot_mode=request.boot_mode or "uefi",
            created_by=current_user.id,
            description=request.description
        )
        
        # Refresh to load images relationship
        await db.refresh(vm, ["images"])
        
        return VMResponse(
            id=vm.id,
            name=vm.name,
            vm_id=vm.vm_id,
            image_id=vm.image_id,
            image_ids=[img.id for img in vm.images] if vm.images else [],
            vcpus=vm.vcpus,
            ram_mb=vm.ram_mb,
            status=vm.status.value,
            disk_path=vm.disk_path,
            zfs_clone=vm.zfs_clone,
            vnc_port=vm.vnc_port,
            vnc_token=vm.vnc_token,
            description=vm.description,
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


@router.get("/host", response_model=Dict[str, Any])
async def get_vm_host_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get VM host information using virsh nodeinfo and free -b
    Matches ggRock /api/vms/host endpoint
    """
    try:
        from app.utils.memory_monitor import MemoryMonitor
        
        vm_manager = get_vm_manager()
        memory_monitor = MemoryMonitor()
        
        host_info = {
            "available": False,
            "libvirt_available": vm_manager._is_libvirt_available(),
            "memory": {},
            "nodeinfo": {},
            "vms": []
        }
        
        # Get memory info using free -b
        try:
            memory_info = memory_monitor.get_memory_info()
            host_info["memory"] = memory_info
        except Exception as e:
            logger.warning("Failed to get memory info", error=str(e))
            host_info["memory"] = {"error": str(e), "available": False}
        
        # Get libvirt nodeinfo if available
        if vm_manager._is_libvirt_available():
            try:
                import libvirt
                conn = vm_manager.conn
                if conn:
                    nodeinfo = conn.getInfo()
                    host_info["nodeinfo"] = {
                        "model": nodeinfo[0],  # CPU model
                        "memory_bytes": nodeinfo[1] * 1024 * 1024,  # Convert MB to bytes
                        "cpus": nodeinfo[2],  # Number of CPUs
                        "mhz": nodeinfo[3],  # CPU frequency in MHz
                        "nodes": nodeinfo[4],  # Number of NUMA nodes
                        "sockets": nodeinfo[5],  # Number of CPU sockets
                        "cores": nodeinfo[6],  # Number of CPU cores per socket
                        "threads": nodeinfo[7],  # Number of CPU threads per core
                        "available": True
                    }
                    
                    # Get list of VMs
                    try:
                        # Get all domains (running, paused, other states)
                        domains = conn.listAllDomains(
                            libvirt.VIR_CONNECT_LIST_DOMAINS_RUNNING |
                            libvirt.VIR_CONNECT_LIST_DOMAINS_PAUSED |
                            libvirt.VIR_CONNECT_LIST_DOMAINS_OTHER
                        )
                        
                        vms_list = []
                        for domain in domains:
                            try:
                                state, _ = domain.state()
                                vms_list.append({
                                    "uuid": domain.UUIDString(),
                                    "name": domain.name(),
                                    "state": state,
                                    "state_str": _domain_state_to_string(state)
                                })
                            except Exception as e:
                                logger.warning("Failed to get domain info", error=str(e))
                                continue
                        
                        host_info["vms"] = vms_list
                    except Exception as e:
                        logger.warning("Failed to list domains", error=str(e))
                        host_info["vms"] = []
                    
                    host_info["available"] = True
            except Exception as e:
                logger.warning("Failed to get libvirt nodeinfo", error=str(e))
                host_info["nodeinfo"] = {"error": str(e), "available": False}
        else:
            host_info["nodeinfo"] = {"available": False, "error": "libvirt not available"}
        
        return host_info
    except Exception as e:
        logger.error("Failed to get VM host info", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get VM host info: {str(e)}"
        )


def _domain_state_to_string(state: int) -> str:
    """Convert libvirt domain state to string"""
    state_map = {
        0: "nostate",
        1: "running",
        2: "blocked",
        3: "paused",
        4: "shutdown",
        5: "shutoff",
        6: "crashed",
        7: "pmsuspended"
    }
    return state_map.get(state, "unknown")

