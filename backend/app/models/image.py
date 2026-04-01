"""
Image model for VHD/VHDX disk images
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from sqlalchemy import BigInteger, Boolean, DateTime, Enum as SQLEnum, ForeignKey, String, Text  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Mapped, mapped_column, relationship  # pyright: ignore[reportMissingImports]
from sqlalchemy.sql import func  # pyright: ignore[reportMissingImports]

from app.core.database import Base


class ImageFormat(str, Enum):
    """Supported image formats"""
    VHD = "vhd"
    VHDX = "vhdx"
    RAW = "raw"
    QCOW2 = "qcow2"
    VMDK = "vmdk"
    VDI = "vdi"


class ImageStatus(str, Enum):
    """Image processing status"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    CONVERTING = "converting"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"


class ImageType(str, Enum):
    """Image type classification"""
    SYSTEM = "system"  # OS images
    APPLICATION = "application"  # Application images
    GAME = "game"      # Game disk images
    DATA = "data"      # Data disk images
    TEMPLATE = "template"  # Template images


class Image(Base):
    """Disk image model"""
    __tablename__ = "images"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # File information
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Image properties
    format: Mapped[ImageFormat] = mapped_column(SQLEnum(ImageFormat), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    virtual_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger)
    compressed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Status and processing
    status: Mapped[ImageStatus] = mapped_column(
        SQLEnum(ImageStatus), 
        default=ImageStatus.UPLOADING,
        nullable=False,
        index=True  # Index for status queries
    )
    image_type: Mapped[ImageType] = mapped_column(
        SQLEnum(ImageType),
        default=ImageType.SYSTEM,
        nullable=False,
        index=True  # Index for type-based queries
    )
    
    # Security and validation
    checksum_md5: Mapped[Optional[str]] = mapped_column(String(32))
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64))
    virus_scanned: Mapped[bool] = mapped_column(Boolean, default=False)
    virus_scan_result: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Metadata
    os_type: Mapped[Optional[str]] = mapped_column(String(50))  # windows11, ubuntu, etc.
    os_version: Mapped[Optional[str]] = mapped_column(String(100))
    architecture: Mapped[Optional[str]] = mapped_column(String(20))  # x64, arm64
    
    # Usage tracking
    download_count: Mapped[int] = mapped_column(default=0)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Foreign keys
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    converted_from_id: Mapped[Optional[int]] = mapped_column(ForeignKey("images.id"))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True  # Index for time-based queries
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Processing info
    processing_log: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships (all relationships must be defined after all columns)
    vms = relationship("VM", foreign_keys="[VM.image_id]", back_populates="image", cascade="all, delete-orphan")
    vm_instances = relationship("VM", secondary="vm_images", back_populates="images")
    machine_instances = relationship("Machine", secondary="machine_images", back_populates="images")
    created_by_user = relationship("User", back_populates="created_images", foreign_keys=[created_by])
    converted_from = relationship("Image", remote_side=[id], backref="conversions")
    targets = relationship("Target", back_populates="image")
    writebacks = relationship("Writeback", back_populates="image", cascade="all, delete-orphan")
    snapshots = relationship("Snapshot", back_populates="image", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Image(id={self.id}, name='{self.name}', format='{self.format}', status='{self.status}')>"
    
    @property
    def file_exists(self) -> bool:
        """Check if image file exists on disk"""
        return Path(self.file_path).exists()
    
    @property
    def size_mb(self) -> float:
        """Get size in MB"""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def size_gb(self) -> float:
        """Get size in GB"""
        return self.size_bytes / (1024 * 1024 * 1024)
    
    @property
    def is_ready(self) -> bool:
        """Check if image is ready for use"""
        return self.status == ImageStatus.READY
    
    @property
    def is_system_image(self) -> bool:
        """Check if this is a system/OS image"""
        return self.image_type == ImageType.SYSTEM
    
    @property
    def can_be_system_disk(self) -> bool:
        """Check if image can be used as system disk"""
        return self.image_type in (ImageType.SYSTEM, ImageType.TEMPLATE)

