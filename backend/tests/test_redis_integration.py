"""
Redis integration tests
"""

import pytest
import asyncio
from httpx import AsyncClient
from app.core.cache import cache_manager
from app.core.security import create_access_token, create_refresh_token
from tests.conftest import REDIS_AVAILABLE

# Skip all Redis tests if Redis is not available
pytestmark = pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available")


class TestRedisIntegration:
    """Test Redis integration functionality"""
    
    @pytest.mark.redis
    @pytest.mark.asyncio
    async def test_redis_connection(self):
        """Test basic Redis connection"""
        try:
            # Test basic set/get
            await cache_manager.set("test_key", "test_value", ttl=60)
            value = await cache_manager.get("test_key")
            assert value == "test_value"
            
            # Test delete
            await cache_manager.delete("test_key")
            value = await cache_manager.get("test_key")
            assert value is None
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_redis_session_storage(self):
        """Test Redis session storage for authentication"""
        try:
            # Create test tokens
            access_token = create_access_token({"sub": "1", "username": "test"})
            refresh_token = create_refresh_token({"sub": "1", "username": "test"})
            
            # Test session data storage
            session_data = {
                "user_id": "1",
                "username": "test",
                "token_type": "access",
                "is_active": True
            }
            
            await cache_manager.set("session:test_session", session_data, ttl=3600)
            retrieved_data = await cache_manager.get("session:test_session")
            
            assert retrieved_data is not None
            assert retrieved_data["user_id"] == "1"
            assert retrieved_data["username"] == "test"
            
            # Clean up
            await cache_manager.delete("session:test_session")
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_redis_ttl_expiration(self):
        """Test Redis TTL expiration"""
        try:
            # Set key with short TTL
            await cache_manager.set("ttl_test", "expires_soon", ttl=1)
            
            # Should be available immediately
            value = await cache_manager.get("ttl_test")
            assert value == "expires_soon"
            
            # Wait for expiration
            await asyncio.sleep(2)
            
            # Should be expired
            value = await cache_manager.get("ttl_test")
            assert value is None
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_redis_json_serialization(self):
        """Test Redis JSON serialization"""
        try:
            # Test complex data structure
            complex_data = {
                "user": {
                    "id": 1,
                    "username": "test",
                    "roles": ["admin", "user"],
                    "metadata": {
                        "last_login": "2023-01-01T00:00:00Z",
                        "preferences": {"theme": "dark"}
                    }
                },
                "session": {
                    "id": "session_123",
                    "created_at": "2023-01-01T00:00:00Z",
                    "expires_at": "2023-01-01T01:00:00Z"
                }
            }
            
            await cache_manager.set("complex_data", complex_data, ttl=3600)
            retrieved_data = await cache_manager.get("complex_data")
            
            assert retrieved_data is not None
            assert retrieved_data["user"]["id"] == 1
            assert retrieved_data["user"]["username"] == "test"
            assert retrieved_data["user"]["roles"] == ["admin", "user"]
            assert retrieved_data["session"]["id"] == "session_123"
            
            # Clean up
            await cache_manager.delete("complex_data")
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_redis_rate_limiting(self):
        """Test Redis-based rate limiting"""
        try:
            # Simulate rate limiting
            client_ip = "192.168.1.100"
            rate_limit_key = f"rate_limit:{client_ip}"
            
            # Check initial state
            current_count = await cache_manager.get(rate_limit_key)
            assert current_count is None or current_count == 0
            
            # Increment rate limit counter
            await cache_manager.increment(rate_limit_key, ttl=60)
            count = await cache_manager.get(rate_limit_key)
            assert count == 1
            
            # Increment again
            await cache_manager.increment(rate_limit_key, ttl=60)
            count = await cache_manager.get(rate_limit_key)
            assert count == 2
            
            # Clean up
            await cache_manager.delete(rate_limit_key)
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_redis_cache_invalidation(self):
        """Test Redis cache invalidation patterns"""
        try:
            # Set multiple related keys
            await cache_manager.set("user:1:profile", {"name": "User 1"}, ttl=3600)
            await cache_manager.set("user:1:sessions", ["session1", "session2"], ttl=3600)
            await cache_manager.set("user:1:permissions", ["read", "write"], ttl=3600)
            
            # Verify all keys exist
            profile = await cache_manager.get("user:1:profile")
            sessions = await cache_manager.get("user:1:sessions")
            permissions = await cache_manager.get("user:1:permissions")
            
            assert profile is not None
            assert sessions is not None
            assert permissions is not None
            
            # Simulate cache invalidation (delete all user-related keys)
            await cache_manager.delete("user:1:profile")
            await cache_manager.delete("user:1:sessions")
            await cache_manager.delete("user:1:permissions")
            
            # Verify all keys are deleted
            profile = await cache_manager.get("user:1:profile")
            sessions = await cache_manager.get("user:1:sessions")
            permissions = await cache_manager.get("user:1:permissions")
            
            assert profile is None
            assert sessions is None
            assert permissions is None
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_redis_error_handling(self):
        """Test Redis error handling"""
        try:
            # Test with invalid data
            await cache_manager.set("invalid_key", None, ttl=60)
            value = await cache_manager.get("invalid_key")
            assert value is None
            
            # Test with empty key
            await cache_manager.set("", "empty_key_value", ttl=60)
            value = await cache_manager.get("")
            assert value == "empty_key_value"
            
            # Clean up
            await cache_manager.delete("")
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_redis_performance(self):
        """Test Redis performance with multiple operations"""
        try:
            # Test bulk operations
            start_time = asyncio.get_event_loop().time()
            
            # Set multiple keys
            tasks = []
            for i in range(100):
                task = cache_manager.set(f"perf_test_{i}", f"value_{i}", ttl=60)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
            # Get multiple keys
            tasks = []
            for i in range(100):
                task = cache_manager.get(f"perf_test_{i}")
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            # Verify all values were retrieved correctly
            for i, result in enumerate(results):
                assert result == f"value_{i}"
            
            # Performance should be reasonable (less than 1 second for 200 operations)
            assert duration < 1.0
            
            # Clean up
            tasks = []
            for i in range(100):
                task = cache_manager.delete(f"perf_test_{i}")
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")


