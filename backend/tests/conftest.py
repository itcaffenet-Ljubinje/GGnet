"""
Pytest fixtures for testing FastAPI app with async support
"""

import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models.base import Base
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

@pytest.fixture(scope="session")
async def prepare_db():
    """Create test database schema once per session"""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture()
async def db_session(prepare_db):
    """Provide a transactional scope around a test."""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture()
async def client(db_session):
    """Provide an AsyncClient for testing FastAPI routes."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

# ------------------------
# User & token fixtures
# ------------------------

@pytest.fixture()
async def admin_user(db_session):
    """Create an admin user."""
    user = User(
        username="admin",
        password=get_password_hash("admin123"),
        role=UserRole.ADMIN
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture()
async def viewer_user(db_session):
    """Create a viewer user."""
    user = User(
        username="viewer",
        password=get_password_hash("viewer123"),
        role=UserRole.VIEWER
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture()
def auth_headers():
    """Return a function to generate auth headers for a user token."""
    def _auth_headers(token: str):
        return {"Authorization": f"Bearer {token}"}
    return _auth_headers

@pytest.fixture()
async def admin_token(admin_user):
    """Return access token for admin user."""
    return create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})

@pytest.fixture()
async def viewer_token(viewer_user):
    """Return access token for viewer user."""
    return create_access_token({"sub": str(viewer_user.id), "role": viewer_user.role.value})
