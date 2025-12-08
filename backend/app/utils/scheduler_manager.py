"""
Scheduler Manager - Async version
Manages scheduled jobs, executions, and task scheduling using APScheduler
"""

import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
import pytz
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.scheduled_job import ScheduledJob, JobExecution, JobType, JobStatus, ExecutionStatus
from app.utils.snapshot_manager import SnapshotManager

logger = structlog.get_logger()


class SchedulerManager:
    """Manages scheduled jobs and executions"""
    
    def __init__(self, db: AsyncSession, websocket_manager=None):
        """
        Initialize Scheduler Manager
        
        Args:
            db: Async database session
            websocket_manager: Optional WebSocket event manager
        """
        self.db = db
        self.websocket_manager = websocket_manager
        
        # Initialize APScheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': True,
            'max_instances': 1
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=pytz.UTC
        )
        
        self.scheduler.start()
        logger.info("Scheduler Manager initialized")
    
    async def load_jobs_from_db(self):
        """Load active jobs from database and schedule them"""
        try:
            stmt = select(ScheduledJob).where(ScheduledJob.status == JobStatus.ACTIVE)
            result = await self.db.execute(stmt)
            active_jobs = result.scalars().all()
            
            for job in active_jobs:
                try:
                    await self._schedule_job(job)
                    logger.info("Loaded scheduled job", job_id=job.id, job_name=job.name)
                except Exception as e:
                    logger.error("Failed to load job", job_id=job.id, error=str(e))
        except Exception as e:
            logger.error("Failed to load jobs from database", error=str(e))
    
    async def _schedule_job(self, job: ScheduledJob):
        """Schedule a job in APScheduler"""
        job_id = f"job_{job.id}"
        
        # Remove existing job if present
        try:
            self.scheduler.remove_job(job_id)
        except Exception:
            pass
        
        # Create trigger based on schedule type
        trigger = self._create_trigger(job)
        
        if trigger:
            # Add job to scheduler
            self.scheduler.add_job(
                func=self._execute_job,
                trigger=trigger,
                id=job_id,
                args=[job.id],
                replace_existing=True,
                name=job.name
            )
            logger.info("Scheduled job", job_id=job.id, job_name=job.name)
    
    def _create_trigger(self, job: ScheduledJob):
        """Create APScheduler trigger from job schedule"""
        schedule = job.schedule if isinstance(job.schedule, dict) else json.loads(job.schedule)
        
        schedule_type = schedule.get('type', 'cron')
        
        if schedule_type == 'once':
            # One-time execution
            run_date = datetime.fromisoformat(schedule.get('run_date'))
            return DateTrigger(run_date=run_date)
        
        elif schedule_type == 'interval':
            # Interval-based (every X seconds/minutes/hours)
            interval = schedule.get('interval', {})
            return IntervalTrigger(
                seconds=interval.get('seconds', 0),
                minutes=interval.get('minutes', 0),
                hours=interval.get('hours', 0),
                days=interval.get('days', 0)
            )
        
        elif schedule_type == 'cron':
            # Cron expression
            cron_expr = schedule.get('cron', {})
            return CronTrigger(
                year=cron_expr.get('year'),
                month=cron_expr.get('month'),
                day=cron_expr.get('day'),
                week=cron_expr.get('week'),
                day_of_week=cron_expr.get('day_of_week'),
                hour=cron_expr.get('hour'),
                minute=cron_expr.get('minute'),
                second=cron_expr.get('second', 0),
                start_date=datetime.fromisoformat(schedule['start_date']) if schedule.get('start_date') else None,
                end_date=datetime.fromisoformat(schedule['end_date']) if schedule.get('end_date') else None
            )
        
        return None
    
    async def _execute_job(self, job_id: int):
        """Execute a scheduled job"""
        try:
            stmt = select(ScheduledJob).where(ScheduledJob.id == job_id)
            result = await self.db.execute(stmt)
            job = result.scalar_one_or_none()
            
            if not job:
                logger.error("Job not found", job_id=job_id)
                return
            
            if job.status != JobStatus.ACTIVE:
                logger.warning("Job is not active, skipping execution", job_id=job_id)
                return
            
            # Create execution record
            execution = JobExecution(
                job_id=job_id,
                status=ExecutionStatus.RUNNING,
            )
            self.db.add(execution)
            await self.db.commit()
            await self.db.refresh(execution)
            
            start_time = datetime.utcnow()
            
            # Execute job based on type
            result = await self._run_job_task(job, execution)
            
            # Update execution record
            end_time = datetime.utcnow()
            execution.status = ExecutionStatus.SUCCESS if result['success'] else ExecutionStatus.FAILED
            execution.completed_at = end_time
            execution.duration = (end_time - start_time).total_seconds()
            execution.output = result.get('output', {})
            execution.error = result.get('error')
            
            # Update job statistics
            job.execution_count += 1
            if result['success']:
                job.success_count += 1
            else:
                job.failure_count += 1
            job.last_run = end_time
            
            await self.db.commit()
            
            # Emit WebSocket event if available
            if self.websocket_manager:
                try:
                    await self.websocket_manager.broadcast({
                        'type': 'scheduler_job_executed',
                        'job_id': job_id,
                        'execution_id': execution.id,
                        'status': execution.status.value,
                        'duration': execution.duration
                    })
                except Exception as e:
                    logger.warning("Failed to emit WebSocket event", error=str(e))
            
            logger.info("Job executed", job_id=job_id, success=result['success'])
            
        except Exception as e:
            logger.error("Error executing job", job_id=job_id, error=str(e), exc_info=True)
            if 'execution' in locals():
                execution.status = ExecutionStatus.FAILED
                execution.error = str(e)
                execution.completed_at = datetime.utcnow()
                await self.db.commit()
    
    async def _run_job_task(self, job: ScheduledJob, execution: JobExecution) -> Dict[str, Any]:
        """Run the actual task for a job"""
        job_data = job.job_data if isinstance(job.job_data, dict) else json.loads(job.job_data)
        
        try:
            if job.job_type == JobType.MACHINE_ACTION:
                return await self._execute_machine_action(job_data)
            elif job.job_type == JobType.BOOT_STATE:
                return await self._execute_boot_state(job_data)
            elif job.job_type == JobType.SNAPSHOT:
                return await self._execute_snapshot(job_data)
            elif job.job_type == JobType.SCRIPT:
                return await self._execute_script(job_data)
            elif job.job_type == JobType.TRIM:
                return await self._execute_trim(job_data)
            elif job.job_type == JobType.BACKUP:
                return await self._execute_backup(job_data)
            else:
                return {'success': False, 'error': f'Unknown job type: {job.job_type}'}
        except Exception as e:
            logger.error("Job task execution failed", job_id=job.id, error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def _execute_machine_action(self, job_data: Dict) -> Dict[str, Any]:
        """Execute machine action (power on/off, restart, shutdown)"""
        action = job_data.get('action')
        machine_ids = job_data.get('machine_ids', [])
        
        # TODO: Integrate with machine management
        logger.info("Executing machine action", action=action, machine_count=len(machine_ids))
        return {'success': True, 'output': {'action': action, 'machines': len(machine_ids)}}
    
    async def _execute_boot_state(self, job_data: Dict) -> Dict[str, Any]:
        """Execute boot state change"""
        # TODO: Implement boot state change
        return {'success': True, 'output': {}}
    
    async def _execute_snapshot(self, job_data: Dict) -> Dict[str, Any]:
        """Execute snapshot creation"""
        try:
            snapshot_manager = SnapshotManager(self.db)
            snapshot = await snapshot_manager.create_snapshot(
                image_id=job_data.get('image_id'),
                machine_id=job_data.get('machine_id'),
                description=job_data.get('description')
            )
            return {'success': True, 'output': {'snapshot_id': snapshot.id}}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_script(self, job_data: Dict) -> Dict[str, Any]:
        """Execute script"""
        # TODO: Implement script execution with proper security
        return {'success': True, 'output': {}}
    
    async def _execute_trim(self, job_data: Dict) -> Dict[str, Any]:
        """Execute TRIM operation"""
        # TODO: Integrate with storage management
        return {'success': True, 'output': {}}
    
    async def _execute_backup(self, job_data: Dict) -> Dict[str, Any]:
        """Execute backup operation"""
        # TODO: Integrate with backup system
        return {'success': True, 'output': {}}
    
    async def create_job(
        self,
        name: str,
        job_type: JobType,
        schedule: Dict,
        job_data: Dict,
        description: Optional[str] = None,
        enabled: bool = True,
        created_by: int = 1
    ) -> ScheduledJob:
        """Create a new scheduled job"""
        job = ScheduledJob(
            name=name,
            job_type=job_type,
            schedule=schedule,
            job_data=job_data,
            description=description,
            status=JobStatus.ACTIVE if enabled else JobStatus.PAUSED,
            created_by=created_by
        )
        
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        
        if enabled:
            await self._schedule_job(job)
        
        logger.info("Created scheduled job", job_id=job.id, job_name=name)
        return job
    
    async def update_job(self, job_id: int, **kwargs) -> bool:
        """Update a scheduled job"""
        stmt = select(ScheduledJob).where(ScheduledJob.id == job_id)
        result = await self.db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return False
        
        for key, value in kwargs.items():
            if hasattr(job, key) and key not in ['schedule', 'job_data']:
                setattr(job, key, value)
        
        if 'schedule' in kwargs:
            job.schedule = kwargs['schedule']
        
        if 'job_data' in kwargs:
            job.job_data = kwargs['job_data']
        
        await self.db.commit()
        
        # Reschedule if active
        if job.status == JobStatus.ACTIVE:
            await self._schedule_job(job)
        
        logger.info("Updated scheduled job", job_id=job_id)
        return True
    
    async def delete_job(self, job_id: int) -> bool:
        """Delete a scheduled job"""
        stmt = select(ScheduledJob).where(ScheduledJob.id == job_id)
        result = await self.db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return False
        
        # Remove from scheduler
        try:
            self.scheduler.remove_job(f"job_{job_id}")
        except Exception:
            pass
        
        await self.db.delete(job)
        await self.db.commit()
        
        logger.info("Deleted scheduled job", job_id=job_id)
        return True
    
    async def pause_job(self, job_id: int) -> bool:
        """Pause a scheduled job"""
        stmt = select(ScheduledJob).where(ScheduledJob.id == job_id)
        result = await self.db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return False
        
        job.status = JobStatus.PAUSED
        await self.db.commit()
        
        # Remove from scheduler
        try:
            self.scheduler.remove_job(f"job_{job_id}")
        except Exception:
            pass
        
        logger.info("Paused scheduled job", job_id=job_id)
        return True
    
    async def resume_job(self, job_id: int) -> bool:
        """Resume a paused job"""
        stmt = select(ScheduledJob).where(ScheduledJob.id == job_id)
        result = await self.db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return False
        
        job.status = JobStatus.ACTIVE
        await self.db.commit()
        
        # Reschedule
        await self._schedule_job(job)
        
        logger.info("Resumed scheduled job", job_id=job_id)
        return True
    
    async def run_job_now(self, job_id: int) -> bool:
        """Run a job immediately"""
        stmt = select(ScheduledJob).where(ScheduledJob.id == job_id)
        result = await self.db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return False
        
        # Execute in background
        await self._execute_job(job_id)
        return True
    
    async def get_jobs(self, status: Optional[JobStatus] = None) -> List[Dict]:
        """Get list of scheduled jobs"""
        stmt = select(ScheduledJob)
        if status:
            stmt = stmt.where(ScheduledJob.status == status)
        
        stmt = stmt.order_by(ScheduledJob.created_at.desc())
        result = await self.db.execute(stmt)
        jobs = result.scalars().all()
        
        return [await self._job_to_dict(job) for job in jobs]
    
    async def get_job(self, job_id: int) -> Optional[Dict]:
        """Get a single scheduled job"""
        stmt = select(ScheduledJob).where(ScheduledJob.id == job_id)
        result = await self.db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return None
        
        return await self._job_to_dict(job)
    
    async def get_executions(self, job_id: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """Get job execution history"""
        stmt = select(JobExecution)
        if job_id:
            stmt = stmt.where(JobExecution.job_id == job_id)
        
        stmt = stmt.order_by(JobExecution.started_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        executions = result.scalars().all()
        
        return [self._execution_to_dict(exec) for exec in executions]
    
    async def _job_to_dict(self, job: ScheduledJob) -> Dict:
        """Convert job model to dictionary"""
        # Get next run time from scheduler
        next_run = None
        try:
            scheduler_job = self.scheduler.get_job(f"job_{job.id}")
            if scheduler_job and scheduler_job.next_run_time:
                next_run = scheduler_job.next_run_time.isoformat()
        except Exception:
            pass
        
        return {
            'id': job.id,
            'name': job.name,
            'job_type': job.job_type.value,
            'schedule': job.schedule,
            'job_data': job.job_data,
            'description': job.description,
            'status': job.status.value,
            'next_run': next_run,
            'last_run': job.last_run.isoformat() if job.last_run else None,
            'execution_count': job.execution_count,
            'success_count': job.success_count,
            'failure_count': job.failure_count,
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'created_by': job.created_by
        }
    
    def _execution_to_dict(self, execution: JobExecution) -> Dict:
        """Convert execution model to dictionary"""
        return {
            'id': execution.id,
            'job_id': execution.job_id,
            'status': execution.status.value,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'duration': execution.duration,
            'output': execution.output,
            'error': execution.error
        }
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler Manager shut down")




