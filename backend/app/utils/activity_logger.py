"""
Enhanced Activity Logger
Logs user activities and system events for audit trail
Compatible with existing AuditLog model
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sql_func
import structlog

from app.models.audit import AuditLog, AuditAction, AuditSeverity

logger = structlog.get_logger()


class ActivityType(str, Enum):
    """Extended activity types - maps to AuditAction where possible"""
    # User activities
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    
    # Machine activities
    MACHINE_CREATE = "machine_create"
    MACHINE_UPDATE = "machine_update"
    MACHINE_DELETE = "machine_delete"
    MACHINE_RESTART = "machine_restart"
    MACHINE_SHUTDOWN = "machine_shutdown"
    MACHINE_WAKE = "machine_wake"
    
    # Image activities
    IMAGE_UPLOAD = "image_upload"
    IMAGE_DELETE = "image_delete"
    IMAGE_UPDATE = "image_update"
    IMAGE_BACKUP = "image_backup"
    IMAGE_RESTORE = "image_restore"
    
    # Storage activities
    ARRAY_CREATE = "array_create"
    ARRAY_EXTEND = "array_extend"
    ARRAY_REPLACE = "array_replace"
    DRIVE_ADD = "drive_add"
    DRIVE_REMOVE = "drive_remove"
    TRIM_START = "trim_start"
    TRIM_STOP = "trim_stop"
    ZFS_POOL_CREATE = "zfs_pool_create"
    ZFS_POOL_DESTROY = "zfs_pool_destroy"
    ZFS_POOL_SCRUB = "zfs_pool_scrub"
    ZFS_SNAPSHOT_CREATE = "zfs_snapshot_create"
    ZFS_SNAPSHOT_DESTROY = "zfs_snapshot_destroy"
    
    # Writeback activities
    WRITEBACK_KEEP = "writeback_keep"
    WRITEBACK_DELETE = "writeback_delete"
    
    # Snapshot activities
    SNAPSHOT_CREATE = "snapshot_create"
    SNAPSHOT_DELETE = "snapshot_delete"
    
    # Scheduler activities
    SCHEDULER_JOB_CREATE = "scheduler_job_create"
    SCHEDULER_JOB_UPDATE = "scheduler_job_update"
    SCHEDULER_JOB_DELETE = "scheduler_job_delete"
    SCHEDULER_JOB_EXECUTE = "scheduler_job_execute"
    
    # Network activities
    PXE_ENABLE = "pxe_enable"
    PXE_DISABLE = "pxe_disable"
    ISCSI_TARGET_CREATE = "iscsi_target_create"
    ISCSI_TARGET_DELETE = "iscsi_target_delete"
    
    # System activities
    SYSTEM_SETTINGS_UPDATE = "system_settings_update"
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"
    
    # Batch operations
    BATCH_OPERATION_START = "batch_operation_start"
    BATCH_OPERATION_COMPLETE = "batch_operation_complete"
    BATCH_OPERATION_FAILED = "batch_operation_failed"


class ActivityLevel(str, Enum):
    """Activity severity levels - maps to AuditSeverity"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


def _map_activity_to_audit_action(activity_type: ActivityType) -> AuditAction:
    """Map ActivityType to AuditAction"""
    mapping = {
        ActivityType.USER_LOGIN: AuditAction.LOGIN,
        ActivityType.USER_LOGOUT: AuditAction.LOGOUT,
        ActivityType.USER_CREATE: AuditAction.USER_CREATED,
        ActivityType.USER_UPDATE: AuditAction.USER_UPDATED,
        ActivityType.USER_DELETE: AuditAction.USER_DELETED,
        ActivityType.MACHINE_CREATE: AuditAction.MACHINE_CREATED,
        ActivityType.MACHINE_UPDATE: AuditAction.MACHINE_UPDATED,
        ActivityType.MACHINE_DELETE: AuditAction.MACHINE_DELETED,
        ActivityType.IMAGE_UPLOAD: AuditAction.IMAGE_UPLOADED,
        ActivityType.IMAGE_DELETE: AuditAction.IMAGE_DELETED,
        ActivityType.ISCSI_TARGET_CREATE: AuditAction.TARGET_CREATED,
        ActivityType.ISCSI_TARGET_DELETE: AuditAction.TARGET_DELETED,
    }
    return mapping.get(activity_type, AuditAction.CONFIG_CHANGED)