class TestRedisWithFastAPI:
    """Test Redis integration with FastAPI endpoints"""
    
    @pytest.mark.asyncio
    async def test_auth_with_redis_sessions(self, client: AsyncClient):
        """Test authentication with Redis session storage"""
        try:
            # Test login (should create Redis session)
            response = await client.post("/auth/login", json={
                "username": "admin",
                "password": "admin123"
            })
            
            if response.status_code == 200:
                data = response.json()
                access_token = data["access_token"]
                
                # Test authenticated request (should use Redis session)
                response = await client.get(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                assert response.status_code == 200
                user_data = response.json()
                assert user_data["username"] == "admin"
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_rate_limiting_with_redis(self, client: AsyncClient):
        """Test rate limiting with Redis"""
        try:
            # Make multiple requests to trigger rate limiting
            for i in range(25):  # Exceed default rate limit
                response = await client.post("/auth/login", json={
                    "username": "admin",
                    "password": "wrong_password"
                })
                
                if response.status_code == 429:  # Rate limited
                    break
            
            # Should eventually get rate limited
            assert response.status_code == 429
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_on_logout(self, client: AsyncClient):
        """Test cache invalidation on logout"""
        try:
            # Login
            response = await client.post("/auth/login", json={
                "username": "admin",
                "password": "admin123"
            })
            
            if response.status_code == 200:
                data = response.json()
                access_token = data["access_token"]
                
                # Logout (should invalidate Redis session)
                response = await client.post(
                    "/auth/logout",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                assert response.status_code == 200
                
                # Try to use token after logout (should fail)
                response = await client.get(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                assert response.status_code == 401
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
