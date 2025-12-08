"""
Writeback management routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from sqlalchemy import select

from app.core.dependencies import get_db, require_operator
from app.models.user import User
from app.models.writeback import Writeback
from app.utils.writeback_manager import WritebackManager

logger = structlog.get_logger()

router = APIRouter(prefix="/writebacks", tags=["writebacks"])


@router.get("")
async def list_writebacks(
    machine_id: Optional[int] = Query(None),
    image_id: Optional[int] = Query(None),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """List all writebacks with optional filtering"""
    manager = WritebackManager(db)
    writebacks = await manager.list_writebacks(machine_id=machine_id, image_id=image_id)
    return {"writebacks": writebacks}


@router.get("/machine/{machine_id}")
async def list_machine_writebacks(
    machine_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """List all writebacks for a machine"""
    manager = WritebackManager(db)
    writebacks = await manager.list_machine_writebacks(machine_id)
    return {"machine_id": machine_id, "writebacks": writebacks}


@router.get("/image/{image_id}")
async def list_image_writebacks(
    image_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """List all writebacks for an image"""
    manager = WritebackManager(db)
    # Note: This would need to be added to WritebackManager
    # For now, we can filter by image_id in the list
    stmt = select(Writeback).where(Writeback.image_id == image_id)
    result = await db.execute(stmt)
    writebacks = result.scalars().all()
    
    writeback_list = []
    for wb in writebacks:
        import os
        file_exists = os.path.exists(wb.path) if wb.path else False
        file_size = os.path.getsize(wb.path) if file_exists and wb.path else wb.size
        
        writeback_list.append({
            'id': wb.id,
            'machine_id': wb.machine_id,
            'image_id': wb.image_id,
            'path': wb.path,
            'size': file_size,
            'file_exists': file_exists,
            'is_permanent': wb.is_permanent,
            'created_at': wb.created_at.isoformat() if wb.created_at else None
        })
    
    return {"image_id": image_id, "writebacks": writeback_list}


@router.post("/{writeback_id}/keep")
async def keep_writeback(
    writeback_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Mark a writeback as permanent (keep it)"""
    manager = WritebackManager(db)
    success, error = await manager.keep_writeback(writeback_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Failed to keep writeback"
        )
    
    return {"message": "Writeback marked as permanent", "writeback_id": writeback_id}


@router.post("/machine/{machine_id}/keep-all")
async def keep_all_machine_writebacks(
    machine_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Keep all writebacks for a machine"""
    manager = WritebackManager(db)
    kept_count, failed_count = await manager.keep_all_writebacks(machine_id)
    
    return {
        "machine_id": machine_id,
        "kept_count": kept_count,
        "failed_count": failed_count
    }


@router.delete("/{writeback_id}")
async def delete_writeback(
    writeback_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Delete a writeback"""
    manager = WritebackManager(db)
    success, error = await manager.delete_writeback(writeback_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Failed to delete writeback"
        )
    
    return {"message": "Writeback deleted", "writeback_id": writeback_id}


@router.delete("/machine/{machine_id}/all")
async def delete_machine_writebacks(
    machine_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Delete all writebacks for a machine"""
    manager = WritebackManager(db)
    deleted_count, failed_count = await manager.delete_machine_writebacks(machine_id)
    
    return {
        "machine_id": machine_id,
        "deleted_count": deleted_count,
        "failed_count": failed_count
    }


@router.delete("/image/{image_id}/all")
async def delete_image_writebacks(
    image_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Delete all writebacks for an image"""
    manager = WritebackManager(db)
    deleted_count, failed_count = await manager.delete_image_writebacks(image_id)
    
    return {
        "image_id": image_id,
        "deleted_count": deleted_count,
        "failed_count": failed_count
    }


@router.get("/{writeback_id}")
async def get_writeback_info(
    writeback_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Get information about a writeback"""
    manager = WritebackManager(db)
    info = await manager.get_writeback_info(writeback_id)
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Writeback not found"
        )
    
    return info

