"""
Storage management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import os
import structlog
import psutil
from pathlib import Path

from app.core.database import get_db
from app.core.config import get_settings
from app.core.dependencies import get_current_user, require_operator
from app.models.user import User
from app.core.exceptions import StorageError

router = APIRouter()
logger = structlog.get_logger()
settings = get_settings()


# Pydantic models
class StorageInfo(BaseModel):
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    total_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float


class StorageResponse(BaseModel):
    upload_storage: StorageInfo
    images_storage: StorageInfo
    system_storage: StorageInfo


class MountInfo(BaseModel):
    device: str
    mountpoint: str
    filesystem: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float


def get_directory_info(path: Path) -> StorageInfo:
    """Get storage information for a directory"""
    try:
        # Get disk usage for the directory's filesystem
        usage = psutil.disk_usage(str(path))
        
        return StorageInfo(
            path=str(path),
            total_bytes=usage.total,
            used_bytes=usage.used,
            free_bytes=usage.free,
            total_gb=round(usage.total / (1024**3), 2),
            used_gb=round(usage.used / (1024**3), 2),
            free_gb=round(usage.free / (1024**3), 2),
            usage_percent=round((usage.used / usage.total) * 100, 2)
        )
    except Exception as e:
        logger.error("Failed to get directory info", path=str(path), error=str(e))
        raise StorageError(f"Failed to get storage info for {path}: {str(e)}")


@router.get("/info", response_model=StorageResponse)
async def get_storage_info(
    current_user: User = Depends(get_current_user)
):
    """Get storage information for all configured directories"""
    
    try:
        upload_info = get_directory_info(settings.UPLOAD_DIR)
        images_info = get_directory_info(settings.IMAGES_DIR)
        
        # System storage (root filesystem)
        system_info = get_directory_info(Path("/"))
        
        return StorageResponse(
            upload_storage=upload_info,
            images_storage=images_info,
            system_storage=system_info
        )
        
    except Exception as e:
        logger.error("Failed to get storage information", error=str(e))
        raise StorageError(f"Failed to get storage information: {str(e)}")


@router.get("/mounts", response_model=List[MountInfo])
async def get_mount_info(
    current_user: User = Depends(require_operator)
):
    """Get information about all mounted filesystems"""
    
    try:
        mounts = []
        
        # Get all disk partitions
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            try:
                # Get usage info for each partition
                usage = psutil.disk_usage(partition.mountpoint)
                
                mount_info = MountInfo(
                    device=partition.device,
                    mountpoint=partition.mountpoint,
                    filesystem=partition.fstype,
                    total_bytes=usage.total,
                    used_bytes=usage.used,
                    free_bytes=usage.free,
                    usage_percent=round((usage.used / usage.total) * 100, 2) if usage.total > 0 else 0
                )
                
                mounts.append(mount_info)
                
            except PermissionError:
                # Skip partitions we can't access
                continue
            except Exception as e:
                logger.warning(
                    "Failed to get usage for partition",
                    device=partition.device,
                    mountpoint=partition.mountpoint,
                    error=str(e)
                )
                continue
        
        return mounts
        
    except Exception as e:
        logger.error("Failed to get mount information", error=str(e))
        raise StorageError(f"Failed to get mount information: {str(e)}")


@router.post("/cleanup")
async def cleanup_storage(
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Clean up temporary and orphaned files"""
    
    try:
        cleanup_stats = {
            "temp_files_removed": 0,
            "orphaned_files_removed": 0,
            "space_freed_bytes": 0
        }
        
        # Implement actual cleanup logic
        import os
        import time
        from datetime import datetime, timedelta
        
        # Remove temporary upload files older than 24 hours
        temp_upload_dir = settings.UPLOAD_DIR / "temp"
        if temp_upload_dir.exists():
            current_time = time.time()
            for file_path in temp_upload_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > 24 * 3600:  # 24 hours
                        try:
                            file_path.unlink()
                            cleanup_stats["temp_files_removed"] += 1
                            cleanup_stats["space_freed_bytes"] += file_path.stat().st_size
                        except OSError:
                            logger.warning(f"Failed to remove temp file: {file_path}")
        
        # Remove orphaned image files not referenced in database
        images_dir = settings.IMAGES_DIR
        if images_dir.exists():
            # Get all image files from database
            db_images_result = await db.execute(select(Image.filename))
            db_filenames = {row[0] for row in db_images_result.fetchall()}
            
            # Check files in images directory
            for file_path in images_dir.iterdir():
                if file_path.is_file() and file_path.name not in db_filenames:
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        cleanup_stats["orphaned_files_removed"] += 1
                        cleanup_stats["space_freed_bytes"] += file_size
                    except OSError:
                        logger.warning(f"Failed to remove orphaned file: {file_path}")
        
        # Clean up old log files (older than 30 days)
        logs_dir = Path("./logs")
        if logs_dir.exists():
            cutoff_date = datetime.now() - timedelta(days=30)
            for file_path in logs_dir.iterdir():
                if file_path.is_file() and file_path.suffix == ".log":
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        try:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            cleanup_stats["temp_files_removed"] += 1
                            cleanup_stats["space_freed_bytes"] += file_size
                        except OSError:
                            logger.warning(f"Failed to remove old log file: {file_path}")
        
        # Remove incomplete uploads (files with .tmp extension)
        for directory in [settings.UPLOAD_DIR, settings.IMAGES_DIR]:
            if directory.exists():
                for file_path in directory.rglob("*.tmp"):
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        cleanup_stats["temp_files_removed"] += 1
                        cleanup_stats["space_freed_bytes"] += file_size
                    except OSError:
                        logger.warning(f"Failed to remove incomplete upload: {file_path}")
        
        logger.info(
            "Storage cleanup completed",
            stats=cleanup_stats,
            user_id=current_user.id
        )
        
        return {
            "message": "Storage cleanup completed",
            "stats": cleanup_stats
        }
        
    except Exception as e:
        logger.error("Storage cleanup failed", error=str(e), user_id=current_user.id)
        raise StorageError(f"Storage cleanup failed: {str(e)}")


