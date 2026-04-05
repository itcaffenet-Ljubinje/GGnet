"""
Boot Event model for logging network boot events
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, JSON  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Mapped, mapped_column, relationship  # pyright: ignore[reportMissingImports]
from sqlalchemy.sql import func  # pyright: ignore[reportMissingImports]

from app.core.database import Base


class BootEventType(str, Enum):
    """Boot event types"""
    DHCP_REQUEST = "dhcp_request"
    TFTP_REQUEST = "tftp_request"
    IPXE_LOAD = "ipxe_load"
    ISCSI_CONNECT = "iscsi_connect"
    ISCSI_DISCONNECT = "iscsi_disconnect"
    BOOT_SUCCESS = "boot_success"
    BOOT_FAILED = "boot_failed"
    BOOT_TIMEOUT = "boot_timeout"
    PXE_START = "pxe_start"
    PXE_END = "pxe_end"


class BootEventStatus(str, Enum):
    """Boot event status"""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    TIMEOUT = "timeout"


class BootEvent(Base):
    """Boot event model for tracking network boot process"""
    __tablename__ = "boot_events"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Machine reference
    machine_id: Mapped[Optional[int]] = mapped_column(ForeignKey("machines.id"), index=True)
    session_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sessions.id"), index=True)
    
    # Event information
    event_type: Mapped[BootEventType] = mapped_column(
        SQLEnum(BootEventType),
        nullable=False,
        index=True
    )
    status: Mapped[BootEventStatus] = mapped_column(
        SQLEnum(BootEventStatus),
        nullable=False,
        index=True
    )
    
    # Event details
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Network information
    client_ip: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 support
    server_ip: Mapped[Optional[str]] = mapped_column(String(45))
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), index=True)
    
    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Relationships
    machine = relationship("Machine", back_populates="boot_events")
    session = relationship("Session", back_populates="boot_events")
    
    def __repr__(self) -> str:
        return f"<BootEvent(id={self.id}, machine_id={self.machine_id}, event_type='{self.event_type}', status='{self.status}')>"