def _map_level_to_severity(level: ActivityLevel) -> AuditSeverity:
    """Map ActivityLevel to AuditSeverity"""
    mapping = {
        ActivityLevel.INFO: AuditSeverity.INFO,
        ActivityLevel.WARNING: AuditSeverity.WARNING,
        ActivityLevel.ERROR: AuditSeverity.ERROR,
        ActivityLevel.CRITICAL: AuditSeverity.CRITICAL,
    }
    return mapping.get(level, AuditSeverity.INFO)


class ActivityLogger:
    """Enhanced activity logger compatible with AuditLog model"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize Activity Logger
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def log(
        self,
        activity_type: ActivityType,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        level: ActivityLevel = ActivityLevel.INFO,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        resource_name: Optional[str] = None,
    ) -> AuditLog:
        """
        Log an activity
        
        Args:
            activity_type: Type of activity
            user_id: User ID (if user-initiated)
            username: Username (if user-initiated)
            level: Activity severity level
            description: Human-readable description
            metadata: Additional metadata (JSON-serializable)
            ip_address: Client IP address
            user_agent: Client user agent
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            resource_name: Name of resource affected
            
        Returns:
            Created AuditLog instance
        """
        # Map to AuditAction and AuditSeverity
        action = _map_activity_to_audit_action(activity_type)
        severity = _map_level_to_severity(level)
        
        # Create audit log entry
        audit_log = AuditLog(
            action=action,
            severity=severity,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            message=description or self._get_default_description(activity_type),
            details={
                "activity_type": activity_type.value,
                **(metadata or {})
            },
            tags=[activity_type.value, level.value],
        )
        
        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        
        logger.info(
            "Activity logged",
            activity_type=activity_type.value,
            user_id=user_id,
            username=username,
            level=level.value
        )
        
        return audit_log
    
    def _get_default_description(self, activity_type: ActivityType) -> str:
        """Get default description for activity type"""
        descriptions = {
            ActivityType.USER_LOGIN: "User logged in",
            ActivityType.USER_LOGOUT: "User logged out",
            ActivityType.USER_CREATE: "User created",
            ActivityType.USER_UPDATE: "User updated",
            ActivityType.USER_DELETE: "User deleted",
            ActivityType.MACHINE_CREATE: "Machine created",
            ActivityType.MACHINE_UPDATE: "Machine updated",
            ActivityType.MACHINE_DELETE: "Machine deleted",
            ActivityType.MACHINE_RESTART: "Machine restarted",
            ActivityType.MACHINE_SHUTDOWN: "Machine shut down",
            ActivityType.MACHINE_WAKE: "Machine woken up",
            ActivityType.IMAGE_UPLOAD: "Image uploaded",
            ActivityType.IMAGE_DELETE: "Image deleted",
            ActivityType.IMAGE_UPDATE: "Image updated",
            ActivityType.IMAGE_BACKUP: "Image backup created",
            ActivityType.IMAGE_RESTORE: "Image restored",
            ActivityType.ARRAY_CREATE: "Storage array created",
            ActivityType.ARRAY_EXTEND: "Storage array extended",
            ActivityType.ARRAY_REPLACE: "Storage array drive replaced",
            ActivityType.DRIVE_ADD: "Drive added",
            ActivityType.DRIVE_REMOVE: "Drive removed",
            ActivityType.TRIM_START: "TRIM operation started",
            ActivityType.TRIM_STOP: "TRIM operation stopped",
            ActivityType.WRITEBACK_KEEP: "Writeback kept",
            ActivityType.WRITEBACK_DELETE: "Writeback deleted",
            ActivityType.SNAPSHOT_CREATE: "Snapshot created",
            ActivityType.SNAPSHOT_DELETE: "Snapshot deleted",
            ActivityType.ZFS_POOL_CREATE: "ZFS pool created",
            ActivityType.ZFS_POOL_DESTROY: "ZFS pool destroyed",
            ActivityType.ZFS_POOL_SCRUB: "ZFS pool scrub started",
            ActivityType.ZFS_SNAPSHOT_CREATE: "ZFS snapshot created",
            ActivityType.ZFS_SNAPSHOT_DESTROY: "ZFS snapshot destroyed",
            ActivityType.SCHEDULER_JOB_CREATE: "Scheduled job created",
            ActivityType.SCHEDULER_JOB_UPDATE: "Scheduled job updated",
            ActivityType.SCHEDULER_JOB_DELETE: "Scheduled job deleted",
            ActivityType.SCHEDULER_JOB_EXECUTE: "Scheduled job executed",
            ActivityType.PXE_ENABLE: "PXE boot enabled",
            ActivityType.PXE_DISABLE: "PXE boot disabled",
            ActivityType.ISCSI_TARGET_CREATE: "iSCSI target created",
            ActivityType.ISCSI_TARGET_DELETE: "iSCSI target deleted",
            ActivityType.SYSTEM_SETTINGS_UPDATE: "System settings updated",
            ActivityType.SYSTEM_BACKUP: "System backup created",
            ActivityType.SYSTEM_RESTORE: "System restored",
            ActivityType.BATCH_OPERATION_START: "Batch operation started",
            ActivityType.BATCH_OPERATION_COMPLETE: "Batch operation completed",
            ActivityType.BATCH_OPERATION_FAILED: "Batch operation failed",
        }
        
        return descriptions.get(activity_type, "Activity performed")
    
    async def get_activities(
        self,
        user_id: Optional[int] = None,
        activity_type: Optional[ActivityType] = None,
        level: Optional[ActivityLevel] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Get activity logs with filters
        
        Args:
            user_id: Filter by user ID
            activity_type: Filter by activity type
            level: Filter by level
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of AuditLog instances
        """
        stmt = select(AuditLog)
        
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        
        if activity_type:
            # Filter by activity type in details JSON
            stmt = stmt.where(
                AuditLog.details["activity_type"].astext == activity_type.value
            )
        
        if level:
            severity = _map_level_to_severity(level)
            stmt = stmt.where(AuditLog.severity == severity)
        
        if start_date:
            stmt = stmt.where(AuditLog.timestamp >= start_date)
        
        if end_date:
            stmt = stmt.where(AuditLog.timestamp <= end_date)
        
        stmt = stmt.order_by(AuditLog.timestamp.desc())
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_activity_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get activity statistics
        
        Args:
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            Statistics dict
        """
        stmt = select(AuditLog)
        
        if start_date:
            stmt = stmt.where(AuditLog.timestamp >= start_date)
        
        if end_date:
            stmt = stmt.where(AuditLog.timestamp <= end_date)
        
        # Get total count
        count_stmt = select(sql_func.count()).select_from(stmt.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0
        
        # Count by severity
        by_level = {}
        for severity in AuditSeverity:
            severity_stmt = stmt.where(AuditLog.severity == severity)
            count_stmt = select(sql_func.count()).select_from(severity_stmt.subquery())
            result = await self.db.execute(count_stmt)
            count = result.scalar() or 0
            by_level[severity.value] = count
        
        # Count by activity type (from details JSON)
        # This is simplified - in production, might want to use JSON aggregation
        by_type = {}
        all_activities = await self.get_activities(
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        for activity in all_activities:
            if activity.details and "activity_type" in activity.details:
                activity_type = activity.details["activity_type"]
                by_type[activity_type] = by_type.get(activity_type, 0) + 1
        
        # Sort by count and get top 10
        by_type = dict(sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:10])
        
        return {
            "total": total,
            "by_level": by_level,
            "by_type": by_type
        }

