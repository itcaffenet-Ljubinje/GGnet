"""
Security utilities for authentication and authorization
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import secrets
import structlog
import asyncio

from app.core.config import get_settings
from app.core.cache import cache_manager

logger = structlog.get_logger()

# Password hashing
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception:
    # Fallback for CI environments where bcrypt binding may fail
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Get settings
settings = get_settings()


class SecurityError(Exception):
    """Base security exception"""
    pass


class TokenError(SecurityError):
    """Token-related errors"""
    pass


class PasswordError(SecurityError):
    """Password-related errors"""
    pass


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error("Password verification failed", error=str(e))
        return False


def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Ensure password is not too long for bcrypt (max 72 bytes)
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error("Password hashing failed", error=str(e))
        # Attempt fallback scheme explicitly
        try:
            fallback_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
            hashed = fallback_ctx.hash(password)
            logger.warning("Used fallback password hashing (pbkdf2_sha256)")
            return hashed
        except Exception as e2:
            logger.error("Fallback password hashing failed", error=str(e2))
            raise PasswordError("Failed to hash password")


def validate_password_strength(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return sum([has_upper, has_lower, has_digit, has_special]) >= 3


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with Redis session storage"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add token metadata
    token_id = secrets.token_urlsafe(32)
    to_encode.update({
        "exp": expire, 
        "type": "access",
        "jti": token_id,  # JWT ID for tracking
        "iat": datetime.utcnow(),  # Issued at
        "iss": "ggnet"  # Issuer
    })
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        
        # Store token in Redis for session management
        session_data = {
            "user_id": data.get("sub"),
            "username": data.get("username"),
            "token_type": "access",
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expire.isoformat(),
            "is_active": True
        }
        
        # Cache token session (async operation)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, create a task
                asyncio.create_task(
                    cache_manager.set(f"session:{token_id}", session_data, ttl=int(expires_delta.total_seconds()) if expires_delta else settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
                )
            else:
                # If we're not in an async context, run it directly
                loop.run_until_complete(
                    cache_manager.set(f"session:{token_id}", session_data, ttl=int(expires_delta.total_seconds()) if expires_delta else settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
                )
        except Exception as cache_error:
            logger.warning("Failed to cache token session", error=str(cache_error))
        
        logger.info("Access token created", user_id=data.get("sub"), token_id=token_id, expires_at=expire)
        return encoded_jwt
    except Exception as e:
        logger.error("Failed to create access token", error=str(e))
        raise TokenError("Failed to create access token")


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token with Redis session storage"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Add token metadata
    token_id = secrets.token_urlsafe(32)
    to_encode.update({
        "exp": expire, 
        "type": "refresh",
        "jti": token_id,  # JWT ID for tracking
        "iat": datetime.utcnow(),  # Issued at
        "iss": "ggnet"  # Issuer
    })
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        
        # Store refresh token in Redis
        refresh_data = {
            "user_id": data.get("sub"),
            "username": data.get("username"),
            "token_type": "refresh",
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expire.isoformat(),
            "is_active": True,
            "access_tokens": []  # Track associated access tokens
        }
        
        # Cache refresh token session
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, create a task
                asyncio.create_task(
                    cache_manager.set(f"refresh:{token_id}", refresh_data, ttl=int(expires_delta.total_seconds()) if expires_delta else settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
                )
            else:
                # If we're not in an async context, run it directly
                loop.run_until_complete(
                    cache_manager.set(f"refresh:{token_id}", refresh_data, ttl=int(expires_delta.total_seconds()) if expires_delta else settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
                )
        except Exception as cache_error:
            logger.warning("Failed to cache refresh token session", error=str(cache_error))
        
        logger.info("Refresh token created", user_id=data.get("sub"), token_id=token_id, expires_at=expire)
        return encoded_jwt
    except Exception as e:
        logger.error("Failed to create refresh token", error=str(e))
        raise TokenError("Failed to create refresh token")


async def verify_token(token: str, token_type: str = "access") -> dict:
    """Verify and decode JWT token with Redis session validation"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Verify token type
        if payload.get("type") != token_type:
            raise TokenError(f"Invalid token type. Expected {token_type}")
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None:
            raise TokenError("Token missing expiration")
        
        if datetime.utcnow() > datetime.fromtimestamp(exp):
            raise TokenError("Token has expired")
        
        # Validate session in Redis
        token_id = payload.get("jti")
        if token_id:
            cache_key = f"session:{token_id}" if token_type == "access" else f"refresh:{token_id}"
            session_data = await cache_manager.get(cache_key)
            
            if not session_data:
                raise TokenError("Session not found or expired")
            
            if not session_data.get("is_active", False):
                raise TokenError("Session is inactive")
            
            # Update last access time
            session_data["last_access"] = datetime.utcnow().isoformat()
            await cache_manager.set(cache_key, session_data, ttl=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        
        return payload
        
    except JWTError as e:
        logger.error("JWT verification failed", error=str(e))
        raise TokenError("Invalid token")
    except Exception as e:
        logger.error("Token verification failed", error=str(e))
        raise TokenError("Token verification failed")


def generate_session_id() -> str:
    """Generate a secure session ID"""
    return secrets.token_urlsafe(32)


async def revoke_token(token: str, token_type: str = "access") -> bool:
    """Revoke a JWT token by marking it as inactive in Redis"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        token_id = payload.get("jti")
        if not token_id:
            return False
        
        cache_key = f"session:{token_id}" if token_type == "access" else f"refresh:{token_id}"
        session_data = await cache_manager.get(cache_key)
        
        if session_data:
            session_data["is_active"] = False
            session_data["revoked_at"] = datetime.utcnow().isoformat()
            await cache_manager.set(cache_key, session_data, ttl=24 * 60 * 60)  # Keep for 24 hours
        
        logger.info("Token revoked", token_id=token_id, token_type=token_type)
        return True
        
    except Exception as e:
        logger.error("Failed to revoke token", error=str(e))
        return False


async def revoke_user_sessions(user_id: str) -> int:
    """Revoke all active sessions for a user"""
    try:
        # This would require scanning Redis keys, which is not ideal
        # In production, you might want to maintain a user->sessions mapping
        logger.info("Revoking all sessions for user", user_id=user_id)
        return 0  # Placeholder implementation
        
    except Exception as e:
        logger.error("Failed to revoke user sessions", error=str(e), user_id=user_id)
        return 0


async def get_active_sessions(user_id: str) -> list:
    """Get all active sessions for a user"""
    try:
        # This would require scanning Redis keys or maintaining a user->sessions mapping
        # Placeholder implementation
        return []
        
    except Exception as e:
        logger.error("Failed to get active sessions", error=str(e), user_id=user_id)
        return []


async def cleanup_expired_sessions() -> int:
    """Clean up expired sessions from Redis"""
    try:
        # Redis TTL handles automatic cleanup, but this could be used for manual cleanup
        # Placeholder implementation
        return 0
        
    except Exception as e:
        logger.error("Failed to cleanup expired sessions", error=str(e))
        return 0


def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(48)


def create_credentials_exception(detail: str = "Could not validate credentials") -> HTTPException:
    """Create standardized credentials exception"""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_permission_exception(detail: str = "Not enough permissions") -> HTTPException:
    """Create standardized permission exception"""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )


def mask_sensitive_data(data: Union[str, dict], fields: list = None) -> Union[str, dict]:
    """Mask sensitive data for logging"""
    if fields is None:
        fields = ["password", "token", "secret", "key", "hash"]
    
    if isinstance(data, str):
        # Simple string masking
        if any(field in data.lower() for field in fields):
            return "***MASKED***"
        return data
    
    elif isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            if any(field in key.lower() for field in fields):
                masked[key] = "***MASKED***"
            elif isinstance(value, (dict, list)):
                masked[key] = mask_sensitive_data(value, fields)
            else:
                masked[key] = value
        return masked
    
    elif isinstance(data, list):
        return [mask_sensitive_data(item, fields) for item in data]
    
    return data


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.attempts = {}
    
    def is_allowed(self, key: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """Check if request is allowed based on rate limiting"""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old attempts
        if key in self.attempts:
            self.attempts[key] = [
                attempt for attempt in self.attempts[key] 
                if attempt > window_start
            ]
        
        # Check current attempts
        current_attempts = len(self.attempts.get(key, []))
        
        if current_attempts >= max_attempts:
            return False
        
        # Record this attempt
        if key not in self.attempts:
            self.attempts[key] = []
        self.attempts[key].append(now)
        
        return True
    
    def reset(self, key: str):
        """Reset rate limiting for a key"""
        if key in self.attempts:
            del self.attempts[key]


# Global rate limiter instance
rate_limiter = RateLimiter()

