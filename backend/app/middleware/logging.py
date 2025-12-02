"""
Enhanced logging middleware
"""

import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.core.logging_config import log_performance_event

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced logging middleware with request tracking"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        # Log request start
        logger.info(
            "HTTP request started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", ""),
            content_length=request.headers.get("content-length", "0")
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            duration_ms = round(duration * 1000, 2)
            
            # Log request completion
            logger.info(
                "HTTP request completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_size=response.headers.get("content-length", "0")
            )
            
            # Log performance event for slow requests
            if duration_ms > 1000:  # Log requests taking more than 1 second
                log_performance_event(
                    operation=f"{request.method} {request.url.path}",
                    duration_ms=duration_ms,
                    details={
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "client_ip": request.client.host if request.client else None
                    }
                )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration for failed requests
            duration = time.time() - start_time
            duration_ms = round(duration * 1000, 2)
            
            # Log request error
            logger.error(
                "HTTP request failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                error=str(e),
                exc_info=True
            )
            
            # Re-raise the exception
            raise