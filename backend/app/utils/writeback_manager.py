"""
Writeback Manager
Handles writeback operations (keep, delete, list) - Async version
"""

import os
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import structlog

from app.models.writeback import Writeback
from app.models.machine import Machine
from app.models.image import Image

logger = structlog.get_logger()


class WritebackManager:
    """Manages writeback operations"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize writeback manager
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def list_writebacks(
        self, 
        machine_id: Optional[int] = None, 
        image_id: Optional[int] = None
    ) -> List[Dict]:
        """
        List all writebacks with optional filtering
        
        Args:
            machine_id: Optional machine ID filter
            image_id: Optional image ID filter
            
        Returns:
            List of writeback dictionaries
        """
        stmt = select(Writeback)
        
        if machine_id is not None:
            stmt = stmt.where(Writeback.machine_id == machine_id)
        if image_id is not None:
            stmt = stmt.where(Writeback.image_id == image_id)
        
        result = await self.db.execute(stmt)
        writebacks = result.scalars().all()
        
        writeback_list = []
        for wb in writebacks:
            # Check if file exists
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
        
        return writeback_list
    
    async def list_machine_writebacks(self, machine_id: int) -> List[Dict]:
        """
        List all writebacks for a machine
        
        Args:
            machine_id: Machine ID
            
        Returns:
            List of writeback dictionaries
        """
        return await self.list_writebacks(machine_id=machine_id)
    
    async def keep_writeback(self, writeback_id: int) -> Tuple[bool, Optional[str]]:
        """
        Keep a writeback (mark as permanent, don't delete on reset)
        
        Args:
            writeback_id: Writeback ID
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            stmt = select(Writeback).where(Writeback.id == writeback_id)
            result = await self.db.execute(stmt)
            writeback = result.scalar_one_or_none()
            
            if not writeback:
                return False, "Writeback not found"
            
            writeback.is_permanent = True
            await self.db.commit()
            
            return True, None
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to keep writeback", writeback_id=writeback_id, error=str(e))
            return False, str(e)
    
    async def keep_all_writebacks(self, machine_id: int) -> Tuple[int, int]:
        """
        Keep all writebacks for a machine
        
        Args:
            machine_id: Machine ID
            
        Returns:
            Tuple of (kept_count, failed_count)
        """
        stmt = select(Writeback).where(Writeback.machine_id == machine_id)
        result = await self.db.execute(stmt)
        writebacks = result.scalars().all()
        
        kept_count = 0
        failed_count = 0
        
        for wb in writebacks:
            success, error = await self.keep_writeback(wb.id)
            if success:
                kept_count += 1
            else:
                failed_count += 1
        
        return kept_count, failed_count
    
    async def delete_writeback(self, writeback_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete a writeback file and database record
        
        Args:
            writeback_id: Writeback ID
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            stmt = select(Writeback).where(Writeback.id == writeback_id)
            result = await self.db.execute(stmt)
            writeback = result.scalar_one_or_none()
            
            if not writeback:
                return False, "Writeback not found"
            
            # Delete file if exists
            if writeback.path and os.path.exists(writeback.path):
                try:
                    os.remove(writeback.path)
                except OSError as e:
                    return False, f"Failed to delete file: {str(e)}"
            
            # Delete database record
            await self.db.delete(writeback)
            await self.db.commit()
            
            return True, None
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to delete writeback", writeback_id=writeback_id, error=str(e))
            return False, str(e)
    
    async def delete_machine_writebacks(self, machine_id: int) -> Tuple[int, int]:
        """
        Delete all writebacks for a machine
        
        Args:
            machine_id: Machine ID
            
        Returns:
            Tuple of (deleted_count, failed_count)
        """
        stmt = select(Writeback).where(Writeback.machine_id == machine_id)
        result = await self.db.execute(stmt)
        writebacks = result.scalars().all()
        
        deleted_count = 0
        failed_count = 0
        
        for wb in writebacks:
            success, error = await self.delete_writeback(wb.id)
            if success:
                deleted_count += 1
            else:
                failed_count += 1
        
        return deleted_count, failed_count
    
    async def delete_image_writebacks(self, image_id: int) -> Tuple[int, int]:
        """
        Delete all writebacks for an image
        
        Args:
            image_id: Image ID
            
        Returns:
            Tuple of (deleted_count, failed_count)
        """
        stmt = select(Writeback).where(Writeback.image_id == image_id)
        result = await self.db.execute(stmt)
        writebacks = result.scalars().all()
        
        deleted_count = 0
        failed_count = 0
        
        for wb in writebacks:
            success, error = await self.delete_writeback(wb.id)
            if success:
                deleted_count += 1
            else:
                failed_count += 1
        
        return deleted_count, failed_count
    
    async def get_writeback_info(self, writeback_id: int) -> Optional[Dict]:
        """
        Get information about a writeback
        
        Args:
            writeback_id: Writeback ID
            
        Returns:
            Writeback info dictionary or None
        """
        stmt = select(Writeback).where(Writeback.id == writeback_id)
        result = await self.db.execute(stmt)
        writeback = result.scalar_one_or_none()
        
        if not writeback:
            return None
        
        file_exists = os.path.exists(writeback.path) if writeback.path else False
        file_size = os.path.getsize(writeback.path) if file_exists and writeback.path else writeback.size
        
        return {
            'id': writeback.id,
            'machine_id': writeback.machine_id,
            'image_id': writeback.image_id,
            'path': writeback.path,
            'size': file_size,
            'file_exists': file_exists,
            'is_permanent': writeback.is_permanent,
            'created_at': writeback.created_at.isoformat() if writeback.created_at else None
        }
    
    async def create_writeback(self, machine_id: int, image_id: int, path: str, size: int = 0) -> Writeback:
        """
        Create a new writeback record
        
        Args:
            machine_id: Machine ID
            image_id: Image ID
            path: Path to writeback file
            size: Size of writeback file in bytes
            
        Returns:
            Created Writeback instance
        """
        writeback = Writeback(
            machine_id=machine_id,
            image_id=image_id,
            path=path,
            size=size,
            is_permanent=False
        )
        
        self.db.add(writeback)
        await self.db.commit()
        await self.db.refresh(writeback)
        
        return writeback

