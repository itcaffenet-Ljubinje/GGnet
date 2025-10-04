"""
GGnet Diskless Server - Main FastAPI Application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request  # pyright: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware  # pyright: ignore[reportMissingImports]
from fastapi.middleware.trustedhost import TrustedHostMiddleware  # pyright: ignore[reportMissingImports]
from fastapi.responses import JSONResponse  # pyright: ignore[reportMissingImports]
import structlog  # pyright: ignore[reportMissingImports]
import time

from app.core.config import get_settings
from app.core.database import init_db
from app.core.exceptions import GGnetException
from app.routes import auth, images, machines, sessions, targets, storage, health
from app.middleware.rate_limiting import RateLimitMiddleware
from app.middleware.logging import LoggingMiddleware

# Configure structured logging
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

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting GGnet Diskless Server")
    settings = get_settings()
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GGnet Diskless Server")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="GGnet Diskless Server",
        description="Diskless server for Windows 11 UEFI+SecureBoot clients",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.DEBUG else ["localhost", "127.0.0.1"]
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"] if settings.DEBUG else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    
    # Exception handlers
    @app.exception_handler(GGnetException)
    async def ggnet_exception_handler(request: Request, exc: GGnetException):
        logger.error(
            "GGnet exception occurred",
            error_code=exc.error_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "detail": exc.detail,
                "timestamp": time.time()
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception occurred",
            error=str(exc),
            path=request.url.path,
            method=request.method,
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "detail": "An internal server error occurred",
                "timestamp": time.time()
            }
        )
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(auth.router, prefix="/auth", tags=["authentication"])
    app.include_router(images.router, prefix="/images", tags=["images"])
    app.include_router(machines.router, prefix="/machines", tags=["machines"])
    app.include_router(targets.router, prefix="/targets", tags=["targets"])
    app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
    app.include_router(storage.router, prefix="/storage", tags=["storage"])
    
    return app


# Create the application instance
app = create_app()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GGnet Diskless Server",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

