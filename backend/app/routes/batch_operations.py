"""
Batch Operations API Routes
Bulk operations on images and machines
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import structlog

from app.core.dependencies import get_db, require_operator
from app.models.user import User
from app.models.batch_operation import BatchOperationType, BatchOperationStatus
from app.utils.batch_image_operations import BatchImageOperationsManager
from app.utils.batch_machine_operations import BatchMachineOperationsManager

router = APIRouter(prefix="/batch", tags=["batch-operations"])
logger = structlog.get_logger()


class BatchImageBackupRequest(BaseModel):
    image_ids: List[int]
    backup_path: str
    is_remote: bool = False
    remote_host: Optional[str] = None
    remote_path: Optional[str] = None


class BatchImageRestoreRequest(BaseModel):
    image_ids: List[int]
    backup_path: str
    is_remote: bool = False


class BatchImageTestRequest(BaseModel):
    image_ids: List[int]
    backup_path: str


class BatchMachineOperationRequest(BaseModel):
    machine_ids: List[int]
    operation_type: BatchOperationType


class BatchOperationResponse(BaseModel):
    id: int
    operation_type: str
    status: str
    total_items: int
    completed_items: int
    failed_items: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.post("/images/backup", response_model=BatchOperationResponse)
async def batch_backup_images(
    request: BatchImageBackupRequest,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Execute batch backup operation on images"""
    try:
        manager = BatchImageOperationsManager(db)
        
        if request.is_remote:
            if not request.remote_host or not request.remote_path:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="remote_host and remote_path required for remote backup"
                )
            batch_op = await manager.execute_batch_backup_remote(
                image_ids=request.image_ids,
                remote_host=request.remote_host,
                remote_path=request.remote_path,
                created_by=current_user.id
            )
        else:
            batch_op = await manager.execute_batch_backup_local(
                image_ids=request.image_ids,
                backup_path=request.backup_path,
                created_by=current_user.id
            )
        
        return BatchOperationResponse(
            id=batch_op.id,
            operation_type=batch_op.operation_type.value,
            status=batch_op.status.value,
            total_items=batch_op.total_items,
            completed_items=batch_op.completed_items,
            failed_items=batch_op.failed_items,
            created_at=batch_op.created_at.isoformat(),
            started_at=batch_op.started_at.isoformat() if batch_op.started_at else None,
            completed_at=batch_op.completed_at.isoformat() if batch_op.completed_at else None,
            error_message=batch_op.error_message
        )
    except Exception as e:
        logger.error("Failed to start batch image backup", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start batch backup: {str(e)}"
        )