@router.get("/health")
async def check_storage_health(
    current_user: User = Depends(get_current_user)
):
    """Check storage health and return warnings if needed"""
    
    try:
        health_status = {
            "status": "healthy",
            "warnings": [],
            "errors": []
        }
        
        # Check upload directory
        try:
            upload_info = get_directory_info(settings.UPLOAD_DIR)
            if upload_info.usage_percent > 90:
                health_status["warnings"].append(
                    f"Upload directory is {upload_info.usage_percent}% full"
                )
            if upload_info.usage_percent > 95:
                health_status["errors"].append(
                    f"Upload directory critically full: {upload_info.usage_percent}%"
                )
        except Exception as e:
            health_status["errors"].append(f"Cannot access upload directory: {str(e)}")
        
        # Check images directory
        try:
            images_info = get_directory_info(settings.IMAGES_DIR)
            if images_info.usage_percent > 90:
                health_status["warnings"].append(
                    f"Images directory is {images_info.usage_percent}% full"
                )
            if images_info.usage_percent > 95:
                health_status["errors"].append(
                    f"Images directory critically full: {images_info.usage_percent}%"
                )
        except Exception as e:
            health_status["errors"].append(f"Cannot access images directory: {str(e)}")
        
        # Check directory permissions
        if not settings.UPLOAD_DIR.exists():
            health_status["errors"].append("Upload directory does not exist")
        elif not os.access(settings.UPLOAD_DIR, os.W_OK):
            health_status["errors"].append("Upload directory is not writable")
        
        if not settings.IMAGES_DIR.exists():
            health_status["errors"].append("Images directory does not exist")
        elif not os.access(settings.IMAGES_DIR, os.W_OK):
            health_status["errors"].append("Images directory is not writable")
        
        # Determine overall status
        if health_status["errors"]:
            health_status["status"] = "error"
        elif health_status["warnings"]:
            health_status["status"] = "warning"
        
        return health_status
        
    except Exception as e:
        logger.error("Storage health check failed", error=str(e))
        return {
            "status": "error",
            "warnings": [],
            "errors": [f"Health check failed: {str(e)}"]
        }

