"""
Snapshot model for image snapshots
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String, Text  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Mapped, mapped_column, relationship  # pyright: ignore[reportMissingImports]
from sqlalchemy.sql import func  # pyright: ignore[reportMissingImports]

from app.core.database import Base


class RetentionPolicy(str, Enum):
    """Snapshot retention policies"""
    KEEP_ALL = "keep_all"
    KEEP_LAST_N = "keep_last_n"
    KEEP_DAILY = "keep_daily"
    KEEP_WEEKLY = "keep_weekly"
    KEEP_MONTHLY = "keep_monthly"
    KEEP_DAYS = "keep_days"


class Snapshot(Base):
    """Image snapshot model"""
    __tablename__ = "snapshots"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Relationships
    image_id: Mapped[int] = mapped_column(ForeignKey("images.id"), nullable=False, index=True)
    machine_id: Mapped[Optional[int]] = mapped_column(ForeignKey("machines.id"), index=True)
    
    # Snapshot information
    snapshot_path: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Retention policy
    retention_policy: Mapped[Optional[RetentionPolicy]] = mapped_column(
        SQLEnum(RetentionPolicy),
        nullable=True
    )
    retention_value: Mapped[Optional[int]] = mapped_column()  # N for KEEP_LAST_N, days for KEEP_DAYS
    
    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    image = relationship("Image", back_populates="snapshots")
    machine = relationship("Machine", back_populates="snapshots")
    
    def __repr__(self) -> str:
        return f"<Snapshot(id={self.id}, image_id={self.image_id}, path='{self.snapshot_path}')>"




