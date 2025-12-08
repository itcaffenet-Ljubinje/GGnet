"""
Batch Operation models for bulk operations on images and machines
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, JSON  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Mapped, mapped_column, relationship  # pyright: ignore[reportMissingImports]
from sqlalchemy.sql import func  # pyright: ignore[reportMissingImports]

from app.core.database import Base


class BatchOperationType(str, Enum):
    """Batch operation types"""
    # Image operations
    IMAGE_BACKUP = "image_backup"
    IMAGE_RESTORE = "image_restore"
    IMAGE_TEST = "image_test"
    
    # Machine operations
    MACHINE_RESTART = "machine_restart"
    MACHINE_SHUTDOWN = "machine_shutdown"
    MACHINE_WAKE = "machine_wake"
    MACHINE_TURN_ON = "machine_turn_on"


class BatchOperationStatus(str, Enum):
    """Batch operation status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchOperation(Base):
    """Batch operation model"""
    __tablename__ = "batch_operations"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Operation details
    operation_type: Mapped[BatchOperationType] = mapped_column(
        SQLEnum(BatchOperationType),
        nullable=False,
        index=True
    )
    status: Mapped[BatchOperationStatus] = mapped_column(
        SQLEnum(BatchOperationStatus),
        default=BatchOperationStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Progress tracking
    total_items: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_items: Mapped[int] = mapped_column(Integer, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, default=0)
    
    # Operation configuration
    config: Mapped[Optional[dict]] = mapped_column(JSON)  # Operation-specific config (backup_path, etc.)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
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
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    image_operations = relationship("BatchImageOperation", back_populates="batch_operation", cascade="all, delete-orphan")
    machine_operations = relationship("BatchMachineOperation", back_populates="batch_operation", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<BatchOperation(id={self.id}, type='{self.operation_type}', status='{self.status}')>"


class BatchImageOperation(Base):
    """Individual image operation within a batch"""
    __tablename__ = "batch_image_operations"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Relationship
    batch_operation_id: Mapped[int] = mapped_column(ForeignKey("batch_operations.id"), nullable=False, index=True)
    batch_operation = relationship("BatchOperation", back_populates="image_operations")
    
    image_id: Mapped[int] = mapped_column(ForeignKey("images.id"), nullable=False, index=True)
    image = relationship("Image")
    
    # Status
    status: Mapped[BatchOperationStatus] = mapped_column(
        SQLEnum(BatchOperationStatus),
        default=BatchOperationStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    def __repr__(self) -> str:
        return f"<BatchImageOperation(id={self.id}, batch_op_id={self.batch_operation_id}, image_id={self.image_id}, status='{self.status}')>"


class BatchMachineOperation(Base):
    """Individual machine operation within a batch"""
    __tablename__ = "batch_machine_operations"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Relationship
    batch_operation_id: Mapped[int] = mapped_column(ForeignKey("batch_operations.id"), nullable=False, index=True)
    batch_operation = relationship("BatchOperation", back_populates="machine_operations")
    
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), nullable=False, index=True)
    machine = relationship("Machine")
    
    # Status
    status: Mapped[BatchOperationStatus] = mapped_column(
        SQLEnum(BatchOperationStatus),
        default=BatchOperationStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    def __repr__(self) -> str:
        return f"<BatchMachineOperation(id={self.id}, batch_op_id={self.batch_operation_id}, machine_id={self.machine_id}, status='{self.status}')>"




