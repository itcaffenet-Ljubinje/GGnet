"""
Authentication endpoints with enhanced security
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict
import structlog
import json
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user, log_user_activity, get_client_ip
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token, 
    verify_token,
    revoke_token,
    revoke_user_sessions,
    get_active_sessions
)
from app.models.user import User, UserRole, UserStatus
from app.models.audit import AuditAction
from app.core.exceptions import AuthenticationError, ValidationError, NotFoundError

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
    email: str
    password: str
    role: UserRole = UserRole.VIEWER
    is_active: bool = True


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: UserRole
    status: UserStatus
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class UserSecurityInfo(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    status: UserStatus
    is_active: bool
    active_sessions: int
    last_login: Optional[datetime]
    failed_login_attempts: int
    locked_until: Optional[datetime]
    created_at: datetime


@router.post("/test-login")
async def test_login_endpoint(request: Request):
    """Test endpoint to check if auth routes work"""
    body = await request.body()
    logger.info("Test login endpoint called", body=body.decode())
    return {"message": "Test endpoint works", "body": body.decode()}

@router.post("/simple-login")
async def simple_login_endpoint(request: Request):
    """Simple login endpoint for testing"""
    try:
        body = await request.body()
        data = json.loads(body.decode())
        logger.info("Simple login called", data=data)
        
        username = data.get("username")
        password = data.get("password")
        
        if username == "admin" and password == "admin123":
            return {"message": "Login successful", "username": username}
        else:
            return {"message": "Invalid credentials", "username": username}
            
    except Exception as e:
        logger.error("Simple login error", error=str(e))
        return {"error": str(e)}

@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token"""
    
    logger.info("Login endpoint called", username=login_data.username)
    client_ip = get_client_ip(request)
    
    try:
        logger.info("Login attempt started", username=login_data.username, ip=client_ip)
        
        # Get user
        result = await db.execute(
            select(User).where(User.username == login_data.username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning("Login attempt with non-existent username", 
                          username=login_data.username, ip=client_ip)
            raise AuthenticationError("Invalid username or password")
        
        logger.info("User found", username=user.username, user_id=user.id, is_active=user.is_active, status=user.status)
        
        # Check if user is active
        if not user.is_active or user.status != UserStatus.ACTIVE:
            logger.warning("Login attempt with inactive user", 
                          username=login_data.username, ip=client_ip)
            raise AuthenticationError("Account is inactive")
        
        logger.info("User is active", username=user.username)
        
        # Check if user is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            logger.warning("Login attempt with locked user", 
                          username=login_data.username, ip=client_ip)
            raise AuthenticationError("Account is temporarily locked")
        
        logger.info("User is not locked", username=user.username)
        
        # Verify password
        logger.info("Verifying password", username=user.username)
        password_valid = verify_password(login_data.password, user.hashed_password)
        logger.info("Password verification result", username=user.username, valid=password_valid)
        
        if not password_valid:
            # Increment failed login attempts
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                logger.warning("User account locked due to failed login attempts", 
                              username=login_data.username, ip=client_ip)
            
            await db.commit()
            
            logger.warning("Failed login attempt", 
                          username=login_data.username, ip=client_ip)
            raise AuthenticationError("Invalid username or password")
        
        # Reset failed login attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        await db.commit()
        
        # Create tokens
        logger.info("Creating access token", user_id=user.id, username=user.username)
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username}
        )
        logger.info("Creating refresh token", user_id=user.id, username=user.username)
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "username": user.username}
        )
        logger.info("Tokens created successfully", user_id=user.id, username=user.username)
        
        # Log successful login
        logger.info("Logging user activity", user_id=user.id, username=user.username)
        try:
            await log_user_activity(
                action=AuditAction.LOGIN,
                message=f"User logged in successfully",
                request=request,
                user=user,
                resource_type="authentication"
            )
            logger.info("User activity logged successfully", user_id=user.id, username=user.username)
        except Exception as log_error:
            logger.warning("Failed to log user activity", error=str(log_error), user_id=user.id, username=user.username)
        
        logger.info("User logged in successfully", 
                   username=user.username, user_id=user.id, ip=client_ip)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=60 * 60  # 60 minutes
        )
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error("Login error", error=str(e), username=login_data.username, ip=client_ip, exc_info=True)
        raise AuthenticationError("Login failed")


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    try:
        # Verify refresh token
        payload = await verify_token(token_data.refresh_token, "refresh")
        user_id = int(payload.get("sub"))
        
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active or user.status != UserStatus.ACTIVE:
            raise AuthenticationError("Invalid refresh token")
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username}
        )
        
        # Log token refresh
        try:
            await log_user_activity(
                action=AuditAction.LOGIN,
                message=f"Token refreshed",
                request=request,
                user=user,
                resource_type="authentication",
                db=db
            )
        except Exception as log_error:
            logger.warning("Failed to log token refresh", error=str(log_error))
        
        logger.info("Token refreshed", user_id=user.id, username=user.username)
        
        return Token(
            access_token=access_token,
            refresh_token=token_data.refresh_token,  # Keep the same refresh token
            expires_in=60 * 60  # 60 minutes
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
    """Logout user and revoke tokens"""
    
    try:
        # Get token from request
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            
            # Revoke the token
            await revoke_token(token, "access")
        
        # Log logout
        await log_user_activity(
            action=AuditAction.LOGOUT,
            message=f"User logged out",
            request=request,
            user=current_user,
            resource_type="authentication"
        )
        
        logger.info("User logged out", username=current_user.username, user_id=current_user.id)
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error("Logout error", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin only)"""
    
    # Check if current user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Check if username already exists
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise ValidationError("Username already exists")
    
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise ValidationError("Email already exists")
    
    try:
        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            role=user_data.role,
            is_active=user_data.is_active,
            created_by=current_user.id
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Log user creation
        await log_user_activity(
            action=AuditAction.CREATE,
            message=f"Created user: {user.username}",
            request=request,
            user=current_user,
            resource_type="users"
        )
        
        logger.info("User created successfully", 
                   username=user.username, user_id=user.id, created_by=current_user.id)
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            status=user.status,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except Exception as e:
        logger.error("User creation failed", error=str(e), username=user_data.username)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User creation failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        status=current_user.status,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user information"""
    
    try:
        # Update user fields
        if user_data.email is not None:
            # Check if email already exists
            result = await db.execute(
                select(User).where(
                    User.email == user_data.email,
                    User.id != current_user.id
                )
            )
            if result.scalar_one_or_none():
                raise ValidationError("Email already exists")
            current_user.email = user_data.email
        
        await db.commit()
        await db.refresh(current_user)
        
        # Log user update
        await log_user_activity(
            action=AuditAction.UPDATE,
            message=f"Updated user profile",
            request=request,
            user=current_user,
            resource_type="users"
        )
        
        logger.info("User profile updated", user_id=current_user.id)
        
        return UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            role=current_user.role,
            status=current_user.status,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            last_login=current_user.last_login
        )
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error("User profile update failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change current user password"""
    
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise ValidationError("Current password is incorrect")
        
        # Update password
        current_user.hashed_password = get_password_hash(password_data.new_password)
        current_user.password_changed_at = datetime.utcnow()
        
        await db.commit()
        
        # Revoke all user sessions to force re-login
        await revoke_user_sessions(str(current_user.id))
        
        # Log password change
        await log_user_activity(
            action=AuditAction.UPDATE,
            message=f"Password changed",
            request=request,
            user=current_user,
            resource_type="authentication"
        )
        
        logger.info("Password changed", user_id=current_user.id)
        
        return {"message": "Password changed successfully. Please log in again."}
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error("Password change failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin only)"""
    
    # Check if current user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    
    # Log user list access
    await log_user_activity(
        action=AuditAction.LOGIN,  # Using closest available action
        message=f"Listed {len(users)} users",
        request=request,
        user=current_user,
        resource_type="users",
        db=db
    )
    
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            status=user.status,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        for user in users
    ]


@router.get("/users/{user_id}", response_model=UserSecurityInfo)
async def get_user_security_info(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user security information (admin only)"""
    
    # Check if current user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("User not found")
    
    # Get active sessions count
    active_sessions = await get_active_sessions(str(user_id))
    
    return UserSecurityInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        status=user.status,
        is_active=user.is_active,
        active_sessions=len(active_sessions),
        last_login=user.last_login,
        failed_login_attempts=user.failed_login_attempts,
        locked_until=user.locked_until,
        created_at=user.created_at
    )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user (admin only)"""
    
    # Check if current user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("User not found")
    
    try:
        # Update user fields
        if user_data.email is not None:
            # Check if email already exists
            result = await db.execute(
                select(User).where(
                    User.email == user_data.email,
                    User.id != user_id
                )
            )
            if result.scalar_one_or_none():
                raise ValidationError("Email already exists")
            user.email = user_data.email
        
        if user_data.role is not None:
            user.role = user_data.role
        
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
            # If deactivating user, revoke all sessions
            if not user_data.is_active:
                await revoke_user_sessions(str(user_id))
        
        await db.commit()
        await db.refresh(user)
        
        # Log user update
        await log_user_activity(
            action=AuditAction.UPDATE,
            message=f"Updated user: {user.username}",
            request=request,
            user=current_user,
            resource_type="users"
        )
        
        logger.info("User updated", user_id=user_id, updated_by=current_user.id)
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            status=user.status,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error("User update failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User update failed: {str(e)}"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete user (admin only)"""
    
    # Check if current user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Prevent self-deletion
    if user_id == current_user.id:
        raise ValidationError("Cannot delete your own account")
    
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("User not found")
    
    try:
        # Revoke all user sessions
        await revoke_user_sessions(str(user_id))
        
        # Delete user
        await db.delete(user)
        await db.commit()
        
        # Log user deletion
        await log_user_activity(
            action=AuditAction.DELETE,
            message=f"Deleted user: {user.username}",
            request=request,
            user=current_user,
            resource_type="users"
        )
        
        logger.info("User deleted", user_id=user_id, deleted_by=current_user.id)
        
        return {"message": "User deleted successfully"}
        
    except Exception as e:
        logger.error("User deletion failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User deletion failed: {str(e)}"
        )