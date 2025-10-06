"""
Health check and monitoring endpoints
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import psutil
import structlog

from app.core.database import get_db
from app.core.cache import cache_manager
from app.core.config import get_settings

router = APIRouter()
logger = structlog.get_logger()
settings = get_settings()


class HealthStatus:
    """Health status constants"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthResponse:
    """Health check response model"""
    def __init__(self, status: str, timestamp: datetime, version: str, **kwargs):
        self.status = status
        self.timestamp = timestamp
        self.version = version
        self.details = kwargs


@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": HealthStatus.HEALTHY,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "service": "ggnet-backend"
    }


@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with component status"""
    health_status = HealthStatus.HEALTHY
    components = {}
    
    # Database health check
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        components["database"] = {
            "status": HealthStatus.HEALTHY,
            "response_time_ms": 0,  # Could measure actual response time
            "details": "Database connection successful"
        }
    except Exception as e:
        components["database"] = {
            "status": HealthStatus.UNHEALTHY,
            "error": str(e),
            "details": "Database connection failed"
        }
        health_status = HealthStatus.UNHEALTHY
    
    # Redis health check
    try:
        await cache_manager.set("health_check", "ok", expire=10)
        result = await cache_manager.get("health_check")
        if result == "ok":
            components["redis"] = {
                "status": HealthStatus.HEALTHY,
                "details": "Redis connection successful"
            }
        else:
            components["redis"] = {
                "status": HealthStatus.DEGRADED,
                "details": "Redis connection inconsistent"
            }
            if health_status == HealthStatus.HEALTHY:
                health_status = HealthStatus.DEGRADED
    except Exception as e:
        components["redis"] = {
            "status": HealthStatus.UNHEALTHY,
            "error": str(e),
            "details": "Redis connection failed"
        }
        health_status = HealthStatus.UNHEALTHY
    
    # System resources check
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_healthy = (
            cpu_percent < 90 and
            memory.percent < 90 and
            disk.percent < 90
        )
        
        components["system"] = {
            "status": HealthStatus.HEALTHY if system_healthy else HealthStatus.DEGRADED,
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "details": "System resources within normal limits" if system_healthy else "System resources under stress"
        }
        
        if not system_healthy and health_status == HealthStatus.HEALTHY:
            health_status = HealthStatus.DEGRADED
            
    except Exception as e:
        components["system"] = {
            "status": HealthStatus.UNHEALTHY,
            "error": str(e),
            "details": "System resource check failed"
        }
        health_status = HealthStatus.UNHEALTHY
    
    # File system check
    try:
        import os
        from pathlib import Path
        
        # Check if storage directories exist and are writable
        storage_paths = [
            settings.UPLOAD_DIR,
            settings.IMAGES_DIR,
            settings.IMAGE_STORAGE_PATH,
            settings.TEMP_STORAGE_PATH
        ]
        
        storage_healthy = True
        storage_details = []
        
        for path in storage_paths:
            try:
                path_obj = Path(path)
                if not path_obj.exists():
                    path_obj.mkdir(parents=True, exist_ok=True)
                
                # Test write access
                test_file = path_obj / ".health_check"
                test_file.write_text("ok")
                test_file.unlink()
                
                storage_details.append(f"{path}: OK")
            except Exception as e:
                storage_healthy = False
                storage_details.append(f"{path}: ERROR - {str(e)}")
        
        components["storage"] = {
            "status": HealthStatus.HEALTHY if storage_healthy else HealthStatus.UNHEALTHY,
            "details": "; ".join(storage_details)
        }
        
        if not storage_healthy:
            health_status = HealthStatus.UNHEALTHY
            
    except Exception as e:
        components["storage"] = {
            "status": HealthStatus.UNHEALTHY,
            "error": str(e),
            "details": "Storage check failed"
        }
        health_status = HealthStatus.UNHEALTHY
    
    return {
        "status": health_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "service": "ggnet-backend",
        "components": components
    }


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Kubernetes readiness probe endpoint"""
    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))
        
        # Check Redis connectivity
        await cache_manager.set("ready_check", "ok", expire=5)
        result = await cache_manager.get("ready_check")
        
        if result != "ok":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready"
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}"
        )


@router.get("/live", response_model=Dict[str, Any])
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/startup", response_model=Dict[str, Any])
async def startup_check():
    """Kubernetes startup probe endpoint"""
    return {
        "status": "started",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }