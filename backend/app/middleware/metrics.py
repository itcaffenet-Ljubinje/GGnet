"""
Metrics collection middleware
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.routes.metrics import increment_request_count, record_request_duration

logger = structlog.get_logger()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics"""
    
    async def dispatch(self, request: Request, call_next):
        # Record start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Update metrics
        increment_request_count()
        record_request_duration(duration)
        
        # Log request metrics
        logger.info(
            "HTTP request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
            user_agent=request.headers.get("user-agent", ""),
            client_ip=request.client.host if request.client else None
        )
        
        return response
