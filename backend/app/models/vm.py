"""
Virtual Machine model for QEMU/KVM VMs
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, Table, Column  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Mapped, mapped_column, relationship  # pyright: ignore[reportMissingImports]
from sqlalchemy.sql import func  # pyright: ignore[reportMissingImports]

from app.core.database import Base

# Association table for many-to-many relationship between VM and Image
vm_images = Table(
    "vm_images",
    Base.metadata,
    Column("vm_id", Integer, ForeignKey("vms.id", ondelete="CASCADE"), primary_key=True),
    Column("image_id", Integer, ForeignKey("images.id", ondelete="CASCADE"), primary_key=True),
)


class VMStatus(str, Enum):
    """VM status"""
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    ERROR = "error"


class VM(Base):
    """Virtual machine model"""
    __tablename__ = "vms"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Libvirt domain UUID
    vm_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # Image relationships
    # Legacy single image_id for backward compatibility
    image_id: Mapped[Optional[int]] = mapped_column(ForeignKey("images.id"), index=True)
    image = relationship("Image", foreign_keys=[image_id], back_populates="vms")
    
    # Many-to-many relationship for multiple images
    images: Mapped[List["Image"]] = relationship(
        "Image",
        secondary=vm_images,
        back_populates="vm_instances"
    )
    
    # Resources
    vcpus: Mapped[int] = mapped_column(Integer, default=2)
    ram_mb: Mapped[int] = mapped_column(Integer, default=4096)
    
    # Storage
    zfs_clone: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    disk_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Network
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(15), nullable=True, index=True)
    drives_connection: Mapped[str] = mapped_column(String(50), default="local")  # "local" or "network"
    iscsi_target: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Status
    status: Mapped[VMStatus] = mapped_column(
        SQLEnum(VMStatus),
        default=VMStatus.STOPPED,
        nullable=False,
        index=True
    )
    
    # VNC console
    vnc_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vnc_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Boot configuration
    boot_mode: Mapped[str] = mapped_column(String(50), default="uefi")  # "uefi" or "legacy"
    
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
    
    def __repr__(self) -> str:
        return f"<VM(id={self.id}, name='{self.name}', status='{self.status}')>"




