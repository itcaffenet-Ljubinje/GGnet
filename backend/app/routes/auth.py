"""
Authentication and authorization endpoints
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
import structlog

from app.core.database import get_db
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    verify_token,
    validate_password_strength,
    rate_limiter
)
from app.core.dependencies import get_current_user, get_client_ip, get_user_agent
from app.models.user import User, UserRole, UserStatus
from app.models.audit import AuditLog, AuditAction, AuditSeverity
from app.core.exceptions import AuthenticationError, ValidationError, RateLimitError

router = APIRouter()
logger = structlog.get_logger()


# Pydantic models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: str
    role: UserRole = UserRole.VIEWER


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    status: Optional[UserStatus] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    role: UserRole
    status: UserStatus
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT tokens"""
    
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Rate limiting
    rate_key = f"login:{client_ip}"
    if not rate_limiter.is_allowed(rate_key, max_attempts=5, window_minutes=15):
        logger.warning("Login rate limit exceeded", ip=client_ip)
        
        # Log security event
        audit_log = AuditLog.create_log(
            action=AuditAction.LOGIN_FAILED,
            message=f"Rate limit exceeded for IP {client_ip}",
            severity=AuditSeverity.WARNING,
            ip_address=client_ip,
            user_agent=user_agent,
            endpoint="/auth/login",
            http_method="POST"
        )
        db.add(audit_log)
        await db.commit()
        
        raise RateLimitError("Too many login attempts. Please try again later.")
    
    # Get user
    result = await db.execute(
        select(User).where(User.username == user_credentials.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        logger.warning(
            "Login failed - invalid credentials",
            username=user_credentials.username,
            ip=client_ip
        )
        
        # Increment failed attempts if user exists
        if user:
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                logger.warning(
                    "User account locked due to failed attempts",
                    user_id=user.id,
                    username=user.username
                )
        
        # Log failed login
        audit_log = AuditLog.create_log(
            action=AuditAction.LOGIN_FAILED,
            message=f"Failed login attempt for username: {user_credentials.username}",
            user_id=user.id if user else None,
            username=user_credentials.username,
            severity=AuditSeverity.WARNING,
            ip_address=client_ip,
            user_agent=user_agent,
            endpoint="/auth/login",
            http_method="POST"
        )
        db.add(audit_log)
        await db.commit()
        
        raise AuthenticationError("Invalid username or password")
    
    # Check account status
    if not user.is_active or user.status != UserStatus.ACTIVE:
        logger.warning("Login failed - inactive account", user_id=user.id, username=user.username)
        
        audit_log = AuditLog.create_log(
            action=AuditAction.LOGIN_FAILED,
            message=f"Login attempt on inactive account: {user.username}",
            user_id=user.id,
            username=user.username,
            severity=AuditSeverity.WARNING,
            ip_address=client_ip,
            user_agent=user_agent
        )
        db.add(audit_log)
        await db.commit()
        
        raise AuthenticationError("Account is inactive")
    
    if user.is_locked:
        logger.warning("Login failed - locked account", user_id=user.id, username=user.username)
        
        audit_log = AuditLog.create_log(
            action=AuditAction.LOGIN_FAILED,
            message=f"Login attempt on locked account: {user.username}",
            user_id=user.id,
            username=user.username,
            severity=AuditSeverity.WARNING,
            ip_address=client_ip,
            user_agent=user_agent
        )
        db.add(audit_log)
        await db.commit()
        
        raise AuthenticationError("Account is locked. Please contact administrator.")
    
    # Successful login
    user.last_login = datetime.utcnow()
    user.failed_login_attempts = 0
    user.locked_until = None
    
    # Reset rate limiting for successful login
    rate_limiter.reset(rate_key)
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id), "username": user.username})
    refresh_token = create_refresh_token(data={"sub": str(user.id), "username": user.username})
    
    # Log successful login
    audit_log = AuditLog.create_log(
        action=AuditAction.LOGIN,
        message=f"User {user.username} logged in successfully",
        user_id=user.id,
        username=user.username,
        severity=AuditSeverity.INFO,
        ip_address=client_ip,
        user_agent=user_agent,
        endpoint="/auth/login",
        http_method="POST"
    )
    db.add(audit_log)
    await db.commit()
    
    logger.info("User logged in successfully", user_id=user.id, username=user.username, ip=client_ip)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60  # 30 minutes
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    try:
        # Verify refresh token
        payload = verify_token(token_data.refresh_token, "refresh")
        user_id = int(payload.get("sub"))
        
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active or user.status != UserStatus.ACTIVE:
            raise AuthenticationError("Invalid refresh token")
        
        # Create new access token
        access_token = create_access_token(data={"sub": str(user.id), "username": user.username})
        
        logger.info("Token refreshed", user_id=user.id, username=user.username)
        
        return Token(
            access_token=access_token,
            refresh_token=token_data.refresh_token,  # Keep the same refresh token
            expires_in=30 * 60  # 30 minutes
        )
        
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise AuthenticationError("Invalid refresh token")


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout user (client should discard tokens)"""
    
    # Log logout
    audit_log = AuditLog.create_log(
        action=AuditAction.LOGOUT,
        message=f"User {current_user.username} logged out",
        user_id=current_user.id,
        username=current_user.username,
        severity=AuditSeverity.INFO,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        endpoint="/auth/logout",
        http_method="POST"
    )
    db.add(audit_log)
    await db.commit()
    
    logger.info("User logged out", user_id=current_user.id, username=current_user.username)
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        logger.warning("Password change failed - invalid current password", user_id=current_user.id)
        raise AuthenticationError("Invalid current password")
    
    # Validate new password strength
    if not validate_password_strength(password_data.new_password):
        raise ValidationError(
            "Password must be at least 8 characters long and contain at least 3 of: "
            "uppercase letters, lowercase letters, numbers, special characters"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.password_changed_at = datetime.utcnow()
    
    # Log password change
    audit_log = AuditLog.create_log(
        action=AuditAction.PASSWORD_CHANGED,
        message=f"User {current_user.username} changed password",
        user_id=current_user.id,
        username=current_user.username,
        severity=AuditSeverity.INFO,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    db.add(audit_log)
    await db.commit()
    
    logger.info("Password changed successfully", user_id=current_user.id, username=current_user.username)
    
    return {"message": "Password changed successfully"}