@router.post("/images/restore", response_model=BatchOperationResponse)
async def batch_restore_images(
    request: BatchImageRestoreRequest,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Execute batch restore operation on images"""
    try:
        manager = BatchImageOperationsManager(db)
        batch_op = await manager.execute_batch_restore_local(
            image_ids=request.image_ids,
            backup_path=request.backup_path,
            created_by=current_user.id
        )
        
        return BatchOperationResponse(
            id=batch_op.id,
            operation_type=batch_op.operation_type.value,
            status=batch_op.status.value,
            total_items=batch_op.total_items,
            completed_items=batch_op.completed_items,
            failed_items=batch_op.failed_items,
            created_at=batch_op.created_at.isoformat(),
            started_at=batch_op.started_at.isoformat() if batch_op.started_at else None,
            completed_at=batch_op.completed_at.isoformat() if batch_op.completed_at else None,
            error_message=batch_op.error_message
        )
    except Exception as e:
        logger.error("Failed to start batch image restore", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start batch restore: {str(e)}"
        )


@router.post("/images/test", response_model=BatchOperationResponse)
async def batch_test_images(
    request: BatchImageTestRequest,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Execute batch test operation on images (verify backup integrity)"""
    try:
        manager = BatchImageOperationsManager(db)
        batch_op = await manager.execute_batch_test_local(
            image_ids=request.image_ids,
            backup_path=request.backup_path,
            created_by=current_user.id
        )
        
        return BatchOperationResponse(
            id=batch_op.id,
            operation_type=batch_op.operation_type.value,
            status=batch_op.status.value,
            total_items=batch_op.total_items,
            completed_items=batch_op.completed_items,
            failed_items=batch_op.failed_items,
            created_at=batch_op.created_at.isoformat(),
            started_at=batch_op.started_at.isoformat() if batch_op.started_at else None,
            completed_at=batch_op.completed_at.isoformat() if batch_op.completed_at else None,
            error_message=batch_op.error_message
        )
    except Exception as e:
        logger.error("Failed to start batch image test", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start batch test: {str(e)}"
        )


@router.post("/machines", response_model=BatchOperationResponse)
async def batch_operate_machines(
    request_data: BatchMachineOperationRequest,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Execute batch operation on machines"""
    try:
        # Validate operation type
        valid_machine_ops = [
            BatchOperationType.MACHINE_RESTART,
            BatchOperationType.MACHINE_SHUTDOWN,
            BatchOperationType.MACHINE_WAKE,
            BatchOperationType.MACHINE_TURN_ON
        ]
        
        if request_data.operation_type not in valid_machine_ops:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid operation type for machines: {request_data.operation_type}"
            )
        
        # Get WebSocket manager from app state
        websocket_manager = getattr(request.app.state, 'websocket_manager', None)
        if websocket_manager is None:
            logger.warning("WebSocket manager not available in app state")
        
        manager = BatchMachineOperationsManager(db, websocket_manager)
        batch_op = await manager.execute_batch_operation(
            operation_type=request_data.operation_type,
            machine_ids=request_data.machine_ids,
            created_by=current_user.id
        )
        
        return BatchOperationResponse(
            id=batch_op.id,
            operation_type=batch_op.operation_type.value,
            status=batch_op.status.value,
            total_items=batch_op.total_items,
            completed_items=batch_op.completed_items,
            failed_items=batch_op.failed_items,
            created_at=batch_op.created_at.isoformat(),
            started_at=batch_op.started_at.isoformat() if batch_op.started_at else None,
            completed_at=batch_op.completed_at.isoformat() if batch_op.completed_at else None,
            error_message=batch_op.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start batch machine operation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start batch operation: {str(e)}"
        )


@router.get("/operations/{operation_id}")
async def get_batch_operation_status(
    operation_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Get status of a batch operation"""
    try:
        from app.models.batch_operation import BatchOperation
        from sqlalchemy import select
        
        stmt = select(BatchOperation).where(BatchOperation.id == operation_id)
        result = await db.execute(stmt)
        batch_op = result.scalar_one_or_none()
        
        if not batch_op:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch operation {operation_id} not found"
            )
        
        # Get detailed status based on operation type
        if batch_op.operation_type in [
            BatchOperationType.IMAGE_BACKUP,
            BatchOperationType.IMAGE_RESTORE,
            BatchOperationType.IMAGE_TEST
        ]:
            manager = BatchImageOperationsManager(db)
            status_data = await manager.get_operation_status(operation_id)
        else:
            manager = BatchMachineOperationsManager(db)
            status_data = await manager.get_operation_status(operation_id)
        
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch operation {operation_id} not found"
            )
        
        return status_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get batch operation status", operation_id=operation_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get operation status: {str(e)}"
        )


@router.post("/operations/{operation_id}/cancel")
async def cancel_batch_operation(
    operation_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a running batch operation"""
    try:
        from app.models.batch_operation import BatchOperation
        from sqlalchemy import select
        
        stmt = select(BatchOperation).where(BatchOperation.id == operation_id)
        result = await db.execute(stmt)
        batch_op = result.scalar_one_or_none()
        
        if not batch_op:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch operation {operation_id} not found"
            )
        
        # Cancel based on operation type
        if batch_op.operation_type in [
            BatchOperationType.MACHINE_RESTART,
            BatchOperationType.MACHINE_SHUTDOWN,
            BatchOperationType.MACHINE_WAKE,
            BatchOperationType.MACHINE_TURN_ON
        ]:
            manager = BatchMachineOperationsManager(db)
            success = await manager.cancel_operation(operation_id)
        else:
            # For image operations, just update status
            batch_op.status = BatchOperationStatus.CANCELLED
            await db.commit()
            success = True
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel operation in current state"
            )
        
        return {"message": "Operation cancelled", "operation_id": operation_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel batch operation", operation_id=operation_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel operation: {str(e)}"
        )


@router.get("/operations")
async def list_batch_operations(
    operation_type: Optional[BatchOperationType] = None,
    status_filter: Optional[BatchOperationStatus] = Query(None, alias="status"),
    limit: int = 50,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """List batch operations with filters"""
    try:
        from app.models.batch_operation import BatchOperation
        from sqlalchemy import select
        
        stmt = select(BatchOperation)
        
        if operation_type:
            stmt = stmt.where(BatchOperation.operation_type == operation_type)
        
        if status_filter:
            stmt = stmt.where(BatchOperation.status == status_filter)
        
        stmt = stmt.order_by(BatchOperation.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        operations = result.scalars().all()
        
        return [
            BatchOperationResponse(
                id=op.id,
                operation_type=op.operation_type.value,
                status=op.status.value,
                total_items=op.total_items,
                completed_items=op.completed_items,
                failed_items=op.failed_items,
                created_at=op.created_at.isoformat(),
                started_at=op.started_at.isoformat() if op.started_at else None,
                completed_at=op.completed_at.isoformat() if op.completed_at else None,
                error_message=op.error_message
            )
            for op in operations
        ]
    except Exception as e:
        logger.error("Failed to list batch operations", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list operations: {str(e)}"
        )




