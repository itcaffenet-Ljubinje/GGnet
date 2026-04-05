"""
Server monitoring and information endpoints
Provides server status, RAM usage, services status, and other server information
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
import platform
import psutil
from datetime import datetime

from app.core.dependencies import get_db, get_current_user, require_operator
from app.models.user import User
from app.utils.service_monitor import ServiceMonitor
from app.utils.memory_monitor import MemoryMonitor

router = APIRouter(prefix="/server", tags=["server"])
logger = structlog.get_logger()

# Initialize monitors
service_monitor = ServiceMonitor()
memory_monitor = MemoryMonitor()


@router.get("", response_model=Dict[str, Any])
async def get_server_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get server information
    """
    try:
        # Get system information
        system_info = {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "uptime_seconds": int((datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds()),
        }
        
        # Get CPU info
        cpu_info = {
            "count_physical": psutil.cpu_count(logical=False),
            "count_logical": psutil.cpu_count(logical=True),
            "percent": psutil.cpu_percent(interval=0.1),
            "per_cpu_percent": psutil.cpu_percent(interval=0.1, percpu=True),
        }
        
        # Get memory info using free -b
        try:
            memory_info = memory_monitor.get_memory_info()
        except Exception as e:
            logger.warning("Failed to get memory info with free -b, using psutil", error=str(e))
            mem = psutil.virtual_memory()
            memory_info = {
                "total_bytes": mem.total,
                "used_bytes": mem.used,
                "free_bytes": mem.free,
                "available_bytes": mem.available,
                "used_percent": mem.percent,
                "available": True
            }
        
        # Get disk info
        disk = psutil.disk_usage('/')
        disk_info = {
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
            "percent": disk.percent,
        }
        
        return {
            "system": system_info,
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get server info", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server info: {str(e)}"
        )


@router.get("/ram", response_model=Dict[str, Any])
async def get_server_ram(
    current_user: User = Depends(get_current_user)
):
    """
    Get server RAM usage using free -b command (matching ggRock implementation)
    """
    try:
        memory_info = memory_monitor.get_memory_info()
        return memory_info
    except Exception as e:
        logger.error("Failed to get RAM info", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get RAM info: {str(e)}"
        )


@router.get("/services", response_model=List[Dict[str, Any]])
async def get_server_services(
    current_user: User = Depends(require_operator)
):
    """
    Get status of system services using systemctl show
    """
    try:
        services = service_monitor.list_services()
        return services
    except Exception as e:
        logger.error("Failed to get services status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get services status: {str(e)}"
        )


@router.get("/services/{service_name}", response_model=Dict[str, Any])
async def get_service_status(
    service_name: str,
    current_user: User = Depends(require_operator)
):
    """
    Get detailed status of a specific service
    """
    try:
        status_info = service_monitor.get_service_status(service_name)
        return status_info
    except Exception as e:
        logger.error("Failed to get service status", service=service_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service status: {str(e)}"
        )


@router.post("/services/{service_name}/restart", response_model=Dict[str, Any])
async def restart_service(
    service_name: str,
    current_user: User = Depends(require_operator)
):
    """
    Restart a systemd service
    """
    try:
        success = service_monitor.restart_service(service_name)
        if success:
            return {
                "service": service_name,
                "status": "restarted",
                "message": f"Service {service_name} restarted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to restart service {service_name}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to restart service", service=service_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart service: {str(e)}"
        )

