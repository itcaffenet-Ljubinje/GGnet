"""
FastAPI dependencies for authentication and authorization
"""

from typing import Optional
from datetime import datetime
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_db
from app.core.security import verify_token, create_credentials_exception, create_permission_exception
from app.models.user import User, UserRole
from app.models.audit import AuditLog, AuditAction, AuditSeverity

logger = structlog.get_logger()

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user with token refresh support"""
    
    if not credentials:
        logger.warning("No credentials provided", ip=request.client.host)
        raise create_credentials_exception("No authentication token provided")
    
    try:
        # Verify token
        payload = await verify_token(credentials.credentials, "access")
        user_id_str = payload.get("sub")
        
        if user_id_str is None:
            raise create_credentials_exception("Invalid token payload")
        
        # Convert user_id to integer (JWT stores it as string)
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise create_credentials_exception("Invalid user ID in token")
        
        # Get user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user is None:
            logger.warning("User not found", user_id=user_id, ip=request.client.host)
            raise create_credentials_exception("User not found")
        
        if not user.is_active:
            logger.warning("Inactive user attempted access", user_id=user_id, ip=request.client.host)
            raise create_credentials_exception("Inactive user")
        
        if user.locked_until and user.locked_until > datetime.utcnow():
            logger.warning("Locked user attempted access", user_id=user_id, ip=request.client.host)
            raise create_credentials_exception("Account is locked")
        
        # Update last activity
        user.last_login = user.last_login or user.created_at
        await db.commit()
        
        return user
        
    except HTTPException as e:
        # Check if it's a token expiration error
        if "expired" in str(e.detail).lower() or "invalid token" in str(e.detail).lower():
            logger.warning("Token expired or invalid", ip=request.client.host)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired. Please refresh your token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        raise
    except Exception as e:
        logger.error("Authentication failed", error=str(e), ip=request.client.host)
        raise create_credentials_exception("Authentication failed")


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (alias for backward compatibility)"""
    return current_user


def require_role(required_role: UserRole):
    """Dependency factory for role-based access control"""
    
    async def check_role(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Check if user has required role"""
        
        # Admin can access everything
        if current_user.role == UserRole.ADMIN:
            return current_user
        
        # Check specific role requirements
        if required_role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
            logger.warning(
                "Insufficient permissions - admin required",
                user_id=current_user.id,
                user_role=current_user.role,
                required_role=required_role,
                ip=request.client.host
            )
            
            # Log security event
            audit_log = AuditLog.create_log(
                action=AuditAction.PERMISSION_DENIED,
                message=f"User {current_user.username} attempted admin action without permissions",
                user_id=current_user.id,
                username=current_user.username,
                severity=AuditSeverity.WARNING,
                ip_address=request.client.host,
                endpoint=str(request.url.path),
                http_method=request.method
            )
            db.add(audit_log)
            await db.commit()
            
            raise create_permission_exception("Admin privileges required")
        
        if required_role == UserRole.OPERATOR and current_user.role not in [UserRole.ADMIN, UserRole.OPERATOR]:
            logger.warning(
                "Insufficient permissions - operator required",
                user_id=current_user.id,
                user_role=current_user.role,
                required_role=required_role,
                ip=request.client.host
            )
            
            # Log security event
            audit_log = AuditLog.create_log(
                action=AuditAction.PERMISSION_DENIED,
                message=f"User {current_user.username} attempted operator action without permissions",
                user_id=current_user.id,
                username=current_user.username,
                severity=AuditSeverity.WARNING,
                ip_address=request.client.host,
                endpoint=str(request.url.path),
                http_method=request.method
            )
            db.add(audit_log)
            await db.commit()
            
            raise create_permission_exception("Operator privileges required")
        
        return current_user
    
    return check_role


# Convenience dependencies for common roles
require_admin = require_role(UserRole.ADMIN)
require_operator = require_role(UserRole.OPERATOR)


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    
    if not credentials:
        return None
    
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None
    except Exception:
        return None


def get_client_ip(request: Optional[Request]) -> str:
    """Get client IP address from request"""
    if request is None:
        return "127.0.0.1"  # Default for test/system calls
    
    # Check for forwarded headers first (reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Optional[Request]) -> str:
    """Get user agent from request"""
    if request is None:
        return "system"  # Default for test/system calls
    return request.headers.get("User-Agent", "unknown")


async def log_user_activity(
    action: AuditAction,
    message: str,
    request: Request,
    user: Optional[User] = None,
    severity: AuditSeverity = AuditSeverity.INFO,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    resource_name: Optional[str] = None,
    db: AsyncSession = None
):
    """Log user activity for audit purposes
    
    If db session is provided, it will be used (and not committed).
    If db session is not provided, a new session will be created and committed.
    """
    
    try:
        if db is not None:
            # Use existing session without committing
            await _log_audit_entry(
                action, message, request, user, severity, 
                resource_type, resource_id, resource_name, db, should_commit=False
            )
        else:
            # Create a new session and commit
            # Using async context manager directly instead of generator
            from app.core.database import get_async_engine
            from sqlalchemy.ext.asyncio import AsyncSession
            
            async_engine = get_async_engine()
            async with AsyncSession(async_engine) as session:
                async with session.begin():
                    await _log_audit_entry(
                        action, message, request, user, severity, 
                        resource_type, resource_id, resource_name, session, should_commit=False
                    )
                    # Commit is handled by session.begin() context manager
    except Exception as e:
        # Don't let audit logging break the main flow
        logger.error("Failed to log user activity", error=str(e), action=action)


async def _log_audit_entry(
    action: AuditAction,
    message: str,
    request: Request,
    user: Optional[User],
    severity: AuditSeverity,
    resource_type: Optional[str],
    resource_id: Optional[int],
    resource_name: Optional[str],
    db: AsyncSession,
    should_commit: bool = False
):
    """Helper function to log audit entry"""
    try:
        audit_log = AuditLog.create_log(
            action=action,
            message=message,
            user_id=user.id if user else None,
            username=user.username if user else None,
            severity=severity,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            endpoint=str(request.url.path) if request else "system",
            http_method=request.method if request else "SYSTEM"
        )
        
        db.add(audit_log)
        if should_commit:
            await db.commit()
            await db.refresh(audit_log)
        else:
            await db.flush()  # Flush but don't commit - parent will commit
    except Exception as e:
        logger.error("Failed to log audit entry", error=str(e))
        if should_commit and db:
            await db.rollback()
        # Don't raise - logging should never break the main flow
        pass
    
    logger.info(
        "User activity logged",
        action=action,
        user_id=user.id if user else None,
        username=user.username if user else None,
        ip=get_client_ip(request)
    )

