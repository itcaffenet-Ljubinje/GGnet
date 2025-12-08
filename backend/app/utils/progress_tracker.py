"""
Progress tracking utility for long-running operations
Sends WebSocket events for real-time progress updates
"""

from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import structlog

logger = structlog.get_logger()


class ProgressEventType(str, Enum):
    """Progress event types"""
    ARRAY_REBUILD_PROGRESS = "array_rebuild_progress_updated"
    ARRAY_TRIM_PROGRESS = "array_trim_progress_updated"
    IMAGE_IMPORT_PROGRESS = "image_import_progress_updated"
    IMAGE_BACKUP_PROGRESS = "image_backup_progress_updated"
    IMAGE_RESTORE_PROGRESS = "image_restore_progress_updated"
    BATCH_OPERATION_PROGRESS = "batch_operation_progress_updated"


class ProgressTracker:
    """Tracks and broadcasts progress for long-running operations"""
    
    def __init__(self, operation_id: str, operation_type: str, websocket_manager=None):
        """
        Initialize progress tracker
        
        Args:
            operation_id: Unique operation identifier
            operation_type: Type of operation (e.g., "rebuild", "trim", "import")
            websocket_manager: Optional WebSocket manager for broadcasting
        """
        self.operation_id = operation_id
        self.operation_type = operation_type
        self.websocket_manager = websocket_manager
        self.start_time = datetime.utcnow()
        self.current_step = 0
        self.total_steps = 0
        self.status = "running"
        self.message = ""
        self.metadata: Dict[str, Any] = {}
    
    def set_total_steps(self, total: int):
        """Set total number of steps"""
        self.total_steps = total
    
    async def update_progress(
        self,
        current: int,
        total: Optional[int] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Update progress
        
        Args:
            current: Current step number
            total: Total steps (if different from initial)
            message: Progress message
            metadata: Additional metadata
        """
        self.current_step = current
        if total is not None:
            self.total_steps = total
        if message:
            self.message = message
        if metadata:
            self.metadata.update(metadata)
        
        await self._broadcast_progress()
    
    async def update_percentage(
        self,
        percentage: float,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Update progress by percentage
        
        Args:
            percentage: Progress percentage (0-100)
            message: Progress message
            metadata: Additional metadata
        """
        if self.total_steps > 0:
            current = int((percentage / 100) * self.total_steps)
            await self.update_progress(current, message=message, metadata=metadata)
        else:
            # If total_steps not set, just update metadata
            if message:
                self.message = message
            if metadata:
                self.metadata.update(metadata)
            self.metadata["percentage"] = percentage
            await self._broadcast_progress()
    
    async def set_status(self, status: str, message: Optional[str] = None):
        """
        Set operation status
        
        Args:
            status: Status ("running", "completed", "failed", "cancelled")
            message: Status message
        """
        self.status = status
        if message:
            self.message = message
        
        await self._broadcast_progress()
    
    async def complete(self, message: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Mark operation as completed"""
        self.status = "completed"
        if message:
            self.message = message
        if metadata:
            self.metadata.update(metadata)
        await self._broadcast_progress()
    
    async def fail(self, error: str, metadata: Optional[Dict[str, Any]] = None):
        """Mark operation as failed"""
        self.status = "failed"
        self.message = error
        if metadata:
            self.metadata.update(metadata)
        await self._broadcast_progress()
    
    async def cancel(self, message: Optional[str] = None):
        """Mark operation as cancelled"""
        self.status = "cancelled"
        if message:
            self.message = message
        await self._broadcast_progress()
    
    async def _broadcast_progress(self):
        """Broadcast progress update via WebSocket"""
        try:
            if not self.websocket_manager:
                return
            
            # Determine event type based on operation type
            event_type_map = {
                "rebuild": ProgressEventType.ARRAY_REBUILD_PROGRESS,
                "trim": ProgressEventType.ARRAY_TRIM_PROGRESS,
                "import": ProgressEventType.IMAGE_IMPORT_PROGRESS,
                "backup": ProgressEventType.IMAGE_BACKUP_PROGRESS,
                "restore": ProgressEventType.IMAGE_RESTORE_PROGRESS,
                "batch": ProgressEventType.BATCH_OPERATION_PROGRESS,
            }
            
            event_type = event_type_map.get(self.operation_type, ProgressEventType.BATCH_OPERATION_PROGRESS)
            
            # Calculate percentage
            percentage = 0
            if self.total_steps > 0:
                percentage = (self.current_step / self.total_steps) * 100
            elif "percentage" in self.metadata:
                percentage = self.metadata["percentage"]
            
            # Calculate elapsed time
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()
            
            # Prepare progress data
            progress_data = {
                "operation_id": self.operation_id,
                "operation_type": self.operation_type,
                "status": self.status,
                "current_step": self.current_step,
                "total_steps": self.total_steps,
                "percentage": round(percentage, 2),
                "message": self.message,
                "elapsed_seconds": round(elapsed, 2),
                "metadata": self.metadata,
            }
            
            # Broadcast to all connected clients
            await self.websocket_manager.broadcast({
                "type": event_type.value,
                "data": progress_data,
            })
            
        except Exception as e:
            logger.warning("Failed to broadcast progress", error=str(e))
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress data"""
        percentage = 0
        if self.total_steps > 0:
            percentage = (self.current_step / self.total_steps) * 100
        elif "percentage" in self.metadata:
            percentage = self.metadata["percentage"]
        
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "status": self.status,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "percentage": round(percentage, 2),
            "message": self.message,
            "elapsed_seconds": round(elapsed, 2),
            "metadata": self.metadata,
        }


# Global progress trackers storage
_progress_trackers: Dict[str, ProgressTracker] = {}


def create_progress_tracker(operation_id: str, operation_type: str, websocket_manager=None) -> ProgressTracker:
    """
    Create a new progress tracker
    
    Args:
        operation_id: Unique operation identifier
        operation_type: Type of operation
        websocket_manager: Optional WebSocket manager
        
    Returns:
        ProgressTracker instance
    """
    tracker = ProgressTracker(operation_id, operation_type, websocket_manager)
    _progress_trackers[operation_id] = tracker
    return tracker


def get_progress_tracker(operation_id: str) -> Optional[ProgressTracker]:
    """Get a progress tracker by operation ID"""
    return _progress_trackers.get(operation_id)


def remove_progress_tracker(operation_id: str):
    """Remove a progress tracker"""
    if operation_id in _progress_trackers:
        del _progress_trackers[operation_id]




