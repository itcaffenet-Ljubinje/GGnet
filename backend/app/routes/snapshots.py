"""
Snapshot management routes
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import structlog

from app.core.dependencies import get_db, require_operator
from app.models.user import User
from app.models.snapshot import RetentionPolicy
from app.utils.snapshot_manager import SnapshotManager

logger = structlog.get_logger()

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


class SnapshotCreate(BaseModel):
    image_id: int
    machine_id: Optional[int] = None
    description: Optional[str] = None


class SnapshotResponse(BaseModel):
    id: int
    image_id: int
    machine_id: Optional[int]
    snapshot_path: str
    description: Optional[str]
    timestamp: str
    created_at: str


@router.post("", response_model=SnapshotResponse)
async def create_snapshot(
    snapshot_data: SnapshotCreate,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Create a new snapshot"""
    manager = SnapshotManager(db)
    
    try:
        snapshot = await manager.create_snapshot(
            image_id=snapshot_data.image_id,
            machine_id=snapshot_data.machine_id,
            description=snapshot_data.description
        )
        
        return SnapshotResponse(
            id=snapshot.id,
            image_id=snapshot.image_id,
            machine_id=snapshot.machine_id,
            snapshot_path=snapshot.snapshot_path,
            description=snapshot.description,
            timestamp=snapshot.timestamp.isoformat(),
            created_at=snapshot.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to create snapshot", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create snapshot: {str(e)}"
        )


@router.delete("/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Delete a snapshot"""
    manager = SnapshotManager(db)
    
    try:
        await manager.delete_snapshot(snapshot_id)
        return {"message": "Snapshot deleted", "snapshot_id": snapshot_id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to delete snapshot", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete snapshot: {str(e)}"
        )


@router.get("", response_model=List[SnapshotResponse])
async def list_snapshots(
    image_id: Optional[int] = Query(None),
    machine_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """List snapshots with filters"""
    manager = SnapshotManager(db)
    
    snapshots = await manager.list_snapshots(
        image_id=image_id,
        machine_id=machine_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    return [
        SnapshotResponse(
            id=s.id,
            image_id=s.image_id,
            machine_id=s.machine_id,
            snapshot_path=s.snapshot_path,
            description=s.description,
            timestamp=s.timestamp.isoformat(),
            created_at=s.created_at.isoformat()
        )
        for s in snapshots
    ]


@router.get("/stats")
async def get_snapshot_stats(
    image_id: Optional[int] = Query(None),
    machine_id: Optional[int] = Query(None),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Get snapshot statistics"""
    manager = SnapshotManager(db)
    
    stats = await manager.get_snapshot_stats(
        image_id=image_id,
        machine_id=machine_id
    )
    
    return stats


@router.post("/apply-retention")
async def apply_retention_policy(
    image_id: Optional[int] = Query(None),
    machine_id: Optional[int] = Query(None),
    policy: RetentionPolicy = Query(RetentionPolicy.KEEP_LAST_N),
    policy_value: Optional[int] = Query(None),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Apply retention policy to snapshots"""
    manager = SnapshotManager(db)
    
    deleted_count = await manager.apply_retention_policy(
        image_id=image_id,
        machine_id=machine_id,
        policy=policy,
        policy_value=policy_value
    )
    
    return {
        "deleted_count": deleted_count,
        "policy": policy.value,
        "policy_value": policy_value
    }




