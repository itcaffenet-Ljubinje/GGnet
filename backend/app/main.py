"""
GGnet Diskless Server - Main FastAPI Application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect  # pyright: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware  # pyright: ignore[reportMissingImports]
from fastapi.middleware.trustedhost import TrustedHostMiddleware  # pyright: ignore[reportMissingImports]
from fastapi.responses import JSONResponse  # pyright: ignore[reportMissingImports]
import structlog  # pyright: ignore[reportMissingImports]
import time

from app.core.config import get_settings
from app.core.database import init_db
from app.core.exceptions import GGnetException
from app.routes import auth, images, machines, sessions, storage, health, monitoring, file_upload, iscsi
from app.api import targets, sessions as sessions_api
from app.middleware.rate_limiting import RateLimitMiddleware
from app.middleware.logging import LoggingMiddleware
from app.websocket.manager import WebSocketManager

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
    
    # Initialize WebSocket manager
    app.state.websocket_manager = WebSocketManager()
    logger.info("WebSocket manager initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GGnet Diskless Server")
    if hasattr(app.state, 'websocket_manager'):
        await app.state.websocket_manager.disconnect_all()
        logger.info("WebSocket connections closed")


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
    app.include_router(targets.router, prefix="/api/v1", tags=["targets"])
    app.include_router(sessions_api.router, prefix="/api/v1/sessions", tags=["sessions"])
    app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
    app.include_router(storage.router, prefix="/storage", tags=["storage"])
    app.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
    app.include_router(file_upload.router, prefix="/upload", tags=["file-upload"])
    app.include_router(iscsi.router, prefix="/iscsi", tags=["iscsi"])
    
    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates"""
        await websocket.accept()
        
        connection_id = None
        try:
            # Get token from query parameters
            token = websocket.query_params.get("token")
            
            # Connect to WebSocket manager
            connection_id = await app.state.websocket_manager.connect(websocket, token)
            
            # Keep connection alive and handle messages
            while True:
                try:
                    # Wait for messages from client
                    data = await websocket.receive_text()
                    
                    # Process message through manager
                    try:
                        import json
                        message = json.loads(data)
                        await app.state.websocket_manager.handle_client_message(connection_id, message)
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON received", connection_id=connection_id, data=data)
                        
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            # Clean up connection
            if connection_id:
                try:
                    await app.state.websocket_manager.disconnect(connection_id)
                except Exception as e:
                    logger.error(f"WebSocket cleanup error: {e}")
    
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

