"""
Logging configuration for GGnet
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any
import structlog
from app.core.config import get_settings

settings = get_settings()


def setup_logging():
    """Setup structured logging with rotation"""
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure standard library logging
    # Create handlers
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    app_file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    app_file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    error_file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_file_handler.setLevel(logging.ERROR)
    
    # Set formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    app_file_handler.setFormatter(formatter)
    error_file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_file_handler)
    root_logger.addHandler(error_file_handler)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup audit logging
    audit_logger = logging.getLogger("audit")
    audit_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "audit.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    audit_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
    )
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False
    
    # Setup security logging
    security_logger = logging.getLogger("security")
    security_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "security.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    security_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
    )
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.INFO)
    security_logger.propagate = False
    
    # Setup performance logging
    performance_logger = logging.getLogger("performance")
    performance_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "performance.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    performance_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
    )
    performance_logger.addHandler(performance_handler)
    performance_logger.setLevel(logging.INFO)
    performance_logger.propagate = False


def get_audit_logger():
    """Get audit logger instance"""
    return logging.getLogger("audit")


def get_security_logger():
    """Get security logger instance"""
    return logging.getLogger("security")


def get_performance_logger():
    """Get performance logger instance"""
    return logging.getLogger("performance")


def log_audit_event(event_type: str, user_id: int, details: Dict[str, Any]):
    """Log audit event"""
    import datetime
    audit_logger = get_audit_logger()
    audit_logger.info(
        f"AUDIT: {event_type}",
        extra={
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    )


def log_security_event(event_type: str, details: Dict[str, Any]):
    """Log security event"""
    import datetime
    security_logger = get_security_logger()
    security_logger.warning(
        f"SECURITY: {event_type}",
        extra={
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    )


def log_performance_event(operation: str, duration_ms: float, details: Dict[str, Any]):
    """Log performance event"""
    import datetime
    performance_logger = get_performance_logger()
    performance_logger.info(
        f"PERFORMANCE: {operation}",
        extra={
            "operation": operation,
            "duration_ms": duration_ms,
            "details": details,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    )
