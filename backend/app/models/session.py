"""
Session model for tracking diskless boot sessions
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import BigInteger, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, JSON  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Mapped, mapped_column, relationship  # pyright: ignore[reportMissingImports]
from sqlalchemy.sql import func  # pyright: ignore[reportMissingImports]

from app.core.database import Base


class SessionStatus(str, Enum):
    """Session status"""
    STARTING = "starting"
    ACTIVE = "active"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    TIMEOUT = "timeout"


class SessionType(str, Enum):
    """Session type"""
    DISKLESS_BOOT = "diskless_boot"
    MAINTENANCE = "maintenance"
    TESTING = "testing"


class Session(Base):
    """Diskless boot session model"""
    __tablename__ = "sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # Session configuration
    session_type: Mapped[SessionType] = mapped_column(
        SQLEnum(SessionType),
        default=SessionType.DISKLESS_BOOT,
        nullable=False
    )
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus),
        default=SessionStatus.STARTING,
        nullable=False,
        index=True  # Index for status queries
    )
    
    # Relationships
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), nullable=False, index=True)
    machine = relationship("Machine", back_populates="sessions")
    
    target_id: Mapped[int] = mapped_column(ForeignKey("targets.id"), nullable=False, index=True)
    target = relationship("Target", back_populates="sessions")
    
    # Network information
    client_ip: Mapped[Optional[str]] = mapped_column(String(15))
    client_mac: Mapped[Optional[str]] = mapped_column(String(17))
    server_ip: Mapped[str] = mapped_column(String(15), nullable=False)
    
    # Boot information
    boot_method: Mapped[Optional[str]] = mapped_column(String(50))  # pxe, uefi, ipxe
    boot_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    os_load_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ready_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Performance metrics
    boot_duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    os_load_duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    total_startup_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Resource usage
    peak_memory_mb: Mapped[Optional[int]] = mapped_column(Integer)
    peak_cpu_percent: Mapped[Optional[float]] = mapped_column()
    network_bytes_sent: Mapped[Optional[int]] = mapped_column(BigInteger, default=0)
    network_bytes_received: Mapped[Optional[int]] = mapped_column(BigInteger, default=0)
    disk_bytes_read: Mapped[Optional[int]] = mapped_column(BigInteger, default=0)
    disk_bytes_written: Mapped[Optional[int]] = mapped_column(BigInteger, default=0)
    
    # Session timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True  # Index for time-based queries
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_code: Mapped[Optional[str]] = mapped_column(String(50))
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Configuration snapshot (JSON)
    boot_config: Mapped[Optional[dict]] = mapped_column(JSON)
    environment_vars: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # iSCSI target information
    target_iqn: Mapped[Optional[str]] = mapped_column(String(255))
    target_portal: Mapped[Optional[str]] = mapped_column(String(255))
    
    # User context
    initiated_by: Mapped[Optional[str]] = mapped_column(String(100))  # username or system
    user_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Monitoring
    health_check_interval: Mapped[int] = mapped_column(Integer, default=30)  # seconds
    last_health_check: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    health_status: Mapped[Optional[str]] = mapped_column(String(20))  # healthy, warning, critical
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, session_id='{self.session_id}', status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active"""
        return self.status == SessionStatus.ACTIVE
    
    @property
    def is_running(self) -> bool:
        """Check if session is running (starting or active)"""
        return self.status in (SessionStatus.STARTING, SessionStatus.ACTIVE)
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Get session duration in seconds"""
        if self.ended_at is None:
            if self.status in (SessionStatus.STARTING, SessionStatus.ACTIVE):
                return int((datetime.utcnow() - self.started_at).total_seconds())
            return None
        return int((self.ended_at - self.started_at).total_seconds())
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """Get session duration in minutes"""
        duration = self.duration_seconds
        return duration / 60 if duration is not None else None
    
    @property
    def network_total_mb(self) -> float:
        """Get total network usage in MB"""
        sent = self.network_bytes_sent or 0
        received = self.network_bytes_received or 0
        return (sent + received) / (1024 * 1024)
    
    @property
    def disk_total_mb(self) -> float:
        """Get total disk usage in MB"""
        read = self.disk_bytes_read or 0
        written = self.disk_bytes_written or 0
        return (read + written) / (1024 * 1024)
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def calculate_boot_performance(self):
        """Calculate boot performance metrics"""
        if self.boot_time and self.os_load_time:
            self.boot_duration_seconds = int(
                (self.os_load_time - self.boot_time).total_seconds()
            )
        
        if self.os_load_time and self.ready_time:
            self.os_load_duration_seconds = int(
                (self.ready_time - self.os_load_time).total_seconds()
            )
        
        if self.boot_time and self.ready_time:
            self.total_startup_seconds = int(
                (self.ready_time - self.boot_time).total_seconds()
            )

