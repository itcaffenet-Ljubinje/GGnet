"""
Pytest fixtures for testing FastAPI app with async support
"""

import asyncio
import pytest
from httpx import AsyncClient  # pyright: ignore[reportMissingImports]
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import sessionmaker  # pyright: ignore[reportMissingImports]
from app.main import app
from app.core.database import Base
from app.models.user import User, UserRole
from app.core.security import get_password_hash, create_access_token

DATABASE_URL_TEST = "sqlite+aiosqlite:///./test.db"

# Create async engine and session factory
engine_test = create_async_engine(DATABASE_URL_TEST, future=True, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=engine_test,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="function")
async def db_session():
    """Provide a transactional scope around a test."""
    # Create tables for this test
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Provide session
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
    
    # Clean up tables after test
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db_session):
    """Provide an AsyncClient for testing FastAPI routes."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

# ------------------------
# User & token fixtures
# ------------------------

@pytest.fixture(scope="function")
async def admin_user(db_session):
    """Create an admin user."""
    user = User(
        username="admin",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
async def viewer_user(db_session):
    """Create a viewer user."""
    user = User(
        username="viewer",
        hashed_password=get_password_hash("viewer123"),
        role=UserRole.VIEWER
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def auth_headers():
    """Return a function to generate auth headers for a user token."""
    def _auth_headers(token: str):
        return {"Authorization": f"Bearer {token}"}
    return _auth_headers

@pytest.fixture(scope="function")
async def admin_token(admin_user):
    """Return access token for admin user."""
    return create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})

@pytest.fixture(scope="function")
async def viewer_token(viewer_user):
    """Return access token for viewer user."""
    return create_access_token({"sub": str(viewer_user.id), "role": viewer_user.role.value})
