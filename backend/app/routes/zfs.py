"""
ZFS management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import structlog

from app.core.dependencies import get_current_user, require_operator
from app.models.user import User
from app.utils.zfs_manager import ZFSManager, ZFSPool, ZFSDataset, ZFSSnapshot
from app.utils.arc_monitor import ARCMonitor
from app.utils.iostat_reader import IOStatReader
from app.core.exceptions import StorageError

router = APIRouter()
logger = structlog.get_logger()

# Initialize ZFS manager and monitoring
zfs_manager = ZFSManager()
arc_monitor = ARCMonitor()
iostat_reader = IOStatReader()


# Pydantic models
class ZFSPoolResponse(BaseModel):
    name: str
    size: int
    allocated: int
    free: int
    health: str
    mountpoint: Optional[str] = None
    size_gb: float
    allocated_gb: float
    free_gb: float
    usage_percent: float

    class Config:
        from_attributes = True


class ZFSDatasetResponse(BaseModel):
    name: str
    used: int
    available: int
    referenced: int
    mountpoint: Optional[str] = None
    type: str
    compression: Optional[str] = None
    quota: Optional[int] = None
    reservation: Optional[int] = None
    used_gb: float
    available_gb: float
    usage_percent: float

    class Config:
        from_attributes = True


class ZFSSnapshotResponse(BaseModel):
    name: str
    used: int
    referenced: int
    created: str
    used_gb: float

    class Config:
        from_attributes = True


class CreatePoolRequest(BaseModel):
    pool_name: str
    vdevs: List[str]
    pool_type: str = "stripe"  # stripe, mirror, raidz, raidz2, raidz3
    mountpoint: Optional[str] = None


class CreateDatasetRequest(BaseModel):
    dataset_name: str
    pool_name: str
    properties: Optional[dict] = None


class CreateSnapshotRequest(BaseModel):
    dataset_name: str
    snapshot_name: str


@router.get("/pools", response_model=List[ZFSPoolResponse])
async def list_zfs_pools(
    current_user: User = Depends(get_current_user)
):
    """List all ZFS pools"""
    try:
        pools = zfs_manager.list_pools()
        
        response = []
        for pool in pools:
            total_gb = pool.size / (1024 ** 3)
            allocated_gb = pool.allocated / (1024 ** 3)
            free_gb = pool.free / (1024 ** 3)
            usage_percent = (pool.allocated / pool.size * 100) if pool.size > 0 else 0
            
            response.append(ZFSPoolResponse(
                name=pool.name,
                size=pool.size,
                allocated=pool.allocated,
                free=pool.free,
                health=pool.health,
                mountpoint=pool.mountpoint,
                size_gb=round(total_gb, 2),
                allocated_gb=round(allocated_gb, 2),
                free_gb=round(free_gb, 2),
                usage_percent=round(usage_percent, 2)
            ))
        
        return response
    except Exception as e:
        logger.error("Failed to list ZFS pools", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list ZFS pools: {str(e)}")


@router.get("/pools/{pool_name}", response_model=dict)
async def get_zfs_pool_info(
    pool_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a ZFS pool"""
    try:
        info = zfs_manager.get_pool_info(pool_name)
        if not info:
            raise HTTPException(status_code=404, detail=f"Pool {pool_name} not found")
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get ZFS pool info", pool=pool_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get pool info: {str(e)}")


