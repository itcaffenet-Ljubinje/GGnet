"""
Rate limiting middleware
"""

import time
from typing import Callable, Dict, List
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()


class RateLimitStore:
    """In-memory rate limit store"""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed"""
        now = time.time()
        window_start = now - window
        
        # Clean old requests
        if key in self.requests:
            self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
        else:
            self.requests[key] = []
        
        # Check current count
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True
    
    def get_reset_time(self, key: str, window: int) -> float:
        """Get when the rate limit resets"""
        if key not in self.requests or not self.requests[key]:
            return time.time()
        
        oldest_request = min(self.requests[key])
        return oldest_request + window


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, store: RateLimitStore = None):
        super().__init__(app)
        self.store = store or RateLimitStore()
        
        # Rate limit rules: {path_pattern: (requests_per_minute, window_seconds)}
        self.rules = {
            "/auth/login": (20, 300),  # 20 requests per 5 minutes
            "/auth/refresh": (30, 60),  # 30 requests per minute
            "/images/upload": (5, 60),  # 5 uploads per minute
            "default": (200, 60)  # 200 requests per minute for other endpoints
        }
    
    def get_client_key(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get real IP from headers (reverse proxy)
        client_ip = request.headers.get("X-Forwarded-For")
        if client_ip:
            return client_ip.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    def get_rate_limit_rule(self, path: str) -> tuple:
        """Get rate limit rule for path"""
        for pattern, rule in self.rules.items():
            if pattern == "default":
                continue
            if path.startswith(pattern):
                return rule
        
        return self.rules["default"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks and static files
        if (request.url.path.startswith("/health") or 
            request.url.path.startswith("/docs") or 
            request.url.path.startswith("/openapi.json") or
            request.url.path.startswith("/static")):
            return await call_next(request)
        
        # Get client identifier and rate limit rule
        client_key = self.get_client_key(request)
        limit, window = self.get_rate_limit_rule(request.url.path)
        
        # Create rate limit key
        rate_key = f"{client_key}:{request.url.path}"
        
        # Check rate limit
        if not self.store.is_allowed(rate_key, limit, window):
            reset_time = self.store.get_reset_time(rate_key, window)
            retry_after = int(reset_time - time.time())
            
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_key,
                path=request.url.path,
                limit=limit,
                window=window,
                retry_after=retry_after
            )
            
            # Return rate limit error
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Maximum {limit} requests per {window} seconds.",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Window": str(window),
                    "X-RateLimit-Reset": str(int(reset_time))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, limit - len(self.store.requests.get(rate_key, [])))
        reset_time = self.store.get_reset_time(rate_key, window)
        
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        response.headers["X-RateLimit-Window"] = str(window)
        
        return response

