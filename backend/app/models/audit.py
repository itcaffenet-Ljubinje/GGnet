"""
Audit log model for security and compliance tracking
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AuditAction(str, Enum):
    """Audit action types"""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGED = "password_changed"
    
    # User management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_LOCKED = "user_locked"
    USER_UNLOCKED = "user_unlocked"
    
    # Image management
    IMAGE_UPLOADED = "image_uploaded"
    IMAGE_DOWNLOADED = "image_downloaded"
    IMAGE_CONVERTED = "image_converted"
    IMAGE_DELETED = "image_deleted"
    IMAGE_SCANNED = "image_scanned"
    
    # Machine management
    MACHINE_CREATED = "machine_created"
    MACHINE_UPDATED = "machine_updated"
    MACHINE_DELETED = "machine_deleted"
    MACHINE_ONLINE = "machine_online"
    MACHINE_OFFLINE = "machine_offline"
    
    # Target management
    TARGET_CREATED = "target_created"
    TARGET_UPDATED = "target_updated"
    TARGET_DELETED = "target_deleted"
    TARGET_ACTIVATED = "target_activated"
    TARGET_DEACTIVATED = "target_deactivated"
    
    # Session management
    SESSION_STARTED = "session_started"
    SESSION_STOPPED = "session_stopped"
    SESSION_ERROR = "session_error"
    BOOT_INITIATED = "boot_initiated"
    BOOT_COMPLETED = "boot_completed"
    BOOT_FAILED = "boot_failed"
    
    # System operations
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    CONFIG_CHANGED = "config_changed"
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    
    # Security events
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    VIRUS_DETECTED = "virus_detected"


class AuditSeverity(str, Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(Base):
    """Audit log model for tracking all system activities"""
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Event information
    action: Mapped[AuditAction] = mapped_column(SQLEnum(AuditAction), nullable=False, index=True)
    severity: Mapped[AuditSeverity] = mapped_column(
        SQLEnum(AuditSeverity),
        default=AuditSeverity.INFO,
        nullable=False,
        index=True
    )
    
    # User context
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    user = relationship("User", back_populates="audit_logs")
    username: Mapped[Optional[str]] = mapped_column(String(50), index=True)  # Cached for deleted users
    
    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), index=True)  # IPv6 support
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    session_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Resource information
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), index=True)  # image, machine, target, etc.
    resource_id: Mapped[Optional[int]] = mapped_column(index=True)
    resource_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Event details
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON)  # Additional structured data
    
    # Request/Response information
    http_method: Mapped[Optional[str]] = mapped_column(String(10))
    endpoint: Mapped[Optional[str]] = mapped_column(String(500))
    status_code: Mapped[Optional[int]] = mapped_column()
    response_time_ms: Mapped[Optional[int]] = mapped_column()
    
    # Change tracking
    old_values: Mapped[Optional[dict]] = mapped_column(JSON)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Additional metadata
    tags: Mapped[Optional[list]] = mapped_column(JSON)  # For categorization
    correlation_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)  # For tracing related events
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', user='{self.username}', timestamp='{self.timestamp}')>"
    
    @classmethod
    def create_log(
        cls,
        action: AuditAction,
        message: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        resource_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        details: Optional[dict] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        http_method: Optional[str] = None,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        tags: Optional[list] = None,
        correlation_id: Optional[str] = None,
    ) -> "AuditLog":
        """Create a new audit log entry"""
        return cls(
            action=action,
            message=message,
            severity=severity,
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id,
            details=details,
            old_values=old_values,
            new_values=new_values,
            http_method=http_method,
            endpoint=endpoint,
            status_code=status_code,
            response_time_ms=response_time_ms,
            tags=tags,
            correlation_id=correlation_id,
        )
    
    @property
    def is_security_event(self) -> bool:
        """Check if this is a security-related event"""
        security_actions = {
            AuditAction.LOGIN_FAILED,
            AuditAction.UNAUTHORIZED_ACCESS,
            AuditAction.PERMISSION_DENIED,
            AuditAction.SUSPICIOUS_ACTIVITY,
            AuditAction.VIRUS_DETECTED,
            AuditAction.USER_LOCKED,
        }
        return self.action in security_actions
    
    @property
    def is_critical(self) -> bool:
        """Check if this is a critical event"""
        return self.severity == AuditSeverity.CRITICAL
    
    def to_dict(self) -> dict:
        """Convert audit log to dictionary"""
        return {
            "id": self.id,
            "action": self.action,
            "severity": self.severity,
            "username": self.username,
            "message": self.message,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }

