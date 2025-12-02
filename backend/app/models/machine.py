"""
Machine model for client computers
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, String, Text, JSON  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Mapped, mapped_column, relationship  # pyright: ignore[reportMissingImports]
from sqlalchemy.sql import func  # pyright: ignore[reportMissingImports]

from app.core.database import Base


class MachineStatus(str, Enum):
    """Machine status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class BootMode(str, Enum):
    """Boot mode configuration"""
    LEGACY = "legacy"
    UEFI = "uefi"
    UEFI_SECURE = "uefi_secure"


class Machine(Base):
    """Client machine model"""
    __tablename__ = "machines"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Network identification
    mac_address: Mapped[str] = mapped_column(String(17), unique=True, nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(15), index=True)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    # Hardware information
    cpu_info: Mapped[Optional[str]] = mapped_column(String(500))
    memory_mb: Mapped[Optional[int]] = mapped_column()
    disk_info: Mapped[Optional[str]] = mapped_column(Text)
    gpu_info: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Boot configuration
    boot_mode: Mapped[BootMode] = mapped_column(
        SQLEnum(BootMode),
        default=BootMode.UEFI,
        nullable=False
    )
    secure_boot_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    uefi_firmware: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Network boot settings
    pxe_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    ipxe_script_url: Mapped[Optional[str]] = mapped_column(String(500))
    boot_priority: Mapped[int] = mapped_column(default=0)  # Higher = more priority
    
    # Status and management
    status: Mapped[MachineStatus] = mapped_column(
        SQLEnum(MachineStatus),
        default=MachineStatus.ACTIVE,
        nullable=False,
        index=True  # Index for status queries
    )
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    last_boot: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Location and organization
    location: Mapped[Optional[str]] = mapped_column(String(255))
    room: Mapped[Optional[str]] = mapped_column(String(100))
    rack_position: Mapped[Optional[str]] = mapped_column(String(50))
    asset_tag: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Configuration
    auto_boot: Mapped[bool] = mapped_column(Boolean, default=True)
    wake_on_lan: Mapped[bool] = mapped_column(Boolean, default=False)
    power_management: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Custom configuration (JSON field for flexibility)
    custom_config: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Relationships
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_by_user = relationship("User", back_populates="created_machines", foreign_keys=[created_by])
    
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
    
    # Usage tracking
    boot_count: Mapped[int] = mapped_column(default=0)
    total_uptime_hours: Mapped[int] = mapped_column(default=0)
    
    # Notes and maintenance
    notes: Mapped[Optional[str]] = mapped_column(Text)
    maintenance_notes: Mapped[Optional[str]] = mapped_column(Text)
    next_maintenance: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    targets = relationship("Target", back_populates="machine")
    sessions = relationship("Session", back_populates="machine")
    
    def __repr__(self) -> str:
        return f"<Machine(id={self.id}, name='{self.name}', mac='{self.mac_address}', status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if machine is active"""
        return self.status == MachineStatus.ACTIVE
    
    @property
    def supports_secure_boot(self) -> bool:
        """Check if machine supports secure boot"""
        return self.boot_mode in (BootMode.UEFI, BootMode.UEFI_SECURE)
    
    @property
    def requires_secure_boot(self) -> bool:
        """Check if machine requires secure boot"""
        return self.boot_mode == BootMode.UEFI_SECURE and self.secure_boot_enabled
    
    @property
    def formatted_mac(self) -> str:
        """Get formatted MAC address"""
        return self.mac_address.upper().replace("-", ":")
    
    @property
    def memory_gb(self) -> Optional[float]:
        """Get memory in GB"""
        if self.memory_mb is None:
            return None
        return self.memory_mb / 1024
    
    def can_boot_image(self, image) -> bool:
        """Check if machine can boot given image"""
        # Add logic to check compatibility
        # For now, just check if machine is active
        return self.is_active

