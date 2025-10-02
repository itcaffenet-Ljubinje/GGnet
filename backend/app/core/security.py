"""
Security utilities for authentication and authorization
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import secrets
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error("Password hashing failed", error=str(e))
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
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error("Failed to create access token", error=str(e))
        raise TokenError("Failed to create access token")


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error("Failed to create refresh token", error=str(e))
        raise TokenError("Failed to create refresh token")


def verify_token(token: str, token_type: str = "access") -> dict:
    """Verify and decode JWT token"""
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

