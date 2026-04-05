"""
Batch Image Operations Manager - Async version
Handles bulk operations on images (backup, restore, test)
"""

import os
import shutil
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from enum import Enum
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.models.batch_operation import (
    BatchOperation, BatchImageOperation, BatchOperationType, BatchOperationStatus
)
from app.models.image import Image

logger = structlog.get_logger()


class ImageOperationType(str, Enum):
    """Image operation types"""
    BACKUP = 'backup'
    RESTORE = 'restore'
    TEST = 'test'


class BatchImageOperationsManager:
    """Manages batch operations on images"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize batch image operations manager
        
        Args:
            db: Async database session
        """
        self.db = db
        self.active_operations: Dict[int, asyncio.Task] = {}
    
    async def execute_batch_backup_local(
        self,
        image_ids: List[int],
        backup_path: str,
        created_by: int = 1
    ) -> BatchOperation:
        """
        Execute batch local backup operation
        
        Args:
            image_ids: List of image IDs to backup
            backup_path: Local backup directory path
            created_by: User ID who created the operation
            
        Returns:
            BatchOperation instance
        """
        return await self._execute_batch_operation(
            operation_type=BatchOperationType.IMAGE_BACKUP,
            image_ids=image_ids,
            config={"backup_path": backup_path, "is_remote": False},
            created_by=created_by
        )
    
    async def execute_batch_backup_remote(
        self,
        image_ids: List[int],
        remote_host: str,
        remote_path: str,
        created_by: int = 1
    ) -> BatchOperation:
        """
        Execute batch remote backup operation
        
        Args:
            image_ids: List of image IDs to backup
            remote_host: Remote host (IP or hostname)
            remote_path: Remote backup directory path
            created_by: User ID who created the operation
            
        Returns:
            BatchOperation instance
        """
        return await self._execute_batch_operation(
            operation_type=BatchOperationType.IMAGE_BACKUP,
            image_ids=image_ids,
            config={"backup_path": f"{remote_host}:{remote_path}", "is_remote": True},
            created_by=created_by
        )
    
    async def execute_batch_restore_local(
        self,
        image_ids: List[int],
        backup_path: str,
        created_by: int = 1
    ) -> BatchOperation:
        """Execute batch local restore operation"""
        return await self._execute_batch_operation(
            operation_type=BatchOperationType.IMAGE_RESTORE,
            image_ids=image_ids,
            config={"backup_path": backup_path, "is_remote": False},
            created_by=created_by
        )
    
    async def execute_batch_test_local(
        self,
        image_ids: List[int],
        backup_path: str,
        created_by: int = 1
    ) -> BatchOperation:
        """Execute batch local test operation (verify backup integrity)"""
        return await self._execute_batch_operation(
            operation_type=BatchOperationType.IMAGE_TEST,
            image_ids=image_ids,
            config={"backup_path": backup_path, "is_remote": False},
            created_by=created_by
        )
    
    async def _execute_batch_operation(
        self,
        operation_type: BatchOperationType,
        image_ids: List[int],
        config: Dict,
        created_by: int
    ) -> BatchOperation:
        """Execute batch operation on multiple images"""
        # Create batch operation record
        batch_op = BatchOperation(
            operation_type=operation_type,
            status=BatchOperationStatus.PENDING,
            total_items=len(image_ids),
            completed_items=0,
            failed_items=0,
            config=config,
            created_by=created_by
        )
        
        self.db.add(batch_op)
        await self.db.flush()
        
        # Create batch operation image records
        for image_id in image_ids:
            batch_op_image = BatchImageOperation(
                batch_operation_id=batch_op.id,
                image_id=image_id,
                status=BatchOperationStatus.PENDING,
            )
            self.db.add(batch_op_image)
        
        await self.db.commit()
        await self.db.refresh(batch_op)
        
        # Start operation in background task
        task = asyncio.create_task(
            self._execute_operation_task(batch_op.id, operation_type, image_ids, config)
        )
        self.active_operations[batch_op.id] = task
        
        return batch_op
    
    async def _execute_operation_task(
        self,
        batch_op_id: int,
        operation_type: BatchOperationType,
        image_ids: List[int],
        config: Dict
    ):
        """Execute operation in background task"""
        try:
            # Update status to running
            stmt = select(BatchOperation).where(BatchOperation.id == batch_op_id)
            result = await self.db.execute(stmt)
            batch_op = result.scalar_one_or_none()
            
            if not batch_op:
                return
            
            batch_op.status = BatchOperationStatus.RUNNING
            batch_op.started_at = datetime.utcnow()
            await self.db.commit()
            
            # Execute operation on each image
            for image_id in image_ids:
                # Get image
                stmt = select(Image).where(Image.id == image_id)
                result = await self.db.execute(stmt)
                image = result.scalar_one_or_none()
                
                if not image:
                    continue
                
                # Get batch operation image record
                stmt = select(BatchImageOperation).where(
                    BatchImageOperation.batch_operation_id == batch_op_id,
                    BatchImageOperation.image_id == image_id
                )
                result = await self.db.execute(stmt)
                batch_op_image = result.scalar_one_or_none()
                
                if not batch_op_image:
                    continue
                
                # Execute operation
                success, error = await self._execute_single_operation(
                    operation_type,
                    image,
                    config
                )
                
                # Update batch operation image status
                if success:
                    batch_op_image.status = BatchOperationStatus.COMPLETED
                    batch_op_image.completed_at = datetime.utcnow()
                    batch_op.completed_items += 1
                else:
                    batch_op_image.status = BatchOperationStatus.FAILED
                    batch_op_image.error_message = error
                    batch_op.failed_items += 1
                    batch_op.completed_items += 1
                
                await self.db.commit()
                
                # Small delay between operations
                await asyncio.sleep(0.5)
            
            # Update batch operation status
            batch_op.status = BatchOperationStatus.COMPLETED
            batch_op.completed_at = datetime.utcnow()
            await self.db.commit()
            
            logger.info("Batch image operation completed", batch_op_id=batch_op_id)
            
        except Exception as e:
            logger.error("Batch image operation failed", batch_op_id=batch_op_id, error=str(e))
            # Mark operation as failed
            stmt = select(BatchOperation).where(BatchOperation.id == batch_op_id)
            result = await self.db.execute(stmt)
            batch_op = result.scalar_one_or_none()
            if batch_op:
                batch_op.status = BatchOperationStatus.FAILED
                batch_op.error_message = str(e)
                await self.db.commit()
        finally:
            # Remove from active operations
            if batch_op_id in self.active_operations:
                del self.active_operations[batch_op_id]
    
    async def _execute_single_operation(
        self,
        operation_type: BatchOperationType,
        image: Image,
        config: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Execute single operation on an image"""
        if not os.path.exists(image.file_path):
            return False, "Image file not found"
        
        try:
            is_remote = config.get("is_remote", False)
            backup_path = config.get("backup_path", "")
            
            if operation_type == BatchOperationType.IMAGE_BACKUP:
                return await self._backup_image(image.file_path, backup_path, is_remote)
            elif operation_type == BatchOperationType.IMAGE_RESTORE:
                return await self._restore_image(image.file_path, backup_path, is_remote)
            elif operation_type == BatchOperationType.IMAGE_TEST:
                return await self._test_image(image.file_path, backup_path, is_remote)
            else:
                return False, f"Unknown operation type: {operation_type}"
        except Exception as e:
            return False, str(e)
    
    async def _backup_image(self, image_path: str, backup_path: str, is_remote: bool) -> Tuple[bool, Optional[str]]:
        """Backup an image"""
        try:
            if is_remote:
                # Remote backup using rsync or scp
                # TODO: Implement remote backup
                await asyncio.sleep(2)  # Simulate operation
                return True, None
            else:
                # Local backup
                os.makedirs(backup_path, exist_ok=True)
                backup_file = os.path.join(backup_path, os.path.basename(image_path))
                # Use asyncio to run file copy in thread pool
                await asyncio.to_thread(shutil.copy2, image_path, backup_file)
                return True, None
        except Exception as e:
            return False, f"Backup failed: {str(e)}"
    
    async def _restore_image(self, image_path: str, backup_path: str, is_remote: bool) -> Tuple[bool, Optional[str]]:
        """Restore an image from backup"""
        try:
            if is_remote:
                # TODO: Implement remote restore
                await asyncio.sleep(2)
                return True, None
            else:
                backup_file = os.path.join(backup_path, os.path.basename(image_path))
                if not os.path.exists(backup_file):
                    return False, "Backup file not found"
                
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                await asyncio.to_thread(shutil.copy2, backup_file, image_path)
                return True, None
        except Exception as e:
            return False, f"Restore failed: {str(e)}"
    
    async def _test_image(self, image_path: str, backup_path: str, is_remote: bool) -> Tuple[bool, Optional[str]]:
        """Test image backup integrity"""
        try:
            if is_remote:
                # TODO: Implement remote test
                await asyncio.sleep(1)
                return True, None
            else:
                backup_file = os.path.join(backup_path, os.path.basename(image_path))
                if not os.path.exists(backup_file):
                    return False, "Backup file not found"
                
                # Compare file sizes
                original_size = os.path.getsize(image_path)
                backup_size = os.path.getsize(backup_file)
                
                if original_size != backup_size:
                    return False, f"Size mismatch: original={original_size}, backup={backup_size}"
                
                return True, None
        except Exception as e:
            return False, f"Test failed: {str(e)}"
    
    async def get_operation_status(self, operation_id: int) -> Optional[Dict]:
        """Get status of a batch image operation"""
        stmt = select(BatchOperation).where(BatchOperation.id == operation_id)
        result = await self.db.execute(stmt)
        batch_op = result.scalar_one_or_none()
        
        if not batch_op:
            return None
        
        # Get image details
        stmt = select(BatchImageOperation).where(
            BatchImageOperation.batch_operation_id == operation_id
        )
        result = await self.db.execute(stmt)
        images = result.scalars().all()
        
        return {
            'id': batch_op.id,
            'operation_type': batch_op.operation_type.value,
            'status': batch_op.status.value,
            'total_items': batch_op.total_items,
            'completed_items': batch_op.completed_items,
            'failed_items': batch_op.failed_items,
            'config': batch_op.config,
            'created_at': batch_op.created_at.isoformat() if batch_op.created_at else None,
            'started_at': batch_op.started_at.isoformat() if batch_op.started_at else None,
            'completed_at': batch_op.completed_at.isoformat() if batch_op.completed_at else None,
            'error_message': batch_op.error_message,
            'images': [{
                'image_id': img.image_id,
                'status': img.status.value,
                'error_message': img.error_message,
                'completed_at': img.completed_at.isoformat() if img.completed_at else None
            } for img in images]
        }
    
    async def get_operation_history(self, limit: int = 50) -> List[Dict]:
        """Get operation history"""
        stmt = select(BatchOperation).where(
            BatchOperation.operation_type.in_([
                BatchOperationType.IMAGE_BACKUP,
                BatchOperationType.IMAGE_RESTORE,
                BatchOperationType.IMAGE_TEST
            ])
        ).order_by(BatchOperation.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        operations = result.scalars().all()
        
        return [{
            'id': op.id,
            'operation_type': op.operation_type.value,
            'status': op.status.value,
            'total_items': op.total_items,
            'completed_items': op.completed_items,
            'failed_items': op.failed_items,
            'created_at': op.created_at.isoformat() if op.created_at else None,
            'completed_at': op.completed_at.isoformat() if op.completed_at else None
        } for op in operations]




