"""
Custom exceptions for the GGnet application
"""

from typing import Any, Dict, Optional


class GGnetException(Exception):
    """Base exception for GGnet application"""
    
    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        error_code: str = "internal_error",
        headers: Optional[Dict[str, Any]] = None
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        self.headers = headers or {}
        super().__init__(detail)


class AuthenticationError(GGnetException):
    """Authentication related errors"""
    
    def __init__(self, detail: str = "Authentication failed", **kwargs):
        super().__init__(
            detail=detail,
            status_code=401,
            error_code="authentication_error",
            **kwargs
        )


class AuthorizationError(GGnetException):
    """Authorization related errors"""
    
    def __init__(self, detail: str = "Not enough permissions", **kwargs):
        super().__init__(
            detail=detail,
            status_code=403,
            error_code="authorization_error",
            **kwargs
        )


class ValidationError(GGnetException):
    """Validation related errors"""
    
    def __init__(self, detail: str = "Validation failed", **kwargs):
        super().__init__(
            detail=detail,
            status_code=422,
            error_code="validation_error",
            **kwargs
        )


class NotFoundError(GGnetException):
    """Resource not found errors"""
    
    def __init__(self, detail: str = "Resource not found", **kwargs):
        super().__init__(
            detail=detail,
            status_code=404,
            error_code="not_found",
            **kwargs
        )


class ConflictError(GGnetException):
    """Resource conflict errors"""
    
    def __init__(self, detail: str = "Resource conflict", **kwargs):
        super().__init__(
            detail=detail,
            status_code=409,
            error_code="conflict_error",
            **kwargs
        )


class RateLimitError(GGnetException):
    """Rate limiting errors"""
    
    def __init__(self, detail: str = "Rate limit exceeded", **kwargs):
        super().__init__(
            detail=detail,
            status_code=429,
            error_code="rate_limit_exceeded",
            **kwargs
        )


class ImageError(GGnetException):
    """Image processing related errors"""
    
    def __init__(self, detail: str = "Image processing failed", **kwargs):
        super().__init__(
            detail=detail,
            status_code=400,
            error_code="image_error",
            **kwargs
        )


class iSCSIError(GGnetException):
    """iSCSI related errors"""
    
    def __init__(self, detail: str = "iSCSI operation failed", **kwargs):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code="iscsi_error",
            **kwargs
        )


class SessionError(GGnetException):
    """Session management errors"""
    
    def __init__(self, detail: str = "Session operation failed", **kwargs):
        super().__init__(
            detail=detail,
            status_code=400,
            error_code="session_error",
            **kwargs
        )


class StorageError(GGnetException):
    """Storage related errors"""
    
    def __init__(self, detail: str = "Storage operation failed", **kwargs):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code="storage_error",
            **kwargs
        )


class ConfigurationError(GGnetException):
    """Configuration related errors"""
    
    def __init__(self, detail: str = "Configuration error", **kwargs):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code="configuration_error",
            **kwargs
        )


class TargetCLIError(GGnetException):
    """targetcli related errors"""
    
    def __init__(self, detail: str = "targetcli operation failed", **kwargs):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code="targetcli_error",
            **kwargs
        )


class DHCPError(GGnetException):
    """DHCP related errors"""

    def __init__(self, detail: str = "DHCP operation failed", **kwargs):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code="dhcp_error",
            **kwargs
        )


class TFTPError(GGnetException):
    """TFTP related errors"""

    def __init__(self, detail: str = "TFTP operation failed", **kwargs):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code="tftp_error",
            **kwargs
        )