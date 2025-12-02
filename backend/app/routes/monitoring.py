"""
Performance monitoring endpoints
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel
import structlog
import psutil
import asyncio
from pathlib import Path

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_operator
from app.models.user import User
from app.models.image import Image
from app.models.machine import Machine
from app.models.target import Target
from app.models.session import Session, SessionStatus
from app.models.audit import AuditLog
from app.core.config import get_settings

router = APIRouter()
logger = structlog.get_logger()
settings = get_settings()


# Pydantic models
class SystemStats(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    load_average: List[float]
    uptime_seconds: int


class DatabaseStats(BaseModel):
    total_images: int
    total_machines: int
    total_targets: int
    active_sessions: int
    total_users: int
    database_size_mb: float


class SessionStats(BaseModel):
    total_sessions: int
    active_sessions: int
    average_boot_time: float
    success_rate: float
    sessions_by_status: Dict[str, int]


class PerformanceMetrics(BaseModel):
    system: SystemStats
    database: DatabaseStats
    sessions: SessionStats
    timestamp: datetime


@router.get("/metrics", response_model=PerformanceMetrics)
async def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive performance metrics"""
    
    # System stats - optimized for speed
    cpu_percent = psutil.cpu_percent(interval=0.1)  # Reduced from 1 second to 0.1 seconds
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    network_io = psutil.net_io_counters()._asdict()
    
    # Load average (Unix only)
    try:
        load_avg = list(psutil.getloadavg())
    except AttributeError:
        load_avg = [0.0, 0.0, 0.0]
    
    # Uptime
    uptime_seconds = int((datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds())
    
    system_stats = SystemStats(
        cpu_percent=cpu_percent,
        memory_percent=memory.percent,
        disk_percent=disk.percent,
        network_io=network_io,
        load_average=load_avg,
        uptime_seconds=uptime_seconds
    )
    
    # Database stats
    images_count = await db.scalar(select(func.count(Image.id)))
    machines_count = await db.scalar(select(func.count(Machine.id)))
    targets_count = await db.scalar(select(func.count(Target.id)))
    active_sessions_count = await db.scalar(
        select(func.count(Session.id)).where(
            Session.status.in_([SessionStatus.STARTING, SessionStatus.ACTIVE])
        )
    )
    users_count = await db.scalar(select(func.count(User.id)))
    
    # Database size estimation
    db_size_mb = 0.0
    try:
        if settings.DATABASE_URL.startswith('sqlite'):
            db_file = Path(settings.DATABASE_URL.replace('sqlite:///', ''))
            if db_file.exists():
                db_size_mb = db_file.stat().st_size / (1024 * 1024)
        # For PostgreSQL, we'd need a different approach
    except Exception:
        pass
    
    database_stats = DatabaseStats(
        total_images=images_count or 0,
        total_machines=machines_count or 0,
        total_targets=targets_count or 0,
        active_sessions=active_sessions_count or 0,
        total_users=users_count or 0,
        database_size_mb=db_size_mb
    )
    
    # Session stats
    total_sessions = await db.scalar(select(func.count(Session.id)))
    
    # Average boot time (for successful sessions)
    avg_boot_time_result = await db.execute(
        select(func.avg(Session.boot_duration_seconds)).where(
            and_(
                Session.boot_duration_seconds.isnot(None),
                Session.status == SessionStatus.STOPPED
            )
        )
    )
    avg_boot_time = avg_boot_time_result.scalar() or 0.0
    
    # Success rate
    successful_sessions = await db.scalar(
        select(func.count(Session.id)).where(Session.status == SessionStatus.STOPPED)
    )
    success_rate = (successful_sessions / total_sessions * 100) if total_sessions > 0 else 0.0
    
    # Sessions by status
    sessions_by_status_result = await db.execute(
        select(Session.status, func.count(Session.id))
        .group_by(Session.status)
    )
    sessions_by_status = {row[0]: row[1] for row in sessions_by_status_result.fetchall()}
    
    session_stats = SessionStats(
        total_sessions=total_sessions or 0,
        active_sessions=active_sessions_count or 0,
        average_boot_time=avg_boot_time,
        success_rate=success_rate,
        sessions_by_status=sessions_by_status
    )
    
    return PerformanceMetrics(
        system=system_stats,
        database=database_stats,
        sessions=session_stats,
        timestamp=datetime.now()
    )


@router.get("/health/detailed")
async def get_detailed_health(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed health information"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(),
        "checks": {}
    }
    
    # Database connectivity check
    try:
        await db.execute(select(1))
        health_status["checks"]["database"] = {"status": "healthy", "message": "Database connection OK"}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "message": str(e)}
        health_status["status"] = "unhealthy"
    
    # Disk space check
    try:
        disk = psutil.disk_usage('/')
        if disk.percent > 90:
            health_status["checks"]["disk_space"] = {"status": "warning", "message": f"Disk usage: {disk.percent}%"}
        else:
            health_status["checks"]["disk_space"] = {"status": "healthy", "message": f"Disk usage: {disk.percent}%"}
    except Exception as e:
        health_status["checks"]["disk_space"] = {"status": "unhealthy", "message": str(e)}
    
    # Memory check
    try:
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            health_status["checks"]["memory"] = {"status": "warning", "message": f"Memory usage: {memory.percent}%"}
        else:
            health_status["checks"]["memory"] = {"status": "healthy", "message": f"Memory usage: {memory.percent}%"}
    except Exception as e:
        health_status["checks"]["memory"] = {"status": "unhealthy", "message": str(e)}
    
    # Check for stuck sessions
    try:
        stuck_sessions = await db.scalar(
            select(func.count(Session.id)).where(
                and_(
                    Session.status == SessionStatus.STARTING,
                    Session.started_at < datetime.now() - timedelta(minutes=10)
                )
            )
        )
        if stuck_sessions > 0:
            health_status["checks"]["sessions"] = {"status": "warning", "message": f"{stuck_sessions} stuck sessions"}
        else:
            health_status["checks"]["sessions"] = {"status": "healthy", "message": "No stuck sessions"}
    except Exception as e:
        health_status["checks"]["sessions"] = {"status": "unhealthy", "message": str(e)}
    
    return health_status


@router.get("/logs/recent")
async def get_recent_logs(
    limit: int = 100,
    level: Optional[str] = None,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Get recent audit logs"""
    
    query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    
    if level:
        query = query.where(AuditLog.severity == level)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp,
            "severity": log.severity,
            "action": log.action,
            "message": log.message,
            "user": log.user.username if log.user else None,
            "ip_address": log.ip_address,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id
        }
        for log in logs
    ]


@router.get("/sessions/active")
async def get_active_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get currently active sessions with detailed info"""
    
    result = await db.execute(
        select(Session, Machine, Target)
        .join(Machine, Session.machine_id == Machine.id)
        .join(Target, Session.target_id == Target.id)
        .where(Session.status.in_([SessionStatus.STARTING, SessionStatus.ACTIVE]))
        .order_by(Session.started_at.desc())
    )
    
    sessions = []
    for session, machine, target in result.fetchall():
        sessions.append({
            "session_id": session.session_id,
            "status": session.status,
            "started_at": session.started_at,
            "boot_time": session.boot_time,
            "machine": {
                "name": machine.name,
                "mac_address": machine.mac_address,
                "ip_address": machine.ip_address
            },
            "target": {
                "name": target.name,
                "iqn": target.iqn
            },
            "client_ip": session.client_ip,
            "server_ip": session.server_ip,
            "boot_method": session.boot_method,
            "target_iqn": session.target_iqn,
            "target_portal": session.target_portal
        })
    
    return sessions
