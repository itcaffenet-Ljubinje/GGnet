"""
Tests for caching middleware
"""

import pytest
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from httpx import AsyncClient
from app.middleware.caching import CacheMiddleware


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = AsyncMock()
    redis_mock.ping = AsyncMock(return_value=True)
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.setex = AsyncMock(return_value=True)
    redis_mock.keys = AsyncMock(return_value=[])
    redis_mock.delete = AsyncMock(return_value=0)
    return redis_mock


@pytest.fixture
def app_with_cache(mock_redis):
    """Create FastAPI app with cache middleware"""
    app = FastAPI()
    
    @app.get("/api/images")
    async def get_images():
        return {"images": [{"id": 1, "name": "test.vhdx"}]}
    
    @app.get("/api/machines")
    async def get_machines():
        return {"machines": [{"id": 1, "name": "test-machine"}]}
    
    @app.post("/api/images")
    async def create_image():
        return {"id": 1, "name": "new.vhdx"}
    
    # Add cache middleware
    app.add_middleware(
        CacheMiddleware,
        redis_url="redis://localhost:6379",
        default_ttl=300
    )
    
    # Mock Redis connection
    with patch('app.middleware.caching.redis.from_url', return_value=mock_redis):
        yield app


@pytest.mark.asyncio
async def test_cache_middleware_skips_non_get_requests(app_with_cache, mock_redis):
    """Test that non-GET requests are not cached"""
    async with AsyncClient(app=app_with_cache, base_url="http://test") as client:
        response = await client.post("/api/images")
        assert response.status_code == 200
        # Redis should not be called for POST requests
        mock_redis.get.assert_not_called()


@pytest.mark.asyncio
async def test_cache_middleware_skips_non_cacheable_paths(app_with_cache, mock_redis):
    """Test that non-cacheable paths are not cached"""
    async with AsyncClient(app=app_with_cache, base_url="http://test") as client:
        response = await client.get("/api/other")
        assert response.status_code == 404
        # Redis should not be called for non-cacheable paths
        mock_redis.get.assert_not_called()


@pytest.mark.asyncio
async def test_cache_middleware_cache_miss(app_with_cache, mock_redis):
    """Test cache miss scenario"""
    mock_redis.get.return_value = None
    
    async with AsyncClient(app=app_with_cache, base_url="http://test") as client:
        response = await client.get("/api/images")
        assert response.status_code == 200
        assert response.headers.get("X-Cache") == "MISS"
        assert "Cache-Control" in response.headers
        # Should have tried to get from cache
        mock_redis.get.assert_called_once()
        # Should have set cache
        mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_cache_middleware_cache_hit(app_with_cache, mock_redis):
    """Test cache hit scenario"""
    # Create cached data
    cache_data = {
        "body": json.dumps({"images": [{"id": 1, "name": "cached.vhdx"}]}),
        "status_code": 200,
        "headers": {"Content-Type": "application/json"},
        "media_type": "application/json",
        "expires": time.time() + 300,
        "cached_at": "2025-01-01T00:00:00"
    }
    mock_redis.get.return_value = json.dumps(cache_data)
    
    async with AsyncClient(app=app_with_cache, base_url="http://test") as client:
        response = await client.get("/api/images")
        assert response.status_code == 200
        assert response.headers.get("X-Cache") == "HIT"
        assert "X-Cache-Key" in response.headers
        # Should have tried to get from cache
        mock_redis.get.assert_called_once()
        # Should not have set cache (already cached)
        mock_redis.setex.assert_not_called()


@pytest.mark.asyncio
async def test_cache_middleware_expired_cache(app_with_cache, mock_redis):
    """Test expired cache scenario"""
    # Create expired cached data
    cache_data = {
        "body": json.dumps({"images": [{"id": 1, "name": "expired.vhdx"}]}),
        "status_code": 200,
        "headers": {"Content-Type": "application/json"},
        "media_type": "application/json",
        "expires": time.time() - 100,  # Expired
        "cached_at": "2025-01-01T00:00:00"
    }
    mock_redis.get.return_value = json.dumps(cache_data)
    
    async with AsyncClient(app=app_with_cache, base_url="http://test") as client:
        response = await client.get("/api/images")
        assert response.status_code == 200
        # Should treat as cache miss and set new cache
        mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_cache_middleware_only_caches_successful_responses(app_with_cache, mock_redis):
    """Test that only successful responses are cached"""
    app = FastAPI()
    
    @app.get("/api/images")
    async def get_images_error():
        return {"error": "Not found"}, 404
    
    app.add_middleware(
        CacheMiddleware,
        redis_url="redis://localhost:6379",
        default_ttl=300
    )
    
    with patch('app.middleware.caching.redis.from_url', return_value=mock_redis):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/images")
            assert response.status_code == 404
            # Should not cache error responses
            mock_redis.setex.assert_not_called()


@pytest.mark.asyncio
async def test_cache_middleware_redis_connection_failure():
    """Test behavior when Redis connection fails"""
    app = FastAPI()
    
    @app.get("/api/images")
    async def get_images():
        return {"images": []}
    
    app.add_middleware(
        CacheMiddleware,
        redis_url="redis://invalid:6379",
        default_ttl=300
    )
    
    # Mock Redis connection failure
    with patch('app.middleware.caching.redis.from_url', side_effect=Exception("Connection failed")):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/images")
            assert response.status_code == 200
            # Should still work without Redis


@pytest.mark.asyncio
async def test_cache_middleware_cache_key_generation(app_with_cache, mock_redis):
    """Test cache key generation includes auth"""
    mock_redis.get.return_value = None
    
    async with AsyncClient(app=app_with_cache, base_url="http://test") as client:
        # Request with auth
        response1 = await client.get(
            "/api/images",
            headers={"Authorization": "Bearer token1"}
        )
        assert response1.status_code == 200
        
        # Request with different auth
        response2 = await client.get(
            "/api/images",
            headers={"Authorization": "Bearer token2"}
        )
        assert response2.status_code == 200
        
        # Should have different cache keys
        assert mock_redis.setex.call_count == 2
        # Verify different keys were used
        key1 = mock_redis.setex.call_args_list[0][0][0]
        key2 = mock_redis.setex.call_args_list[1][0][0]
        assert key1 != key2


@pytest.mark.asyncio
async def test_cache_middleware_clear_cache(mock_redis):
    """Test clearing cache"""
    middleware = CacheMiddleware(
        app=MagicMock(),
        redis_url="redis://localhost:6379"
    )
    middleware.redis_client = mock_redis
    
    mock_redis.keys.return_value = ["cache:key1", "cache:key2"]
    
    await middleware.clear_cache()
    
    mock_redis.keys.assert_called_once_with("cache:*")
    mock_redis.delete.assert_called_once_with("cache:key1", "cache:key2")


@pytest.mark.asyncio
async def test_cache_middleware_clear_cache_with_pattern(mock_redis):
    """Test clearing cache with pattern"""
    middleware = CacheMiddleware(
        app=MagicMock(),
        redis_url="redis://localhost:6379"
    )
    middleware.redis_client = mock_redis
    
    mock_redis.keys.return_value = ["cache:images:key1"]
    
    await middleware.clear_cache(pattern="images")
    
    mock_redis.keys.assert_called_once_with("cache:*images*")
    mock_redis.delete.assert_called_once_with("cache:images:key1")

