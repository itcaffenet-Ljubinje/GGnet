"""
Scheduler management routes
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import structlog

from app.core.dependencies import get_db, require_operator
from app.models.user import User
from app.models.scheduled_job import JobType, JobStatus
from app.utils.scheduler_manager import SchedulerManager
from app.utils.behavior_manager import BehaviorManager

logger = structlog.get_logger()

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class ScheduleConfig(BaseModel):
    type: str  # 'once', 'interval', 'cron'
    run_date: Optional[str] = None  # For 'once'
    interval: Optional[dict] = None  # For 'interval': {'seconds': 0, 'minutes': 0, 'hours': 0, 'days': 0}
    cron: Optional[dict] = None  # For 'cron': cron expression fields


class ScheduledJobCreate(BaseModel):
    name: str
    job_type: JobType
    schedule: ScheduleConfig
    job_data: dict
    description: Optional[str] = None
    enabled: bool = True


class ScheduledJobUpdate(BaseModel):
    name: Optional[str] = None
    schedule: Optional[ScheduleConfig] = None
    job_data: Optional[dict] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class ScheduledJobResponse(BaseModel):
    id: int
    name: str
    job_type: str
    schedule: dict
    job_data: dict
    description: Optional[str]
    status: str
    next_run: Optional[str]
    last_run: Optional[str]
    execution_count: int
    success_count: int
    failure_count: int
    created_at: str
    created_by: int


@router.get("/behaviors")
async def get_behaviors(
    current_user: User = Depends(require_operator)
):
    """Get list of available job behaviors"""
    return {"behaviors": BehaviorManager.get_behaviors()}


@router.get("/behaviors/{behavior_type}")
async def get_behavior(
    behavior_type: str,
    current_user: User = Depends(require_operator)
):
    """Get behavior metadata by type"""
    behavior = BehaviorManager.get_behavior(behavior_type)
    if not behavior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Behavior type '{behavior_type}' not found"
        )
    return behavior


@router.post("", response_model=ScheduledJobResponse)
async def create_job(
    job_data: ScheduledJobCreate,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Create a new scheduled job"""
    # Validate behavior data
    is_valid, error = BehaviorManager.validate_behavior_data(
        job_data.job_type.value,
        job_data.job_data
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    manager = SchedulerManager(db)
    
    job = await manager.create_job(
        name=job_data.name,
        job_type=job_data.job_type,
        schedule=job_data.schedule.model_dump(),
        job_data=job_data.job_data,
        description=job_data.description,
        enabled=job_data.enabled,
        created_by=current_user.id
    )
    
    job_dict = await manager._job_to_dict(job)
    return ScheduledJobResponse(**job_dict)


@router.get("", response_model=List[ScheduledJobResponse])
async def list_jobs(
    status_filter: Optional[JobStatus] = Query(None, alias="status"),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """List all scheduled jobs"""
    manager = SchedulerManager(db)
    jobs = await manager.get_jobs(status=status_filter)
    
    return [ScheduledJobResponse(**job) for job in jobs]


@router.get("/{job_id}", response_model=ScheduledJobResponse)
async def get_job(
    job_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Get a single scheduled job"""
    manager = SchedulerManager(db)
    job = await manager.get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    
    return ScheduledJobResponse(**job)


@router.put("/{job_id}", response_model=ScheduledJobResponse)
async def update_job(
    job_id: int,
    job_update: ScheduledJobUpdate,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Update a scheduled job"""
    manager = SchedulerManager(db)
    
    update_data = {}
    if job_update.name is not None:
        update_data['name'] = job_update.name
    if job_update.schedule is not None:
        update_data['schedule'] = job_update.schedule.model_dump()
    if job_update.job_data is not None:
        update_data['job_data'] = job_update.job_data
    if job_update.description is not None:
        update_data['description'] = job_update.description
    if job_update.enabled is not None:
        from app.models.scheduled_job import JobStatus
        update_data['status'] = JobStatus.ACTIVE if job_update.enabled else JobStatus.PAUSED
    
    success = await manager.update_job(job_id, **update_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    
    job = await manager.get_job(job_id)
    return ScheduledJobResponse(**job)


@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Delete a scheduled job"""
    manager = SchedulerManager(db)
    success = await manager.delete_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    
    return {"message": "Job deleted", "job_id": job_id}


@router.post("/{job_id}/pause")
async def pause_job(
    job_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Pause a scheduled job"""
    manager = SchedulerManager(db)
    success = await manager.pause_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    
    return {"message": "Job paused", "job_id": job_id}


@router.post("/{job_id}/resume")
async def resume_job(
    job_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Resume a paused job"""
    manager = SchedulerManager(db)
    success = await manager.resume_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    
    return {"message": "Job resumed", "job_id": job_id}


@router.post("/{job_id}/run-now")
async def run_job_now(
    job_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Run a job immediately"""
    manager = SchedulerManager(db)
    success = await manager.run_job_now(job_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    
    return {"message": "Job execution started", "job_id": job_id}


@router.get("/executions/all")
async def get_all_executions(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Get all job executions"""
    manager = SchedulerManager(db)
    executions = await manager.get_executions(limit=limit)
    
    return {"executions": executions}


@router.get("/{job_id}/executions")
async def get_job_executions(
    job_id: int,
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Get execution history for a job"""
    manager = SchedulerManager(db)
    executions = await manager.get_executions(job_id=job_id, limit=limit)
    
    return {"job_id": job_id, "executions": executions}




