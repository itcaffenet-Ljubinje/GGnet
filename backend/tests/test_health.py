"""
Test health check endpoints
"""

import pytest
from httpx import AsyncClient


class TestHealth:
    """Test health check functionality."""
    
    @pytest.mark.asyncio
    async def test_basic_health_check(self, client: AsyncClient):
        """Test basic health check endpoint."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "ggnet-diskless-server"
        assert data["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_detailed_health_check(self, client: AsyncClient, db_session):
        """Test detailed health check endpoint."""
        response = await client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data
        assert "checks" in data
        
        checks = data["checks"]
        assert "database" in checks
        assert "storage" in checks
        assert "system" in checks
    
    @pytest.mark.asyncio
    async def test_readiness_check(self, client: AsyncClient, db_session):
        """Test readiness probe endpoint."""
        response = await client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        # Status might be "ready" or "not_ready" depending on test environment
        assert data["status"] in ["ready", "not_ready"]
    
    @pytest.mark.asyncio
    async def test_liveness_check(self, client: AsyncClient):
        """Test liveness probe endpoint."""
        response = await client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "alive"
        assert "timestamp" in data

