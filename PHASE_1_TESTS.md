# PHASE 1: Backend Core (FastAPI) - Testing Guide

## Overview
This document provides comprehensive testing instructions for the Phase 1 backend implementation, including unit tests, integration tests, and API testing.

## Test Environment Setup

### Prerequisites
- Python 3.11+
- PostgreSQL or SQLite
- Redis server
- pytest and testing dependencies

### Installation
```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx
```

## Running Tests

### All Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/api/ -v
```

### Specific Test Files
```bash
# Authentication tests
pytest tests/test_auth.py -v

# Machine management tests
pytest tests/test_machines.py -v

# Image management tests
pytest tests/test_images.py -v

# Session management tests
pytest tests/test_sessions.py -v

# Integration tests
pytest tests/test_integration.py -v
```

## Test Categories

### 1. Unit Tests

#### Authentication Tests
```python
# tests/test_auth.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_login_success():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_login_invalid_credentials():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "wrong"
        })
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_token_refresh():
    # Test token refresh functionality
    pass
```

#### Machine Management Tests
```python
# tests/test_machines.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_machine():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Get auth token first
        auth_response = await client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = auth_response.json()["access_token"]
        
        # Create machine
        response = await client.post("/api/v1/machines", 
            json={
                "name": "test-machine",
                "mac_address": "00:11:22:33:44:55",
                "ip_address": "192.168.1.100"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201
        assert response.json()["name"] == "test-machine"

@pytest.mark.asyncio
async def test_list_machines():
    # Test machine listing with pagination
    pass

@pytest.mark.asyncio
async def test_machine_validation():
    # Test MAC address and IP validation
    pass
```

#### Image Management Tests
```python
# tests/test_images.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_image_upload():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Get auth token
        auth_response = await client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = auth_response.json()["access_token"]
        
        # Upload test file
        with open("test_image.vhdx", "rb") as f:
            response = await client.post("/api/v1/images/upload",
                files={"file": f},
                data={"name": "test-image", "description": "Test image"},
                headers={"Authorization": f"Bearer {token}"}
            )
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_image_list():
    # Test image listing and filtering
    pass

@pytest.mark.asyncio
async def test_image_conversion():
    # Test image conversion trigger
    pass
```

#### Session Management Tests
```python
# tests/test_sessions.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_session():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Get auth token
        auth_response = await client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = auth_response.json()["access_token"]
        
        # Create session
        response = await client.post("/api/v1/sessions",
            json={
                "target_id": 1,
                "session_type": "DISKLESS_BOOT"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201

@pytest.mark.asyncio
async def test_session_lifecycle():
    # Test complete session lifecycle
    pass

@pytest.mark.asyncio
async def test_session_statistics():
    # Test session statistics endpoint
    pass
```

### 2. Integration Tests

#### Database Integration
```python
# tests/test_integration.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.models.machine import Machine

@pytest.mark.asyncio
async def test_database_connection():
    async with get_db() as db:
        result = await db.execute("SELECT 1")
        assert result.scalar() == 1

@pytest.mark.asyncio
async def test_user_creation():
    async with get_db() as db:
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        assert user.id is not None

@pytest.mark.asyncio
async def test_machine_relationships():
    # Test machine relationships with targets and sessions
    pass
```

#### Redis Integration
```python
# tests/test_redis_integration.py
import pytest
from app.core.cache import cache_manager

@pytest.mark.asyncio
async def test_redis_connection():
    await cache_manager.set("test_key", "test_value", expire=60)
    value = await cache_manager.get("test_key")
    assert value == "test_value"

@pytest.mark.asyncio
async def test_session_caching():
    # Test session token caching
    pass

@pytest.mark.asyncio
async def test_rate_limiting():
    # Test rate limiting functionality
    pass
```

### 3. API Tests

#### End-to-End API Tests
```python
# tests/test_api_e2e.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_complete_workflow():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Login
        auth_response = await client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create machine
        machine_response = await client.post("/api/v1/machines",
            json={
                "name": "workstation-01",
                "mac_address": "00:11:22:33:44:55",
                "ip_address": "192.168.1.101"
            },
            headers=headers
        )
        machine_id = machine_response.json()["id"]
        
        # 3. Upload image
        with open("test_image.vhdx", "rb") as f:
            image_response = await client.post("/api/v1/images/upload",
                files={"file": f},
                data={"name": "windows-10", "description": "Windows 10 image"},
                headers=headers
            )
        image_id = image_response.json()["id"]
        
        # 4. Create target
        target_response = await client.post("/api/v1/targets",
            json={
                "machine_id": machine_id,
                "image_id": image_id,
                "name": "target-01"
            },
            headers=headers
        )
        target_id = target_response.json()["id"]
        
        # 5. Start session
        session_response = await client.post("/api/v1/sessions",
            json={
                "target_id": target_id,
                "session_type": "DISKLESS_BOOT"
            },
            headers=headers
        )
        assert session_response.status_code == 201
        
        # 6. Stop session
        session_id = session_response.json()["id"]
        stop_response = await client.post(f"/api/v1/sessions/{session_id}/stop",
            headers=headers
        )
        assert stop_response.status_code == 200

@pytest.mark.asyncio
async def test_error_handling():
    # Test various error scenarios
    pass

@pytest.mark.asyncio
async def test_rate_limiting():
    # Test rate limiting behavior
    pass
```

### 4. Performance Tests

#### Load Testing
```python
# tests/test_performance.py
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_concurrent_requests():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test concurrent machine creation
        tasks = []
        for i in range(10):
            task = client.post("/api/v1/machines",
                json={
                    "name": f"machine-{i}",
                    "mac_address": f"00:11:22:33:44:{i:02x}",
                    "ip_address": f"192.168.1.{100 + i}"
                }
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        for response in responses:
            assert response.status_code == 201

@pytest.mark.asyncio
async def test_database_performance():
    # Test database query performance
    pass

@pytest.mark.asyncio
async def test_redis_performance():
    # Test Redis operation performance
    pass
```

## Test Configuration

### Pytest Configuration
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
asyncio_mode = auto
```

### Test Fixtures
```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from app.main import app
from app.core.database import get_db
from app.models.user import User

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def auth_headers(client):
    response = await client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def test_user():
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    return user
```

## Test Data Management

### Test Database Setup
```python
# tests/database.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models import *

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///./test.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def test_db(test_engine):
    async_session = sessionmaker(test_engine, class_=AsyncSession)
    async with async_session() as session:
        yield session
        await session.rollback()
```

### Mock Data
```python
# tests/fixtures.py
import pytest
from app.models.machine import Machine, MachineStatus, BootMode
from app.models.image import Image, ImageStatus, ImageFormat

@pytest.fixture
def sample_machine():
    return Machine(
        name="test-workstation",
        mac_address="00:11:22:33:44:55",
        ip_address="192.168.1.100",
        boot_mode=BootMode.UEFI,
        status=MachineStatus.ACTIVE
    )

@pytest.fixture
def sample_image():
    return Image(
        name="test-image",
        filename="test.vhdx",
        file_path="/storage/test.vhdx",
        format=ImageFormat.VHDX,
        status=ImageStatus.READY,
        size_bytes=1024*1024*1024
    )
```

## Continuous Integration

### GitHub Actions
```yaml
# .github/workflows/backend-tests.yml
name: Backend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_ggnet
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-asyncio httpx
    - name: Run tests
      run: |
        cd backend
        pytest tests/ -v --cov=app --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## Test Coverage Goals

### Minimum Coverage Requirements
- **Overall Coverage**: 80%+
- **Critical Paths**: 95%+
- **Authentication**: 100%
- **API Endpoints**: 90%+
- **Database Models**: 85%+
- **Error Handling**: 90%+

### Coverage Reports
```bash
# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html

# Generate XML coverage report
pytest tests/ --cov=app --cov-report=xml

# View coverage in terminal
pytest tests/ --cov=app --cov-report=term-missing
```

## Debugging Tests

### Test Debugging
```bash
# Run tests with verbose output
pytest tests/ -v -s

# Run specific test with debugging
pytest tests/test_auth.py::test_login_success -v -s

# Run tests with pdb debugging
pytest tests/ --pdb

# Run tests with logging
pytest tests/ -v --log-cli-level=DEBUG
```

### Database Debugging
```python
# Add to test files for debugging
import logging
logging.basicConfig(level=logging.DEBUG)

# Print SQL queries
import sqlalchemy
sqlalchemy.engine.Engine.echo = True
```

## Best Practices

### Test Organization
- Group related tests in classes
- Use descriptive test names
- Keep tests focused and atomic
- Use fixtures for common setup

### Test Data
- Use factories for test data creation
- Clean up test data after tests
- Use realistic test data
- Avoid hardcoded values

### Assertions
- Use specific assertions
- Test both success and failure cases
- Verify side effects
- Check response structure

### Performance
- Keep tests fast
- Use appropriate test scopes
- Mock external dependencies
- Avoid unnecessary I/O operations
