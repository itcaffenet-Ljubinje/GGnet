"""
Target model for iSCSI target management
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Mapped, mapped_column, relationship  # pyright: ignore[reportMissingImports]
from sqlalchemy.sql import func  # pyright: ignore[reportMissingImports]

from app.core.database import Base


class TargetStatus(str, Enum):
    """iSCSI target status"""
    CREATING = "creating"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DELETING = "deleting"


class TargetType(str, Enum):
    """Target type"""
    SYSTEM = "system"      # System disk only
    SYSTEM_GAME = "system_game"  # System + Game disk
    GAME_ONLY = "game_only"      # Game disk only


class Target(Base):
    """iSCSI Target model"""
    __tablename__ = "targets"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # iSCSI configuration
    iqn: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    portal_ip: Mapped[str] = mapped_column(String(15), nullable=False)
    portal_port: Mapped[int] = mapped_column(Integer, default=3260, nullable=False)
    
    # Target configuration
    target_type: Mapped[TargetType] = mapped_column(
        SQLEnum(TargetType),
        default=TargetType.SYSTEM,
        nullable=False
    )
    status: Mapped[TargetStatus] = mapped_column(
        SQLEnum(TargetStatus),
        default=TargetStatus.CREATING,
        nullable=False
    )
    
    # Machine assignment
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), nullable=False)
    machine = relationship("Machine", back_populates="targets")
    
    # System image (C: drive)
    system_image_id: Mapped[int] = mapped_column(ForeignKey("images.id"), nullable=False)
    system_image = relationship("Image", back_populates="targets", foreign_keys=[system_image_id])
    
    # Optional extra disk (D: drive for games)
    extra_disk_image_id: Mapped[Optional[int]] = mapped_column(ForeignKey("images.id"))
    extra_disk_image = relationship("Image", back_populates="extra_disk_targets", foreign_keys=[extra_disk_image_id])
    extra_disk_mountpoint: Mapped[Optional[str]] = mapped_column(String(10), default="D:")
    
    # Access control
    read_only: Mapped[bool] = mapped_column(Boolean, default=False)
    authentication_required: Mapped[bool] = mapped_column(Boolean, default=False)
    chap_username: Mapped[Optional[str]] = mapped_column(String(100))
    chap_password: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Performance settings
    max_connections: Mapped[int] = mapped_column(Integer, default=1)
    block_size: Mapped[int] = mapped_column(Integer, default=512)
    cache_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Status tracking
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    last_connected: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    connection_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    sessions = relationship("Session", back_populates="target")
    
    def __repr__(self) -> str:
        return f"<Target(id={self.id}, name='{self.name}', iqn='{self.iqn}', status='{self.status}')>"
    
    @property
    def is_ready(self) -> bool:
        """Check if target is ready for connections"""
        return self.status == TargetStatus.ACTIVE and self.is_active
    
    @property
    def has_extra_disk(self) -> bool:
        """Check if target has extra disk configured"""
        return self.extra_disk_image_id is not None
    
    @property
    def portal_address(self) -> str:
        """Get full portal address"""
        return f"{self.portal_ip}:{self.portal_port}"
    
    @property
    def connection_string(self) -> str:
        """Get iSCSI connection string"""
        return f"iscsi://{self.portal_address}/{self.iqn}"
    
    @property
    def requires_auth(self) -> bool:
        """Check if target requires authentication"""
        return self.authentication_required and self.chap_username is not None
    
    def can_connect(self) -> bool:
        """Check if target can accept connections"""
        return (
            self.is_ready and 
            self.connection_count < self.max_connections and
            self.retry_count < self.max_retries
        )
    
    def get_lun_mapping(self) -> dict:
        """Get LUN mapping for target"""
        mapping = {
            0: {
                "image_id": self.system_image_id,
                "mountpoint": "C:",
                "type": "system"
            }
        }
        
        if self.has_extra_disk:
            mapping[1] = {
                "image_id": self.extra_disk_image_id,
                "mountpoint": self.extra_disk_mountpoint,
                "type": "data"
            }
        
        return mapping

