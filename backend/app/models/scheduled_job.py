"""
Scheduled Job models for task scheduling
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, JSON, Float  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Mapped, mapped_column, relationship  # pyright: ignore[reportMissingImports]
from sqlalchemy.sql import func  # pyright: ignore[reportMissingImports]

from app.core.database import Base


class JobType(str, Enum):
    """Job type enumeration"""
    MACHINE_ACTION = 'machine_action'
    BOOT_STATE = 'boot_state'
    SNAPSHOT = 'snapshot'
    SCRIPT = 'script'
    TRIM = 'trim'
    BACKUP = 'backup'
    CUSTOM = 'custom'


class JobStatus(str, Enum):
    """Job status enumeration"""
    ACTIVE = 'active'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class ExecutionStatus(str, Enum):
    """Job execution status"""
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class ScheduledJob(Base):
    """Scheduled job model"""
    __tablename__ = "scheduled_jobs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Job configuration
    job_type: Mapped[JobType] = mapped_column(
        SQLEnum(JobType),
        nullable=False,
        index=True
    )
    schedule: Mapped[dict] = mapped_column(JSON, nullable=False)  # Schedule configuration (cron, interval, once)
    job_data: Mapped[dict] = mapped_column(JSON, nullable=False)  # Job-specific data
    
    # Status
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus),
        default=JobStatus.ACTIVE,
        nullable=False,
        index=True
    )
    
    # Relationships
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_run: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    
    # Execution tracking
    execution_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    executions = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<ScheduledJob(id={self.id}, name='{self.name}', type='{self.job_type}', status='{self.status}')>"


class JobExecution(Base):
    """Job execution record"""
    __tablename__ = "job_executions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Relationship
    job_id: Mapped[int] = mapped_column(ForeignKey("scheduled_jobs.id"), nullable=False, index=True)
    job = relationship("ScheduledJob", back_populates="executions")
    
    # Execution details
    status: Mapped[ExecutionStatus] = mapped_column(
        SQLEnum(ExecutionStatus),
        default=ExecutionStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration: Mapped[Optional[float]] = mapped_column(Float)  # Duration in seconds
    
    # Results
    output: Mapped[Optional[dict]] = mapped_column(JSON)  # Execution output
    error: Mapped[Optional[str]] = mapped_column(Text)  # Error message if failed
    
    def __repr__(self) -> str:
        return f"<JobExecution(id={self.id}, job_id={self.job_id}, status='{self.status}')>"




