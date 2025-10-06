"""
Prometheus metrics endpoint
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
import psutil
import time
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.user import User
from app.models.machine import Machine
from app.models.image import Image
from app.models.target import Target
from app.models.session import Session

router = APIRouter()

# Simple metrics storage (in production, use prometheus_client)
_metrics = {
    "http_requests_total": 0,
    "http_request_duration_seconds": 0.0,
    "active_sessions": 0,
    "total_machines": 0,
    "total_images": 0,
    "total_targets": 0,
    "total_users": 0,
}


@router.get("/", response_class=Response)
async def prometheus_metrics(db: AsyncSession = Depends(get_db)):
    """Prometheus metrics endpoint"""
    
    # Update metrics from database
    await _update_database_metrics(db)
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Build Prometheus format metrics
    metrics_output = []
    
    # Application metrics
    metrics_output.append(f"# HELP ggnet_http_requests_total Total HTTP requests")
    metrics_output.append(f"# TYPE ggnet_http_requests_total counter")
    metrics_output.append(f"ggnet_http_requests_total {_metrics['http_requests_total']}")
    
    metrics_output.append(f"# HELP ggnet_http_request_duration_seconds HTTP request duration")
    metrics_output.append(f"# TYPE ggnet_http_request_duration_seconds histogram")
    metrics_output.append(f"ggnet_http_request_duration_seconds {_metrics['http_request_duration_seconds']}")
    
    # Database metrics
    metrics_output.append(f"# HELP ggnet_active_sessions Active sessions")
    metrics_output.append(f"# TYPE ggnet_active_sessions gauge")
    metrics_output.append(f"ggnet_active_sessions {_metrics['active_sessions']}")
    
    metrics_output.append(f"# HELP ggnet_total_machines Total machines")
    metrics_output.append(f"# TYPE ggnet_total_machines gauge")
    metrics_output.append(f"ggnet_total_machines {_metrics['total_machines']}")
    
    metrics_output.append(f"# HELP ggnet_total_images Total images")
    metrics_output.append(f"# TYPE ggnet_total_images gauge")
    metrics_output.append(f"ggnet_total_images {_metrics['total_images']}")
    
    metrics_output.append(f"# HELP ggnet_total_targets Total targets")
    metrics_output.append(f"# TYPE ggnet_total_targets gauge")
    metrics_output.append(f"ggnet_total_targets {_metrics['total_targets']}")
    
    metrics_output.append(f"# HELP ggnet_total_users Total users")
    metrics_output.append(f"# TYPE ggnet_total_users gauge")
    metrics_output.append(f"ggnet_total_users {_metrics['total_users']}")
    
    # System metrics
    metrics_output.append(f"# HELP ggnet_system_cpu_percent CPU usage percentage")
    metrics_output.append(f"# TYPE ggnet_system_cpu_percent gauge")
    metrics_output.append(f"ggnet_system_cpu_percent {cpu_percent}")
    
    metrics_output.append(f"# HELP ggnet_system_memory_percent Memory usage percentage")
    metrics_output.append(f"# TYPE ggnet_system_memory_percent gauge")
    metrics_output.append(f"ggnet_system_memory_percent {memory.percent}")
    
    metrics_output.append(f"# HELP ggnet_system_disk_percent Disk usage percentage")
    metrics_output.append(f"# TYPE ggnet_system_disk_percent gauge")
    metrics_output.append(f"ggnet_system_disk_percent {disk.percent}")
    
    metrics_output.append(f"# HELP ggnet_system_memory_bytes Memory usage in bytes")
    metrics_output.append(f"# TYPE ggnet_system_memory_bytes gauge")
    metrics_output.append(f"ggnet_system_memory_bytes {memory.used}")
    
    metrics_output.append(f"# HELP ggnet_system_disk_bytes Disk usage in bytes")
    metrics_output.append(f"# TYPE ggnet_system_disk_bytes gauge")
    metrics_output.append(f"ggnet_system_disk_bytes {disk.used}")
    
    # Timestamp
    timestamp = int(time.time() * 1000)
    metrics_output.append(f"# HELP ggnet_metrics_timestamp Metrics collection timestamp")
    metrics_output.append(f"# TYPE ggnet_metrics_timestamp gauge")
    metrics_output.append(f"ggnet_metrics_timestamp {timestamp}")
    
    return Response(
        content="\n".join(metrics_output),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


async def _update_database_metrics(db: AsyncSession):
    """Update metrics from database"""
    try:
        # Count active sessions
        result = await db.execute(
            text("SELECT COUNT(*) FROM sessions WHERE status = 'ACTIVE'")
        )
        _metrics["active_sessions"] = result.scalar() or 0
        
        # Count total machines
        result = await db.execute(text("SELECT COUNT(*) FROM machines"))
        _metrics["total_machines"] = result.scalar() or 0
        
        # Count total images
        result = await db.execute(text("SELECT COUNT(*) FROM images"))
        _metrics["total_images"] = result.scalar() or 0
        
        # Count total targets
        result = await db.execute(text("SELECT COUNT(*) FROM targets"))
        _metrics["total_targets"] = result.scalar() or 0
        
        # Count total users
        result = await db.execute(text("SELECT COUNT(*) FROM users"))
        _metrics["total_users"] = result.scalar() or 0
        
    except Exception as e:
        # Log error but don't fail the metrics endpoint
        print(f"Error updating database metrics: {e}")


def increment_request_count():
    """Increment HTTP request counter"""
    _metrics["http_requests_total"] += 1


def record_request_duration(duration: float):
    """Record HTTP request duration"""
    _metrics["http_request_duration_seconds"] = duration
