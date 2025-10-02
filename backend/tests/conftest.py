"""
Test configuration and fixtures
"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.config import get_settings
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    """Create a test client."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db_session):
    """Create an admin user for testing."""
    user = User(
        username="admin",
        email="admin@test.com",
        full_name="Test Admin",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_active=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def operator_user(db_session):
    """Create an operator user for testing."""
    user = User(
        username="operator",
        email="operator@test.com",
        full_name="Test Operator",
        hashed_password=get_password_hash("operator123"),
        role=UserRole.OPERATOR,
        status=UserStatus.ACTIVE,
        is_active=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def viewer_user(db_session):
    """Create a viewer user for testing."""
    user = User(
        username="viewer",
        email="viewer@test.com",
        full_name="Test Viewer",
        hashed_password=get_password_hash("viewer123"),
        role=UserRole.VIEWER,
        status=UserStatus.ACTIVE,
        is_active=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def admin_token(client, admin_user):
    """Get admin access token."""
    response = await client.post("/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest_asyncio.fixture
async def operator_token(client, operator_user):
    """Get operator access token."""
    response = await client.post("/auth/login", json={
        "username": "operator",
        "password": "operator123"
    })
    
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest_asyncio.fixture
async def viewer_token(client, viewer_user):
    """Get viewer access token."""
    response = await client.post("/auth/login", json={
        "username": "viewer",
        "password": "viewer123"
    })
    
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


def auth_headers(token: str) -> dict:
    """Create authorization headers."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_image_data():
    """Sample image data for testing."""
    return {
        "name": "Test Image",
        "description": "Test image description",
        "format": "vhdx",
        "size_bytes": 1073741824,  # 1GB
        "image_type": "system",
        "status": "ready"
    }


@pytest.fixture
def sample_machine_data():
    """Sample machine data for testing."""
    return {
        "name": "Test Machine",
        "description": "Test machine description",
        "mac_address": "00:11:22:33:44:55",
        "ip_address": "192.168.1.100",
        "hostname": "test-machine",
        "boot_mode": "uefi",
        "secure_boot_enabled": True,
        "location": "Test Lab",
        "room": "Room 101"
    }

