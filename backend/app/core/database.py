"""
Database configuration and session management
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()

# Database metadata
metadata = MetaData()


class Base(DeclarativeBase):
    """Base class for all database models"""
    metadata = metadata


# Database engines - lazy initialization
_settings = None
_sync_engine = None
_async_engine = None

def get_settings():
    """Get settings instance"""
    global _settings
    if _settings is None:
        from app.core.config import get_settings as _get_settings
        _settings = _get_settings()
    return _settings

def get_sync_engine():
    """Get synchronous engine for migrations"""
    global _sync_engine
    if _sync_engine is None:
        settings = get_settings()
        try:
            _sync_engine = create_engine(
                settings.database_url_sync,
                echo=settings.DEBUG,
                pool_pre_ping=True,
                pool_size=10,  # Number of connections to maintain
                max_overflow=20,  # Maximum number of connections to create beyond pool_size
                pool_recycle=3600,  # Recycle connections after 1 hour
                pool_timeout=30,  # Timeout for getting connection from pool
            )
        except Exception as e:
            logger.error(f"Failed to create sync engine: {e}")
            # Fallback to SQLite if PostgreSQL fails
            if settings.database_url_sync.startswith("postgresql"):
                logger.warning("Falling back to SQLite due to PostgreSQL connection failure")
                _sync_engine = create_engine(
                    "sqlite:///./ggnet.db",
                    echo=settings.DEBUG,
                    pool_pre_ping=True,
                )
            else:
                raise
    return _sync_engine

def get_async_engine():
    """Get asynchronous engine for application"""
    global _async_engine
    if _async_engine is None:
        settings = get_settings()
        try:
            _async_engine = create_async_engine(
                settings.database_url_async,
                echo=settings.DEBUG,
                pool_pre_ping=True,
                pool_size=20,  # Number of connections to maintain (higher for async)
                max_overflow=40,  # Maximum number of connections to create beyond pool_size
                pool_recycle=3600,  # Recycle connections after 1 hour
                pool_timeout=30,  # Timeout for getting connection from pool
            )
        except Exception as e:
            logger.error(f"Failed to create async engine: {e}")
            # Fallback to SQLite if PostgreSQL fails
            if settings.database_url_async.startswith("postgresql"):
                logger.warning("Falling back to SQLite due to PostgreSQL connection failure")
                _async_engine = create_async_engine(
                    "sqlite+aiosqlite:///./ggnet.db",
                    echo=settings.DEBUG,
                    pool_pre_ping=True,
                )
            else:
                raise
    return _async_engine

# Session factories - lazy initialization
_AsyncSessionLocal = None
_SessionLocal = None

def get_async_session_local():
    """Get async session factory"""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False
        )
    return _AsyncSessionLocal

def get_session_local():
    """Get sync session factory"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_sync_engine()
        )
    return _SessionLocal


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    try:
        async_engine = get_async_engine()
        async with async_engine.begin() as conn:
            # Import all models to ensure they are registered
            from app.models import user, image, machine, target, session, audit
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def close_db():
    """Close database connections"""
    global _async_engine, _sync_engine
    if _async_engine is not None:
        await _async_engine.dispose()
    if _sync_engine is not None:
        _sync_engine.dispose()
    logger.info("Database connections closed")

