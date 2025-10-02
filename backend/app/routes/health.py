"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog
from datetime import datetime
import psutil
import os

from app.core.database import get_db
from app.core.config import get_settings

router = APIRouter()
logger = structlog.get_logger()


@router.get("")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ggnet-diskless-server",
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with system information"""
    settings = get_settings()
    
    # Database health
    db_healthy = True
    db_error = None
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_healthy = False
        db_error = str(e)
        logger.error("Database health check failed", error=str(e))
    
    # System resources
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
    except Exception as e:
        logger.error("System metrics collection failed", error=str(e))
        cpu_percent = None
        memory = None
        disk = None
    
    # Check critical directories
    directories_status = {}
    critical_dirs = [settings.UPLOAD_DIR, settings.IMAGES_DIR]
    
    for dir_path in critical_dirs:
        try:
            exists = dir_path.exists()
            writable = os.access(dir_path, os.W_OK) if exists else False
            directories_status[str(dir_path)] = {
                "exists": exists,
                "writable": writable,
                "status": "healthy" if exists and writable else "error"
            }
        except Exception as e:
            directories_status[str(dir_path)] = {
                "exists": False,
                "writable": False,
                "status": "error",
                "error": str(e)
            }
    
    # Overall health status
    overall_healthy = (
        db_healthy and
        all(d["status"] == "healthy" for d in directories_status.values())
    )
    
    health_data = {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ggnet-diskless-server",
        "version": "1.0.0",
        "checks": {
            "database": {
                "status": "healthy" if db_healthy else "error",
                "error": db_error
            },
            "directories": directories_status,
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_mb": round(memory.total / 1024 / 1024) if memory else None,
                    "available_mb": round(memory.available / 1024 / 1024) if memory else None,
                    "percent_used": memory.percent if memory else None
                } if memory else None,
                "disk": {
                    "total_gb": round(disk.total / 1024 / 1024 / 1024) if disk else None,
                    "free_gb": round(disk.free / 1024 / 1024 / 1024) if disk else None,
                    "percent_used": round((disk.used / disk.total) * 100) if disk else None
                } if disk else None
            }
        }
    }
    
    return health_data


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Kubernetes readiness probe"""
    try:
        # Check database connection
        await db.execute(text("SELECT 1"))
        
        # Check critical services (could add more checks here)
        settings = get_settings()
        if not settings.UPLOAD_DIR.exists():
            return {"status": "not_ready", "reason": "upload_directory_missing"}
        
        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return {"status": "not_ready", "reason": str(e)}


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