@router.get("/datasets", response_model=List[ZFSDatasetResponse])
async def list_zfs_datasets(
    pool_name: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List ZFS datasets"""
    try:
        datasets = zfs_manager.list_datasets(pool_name)
        
        response = []
        for dataset in datasets:
            used_gb = dataset.used / (1024 ** 3)
            available_gb = dataset.available / (1024 ** 3)
            total = dataset.used + dataset.available
            usage_percent = (dataset.used / total * 100) if total > 0 else 0
            
            response.append(ZFSDatasetResponse(
                name=dataset.name,
                used=dataset.used,
                available=dataset.available,
                referenced=dataset.referenced,
                mountpoint=dataset.mountpoint,
                type=dataset.type,
                compression=dataset.compression,
                quota=dataset.quota,
                reservation=dataset.reservation,
                used_gb=round(used_gb, 2),
                available_gb=round(available_gb, 2),
                usage_percent=round(usage_percent, 2)
            ))
        
        return response
    except Exception as e:
        logger.error("Failed to list ZFS datasets", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list datasets: {str(e)}")


@router.get("/snapshots", response_model=List[ZFSSnapshotResponse])
async def list_zfs_snapshots(
    dataset_name: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List ZFS snapshots"""
    try:
        snapshots = zfs_manager.list_snapshots(dataset_name)
        
        response = []
        for snapshot in snapshots:
            used_gb = snapshot.used / (1024 ** 3)
            
            response.append(ZFSSnapshotResponse(
                name=snapshot.name,
                used=snapshot.used,
                referenced=snapshot.referenced,
                created=snapshot.created,
                used_gb=round(used_gb, 2)
            ))
        
        return response
    except Exception as e:
        logger.error("Failed to list ZFS snapshots", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list snapshots: {str(e)}")


@router.post("/pools")
async def create_zfs_pool(
    request: CreatePoolRequest,
    current_user: User = Depends(require_operator)
):
    """Create a new ZFS pool"""
    try:
        success = zfs_manager.create_pool(
            pool_name=request.pool_name,
            vdevs=request.vdevs,
            pool_type=request.pool_type,
            mountpoint=request.mountpoint
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create ZFS pool")
        
        return {"message": f"ZFS pool {request.pool_name} created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create ZFS pool", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create pool: {str(e)}")


@router.delete("/pools/{pool_name}")
async def destroy_zfs_pool(
    pool_name: str,
    force: bool = False,
    current_user: User = Depends(require_operator)
):
    """Destroy a ZFS pool"""
    try:
        success = zfs_manager.destroy_pool(pool_name, force=force)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to destroy ZFS pool")
        
        return {"message": f"ZFS pool {pool_name} destroyed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to destroy ZFS pool", pool=pool_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to destroy pool: {str(e)}")


@router.post("/datasets")
async def create_zfs_dataset(
    request: CreateDatasetRequest,
    current_user: User = Depends(require_operator)
):
    """Create a ZFS dataset"""
    try:
        success = zfs_manager.create_dataset(
            dataset_name=request.dataset_name,
            pool_name=request.pool_name,
            properties=request.properties
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create ZFS dataset")
        
        return {"message": f"ZFS dataset {request.pool_name}/{request.dataset_name} created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create ZFS dataset", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create dataset: {str(e)}")


@router.post("/snapshots")
async def create_zfs_snapshot(
    request: CreateSnapshotRequest,
    current_user: User = Depends(require_operator)
):
    """Create a ZFS snapshot"""
    try:
        success = zfs_manager.create_snapshot(
            dataset_name=request.dataset_name,
            snapshot_name=request.snapshot_name
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create ZFS snapshot")
        
        return {"message": f"ZFS snapshot {request.dataset_name}@{request.snapshot_name} created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create ZFS snapshot", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create snapshot: {str(e)}")


@router.get("/arc/stats")
async def get_arc_stats(
    current_user: User = Depends(get_current_user)
):
    """Get ZFS ARC (Adaptive Replacement Cache) statistics"""
    try:
        stats = arc_monitor.get_arc_stats()
        return stats
    except Exception as e:
        logger.error("Failed to get ARC stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get ARC stats: {str(e)}")


@router.get("/pools/{pool_name}/iostat")
async def get_pool_iostat(
    pool_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get IO statistics for a ZFS pool"""
    try:
        iostat = iostat_reader.get_pool_iostat(pool_name)
        return iostat
    except Exception as e:
        logger.error("Failed to get pool iostat", pool=pool_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get pool iostat: {str(e)}")


@router.post("/pools/{pool_name}/scrub")
async def start_pool_scrub(
    pool_name: str,
    current_user: User = Depends(require_operator)
):
    """Start a scrub operation on a ZFS pool"""
    try:
        from app.utils.zfs_enhanced import ZFSUtils
        zfs_utils = ZFSUtils()
        zfs_utils.pool_scrub(pool_name)
        return {"message": f"Scrub started for pool {pool_name}"}
    except Exception as e:
        logger.error("Failed to start pool scrub", pool=pool_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start scrub: {str(e)}")

