"""
Advanced caching strategies for GGnet
"""

from typing import Any, Optional, Union, Dict, List
from functools import wraps
import asyncio
import json
import hashlib
import pickle
from datetime import datetime, timedelta
import structlog
from pathlib import Path

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class CacheManager:
    """Advanced cache manager with multiple backends"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.file_cache_dir = Path("./cache")
        self.file_cache_dir.mkdir(exist_ok=True)
        
        # Cache configuration
        self.default_ttl = 300  # 5 minutes
        self.memory_cache_size = 1000
        self.file_cache_size = 10000
        
        # Initialize Redis if available
        if REDIS_AVAILABLE and settings.REDIS_URL:
            try:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Test connection (will be tested on first use)
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {e}")
                self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback strategy"""
        
        # Try Redis first
        if self.redis_client:
            try:
                # Test connection on first use
                await self._test_redis_connection()
                if self.redis_client:
                    value = await self.redis_client.get(key)
                    if value:
                        return pickle.loads(value)
            except Exception as e:
                logger.warning(f"Redis get failed for key {key}: {e}")
                self.redis_client = None
        
        # Try memory cache
        if key in self.memory_cache:
            cache_entry = self.memory_cache[key]
            if cache_entry['expires'] > datetime.now():
                return cache_entry['value']
            else:
                del self.memory_cache[key]
        
        # Try file cache
        file_path = self.file_cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.cache"
        if file_path.exists():
            try:
                with open(file_path, 'rb') as f:
                    cache_entry = pickle.load(f)
                    if cache_entry['expires'] > datetime.now():
                        # Promote to memory cache
                        self._add_to_memory_cache(key, cache_entry['value'], cache_entry['expires'])
                        return cache_entry['value']
                    else:
                        file_path.unlink()
            except Exception as e:
                logger.warning(f"File cache get failed for key {key}: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with multiple backends"""
        
        ttl = ttl or self.default_ttl
        expires = datetime.now() + timedelta(seconds=ttl)
        
        success = True
        
        # Set in Redis
        if self.redis_client:
            try:
                # Test connection on first use
                await self._test_redis_connection()
                if self.redis_client:
                    await self.redis_client.setex(key, ttl, pickle.dumps(value))
            except Exception as e:
                logger.warning(f"Redis set failed for key {key}: {e}")
                self.redis_client = None
                success = False
        
        # Set in memory cache
        self._add_to_memory_cache(key, value, expires)
        
        # Set in file cache
        try:
            file_path = self.file_cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.cache"
            cache_entry = {'value': value, 'expires': expires}
            with open(file_path, 'wb') as f:
                pickle.dump(cache_entry, f)
        except Exception as e:
            logger.warning(f"File cache set failed for key {key}: {e}")
            success = False
        
        return success
    
    async def delete(self, key: str) -> bool:
        """Delete value from all cache backends"""
        
        success = True
        
        # Delete from Redis
        if self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete failed for key {key}: {e}")
                success = False
        
        # Delete from memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # Delete from file cache
        file_path = self.file_cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.cache"
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning(f"File cache delete failed for key {key}: {e}")
                success = False
        
        return success
    
    async def clear(self) -> bool:
        """Clear all caches"""
        
        success = True
        
        # Clear Redis
        if self.redis_client:
            try:
                await self.redis_client.flushdb()
            except Exception as e:
                logger.warning(f"Redis clear failed: {e}")
                success = False
        
        # Clear memory cache
        self.memory_cache.clear()
        
        # Clear file cache
        try:
            for file_path in self.file_cache_dir.glob("*.cache"):
                file_path.unlink()
        except Exception as e:
            logger.warning(f"File cache clear failed: {e}")
            success = False
        
        return success
    
    def _add_to_memory_cache(self, key: str, value: Any, expires: datetime):
        """Add to memory cache with LRU eviction"""
        
        # Remove expired entries
        now = datetime.now()
        expired_keys = [k for k, v in self.memory_cache.items() if v['expires'] <= now]
        for k in expired_keys:
            del self.memory_cache[k]
        
        # Evict oldest if cache is full
        if len(self.memory_cache) >= self.memory_cache_size:
            oldest_key = min(self.memory_cache.keys(), key=lambda k: self.memory_cache[k]['created'])
            del self.memory_cache[oldest_key]
        
        self.memory_cache[key] = {
            'value': value,
            'expires': expires,
            'created': datetime.now()
        }
    
    async def increment(self, key: str, amount: int = 1, ttl: int = 3600) -> int:
        """Increment a numeric value in cache"""
        
        # Try Redis first
        if self.redis_client:
            try:
                result = await self.redis_client.incr(key, amount)
                await self.redis_client.expire(key, ttl)
                return result
            except Exception as e:
                logger.warning(f"Redis increment failed: {e}")
        
        # Fallback to memory cache
        current_value = await self.get(key)
        if current_value is None:
            new_value = amount
        else:
            try:
                new_value = int(current_value) + amount
            except (ValueError, TypeError):
                new_value = amount
        
        await self.set(key, new_value, ttl)
        return new_value
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        
        # Try Redis first
        if self.redis_client:
            try:
                return await self.redis_client.exists(key) > 0
            except Exception as e:
                logger.warning(f"Redis exists check failed: {e}")
        
        # Fallback to memory cache
        return key in self.memory_cache and not self._is_expired(key)
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for a key"""
        
        # Try Redis first
        if self.redis_client:
            try:
                return await self.redis_client.expire(key, ttl)
            except Exception as e:
                logger.warning(f"Redis expire failed: {e}")
        
        # Fallback to memory cache
        if key in self.memory_cache:
            expires = datetime.now() + timedelta(seconds=ttl)
            self.memory_cache[key]['expires'] = expires
            return True
        
        return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        
        stats = {
            'memory_cache_size': len(self.memory_cache),
            'memory_cache_max': self.memory_cache_size,
            'file_cache_count': len(list(self.file_cache_dir.glob("*.cache"))),
            'redis_available': self.redis_client is not None
        }
        
        if self.redis_client:
            try:
                redis_info = await self.redis_client.info()
                stats['redis_memory_used'] = redis_info.get('used_memory_human', 'N/A')
                stats['redis_keys'] = await self.redis_client.dbsize()
            except Exception as e:
                stats['redis_error'] = str(e)
        
        return stats
    
    async def _test_redis_connection(self):
        """Test Redis connection and disable if failed"""
        try:
            if self.redis_client:
                await self.redis_client.ping()
                logger.info("Redis connection test successful")
        except Exception as e:
            logger.warning(f"Redis connection test failed: {e}")
            self.redis_client = None


# Global cache manager instance
cache_manager = CacheManager()


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    
    # Create a deterministic key from arguments
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            func_key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = await cache_manager.get(func_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func_key}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func_key}")
            result = await func(*args, **kwargs)
            await cache_manager.set(func_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we'll use asyncio to handle caching
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(async_wrapper(*args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def invalidate_cache(pattern: str = None, key: str = None):
    """Decorator for invalidating cache entries"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Execute function first
            result = await func(*args, **kwargs)
            
            # Invalidate cache
            if key:
                await cache_manager.delete(key)
            elif pattern:
                # For pattern-based invalidation, we'd need to implement key scanning
                # This is a simplified version
                logger.info(f"Cache invalidation requested for pattern: {pattern}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(async_wrapper(*args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Cache strategies
class CacheStrategy:
    """Different caching strategies"""
    
    @staticmethod
    def user_data_ttl(user_id: int) -> int:
        """TTL for user data based on user ID"""
        # Admin users get longer cache
        return 600 if user_id == 1 else 300
    
    @staticmethod
    def image_data_ttl(image_size: int) -> int:
        """TTL for image data based on size"""
        # Larger images get longer cache
        if image_size > 1024 * 1024 * 1024:  # > 1GB
            return 3600  # 1 hour
        elif image_size > 100 * 1024 * 1024:  # > 100MB
            return 1800  # 30 minutes
        else:
            return 900  # 15 minutes
    
    @staticmethod
    def session_data_ttl(session_status: str) -> int:
        """TTL for session data based on status"""
        if session_status in ['starting', 'active']:
            return 60  # 1 minute for active sessions
        else:
            return 1800  # 30 minutes for inactive sessions


# Cache warming functions
async def warm_cache():
    """Warm up frequently accessed cache entries"""
    
    logger.info("Starting cache warming...")
    
    try:
        # Import here to avoid circular imports
        from app.core.database import AsyncSessionLocal
        from app.models.user import User
        from app.models.image import Image
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            # Warm user cache
            users_result = await db.execute(select(User).limit(10))
            users = users_result.scalars().all()
            for user in users:
                await cache_manager.set(f"user:{user.id}", user, CacheStrategy.user_data_ttl(user.id))
            
            # Warm image cache
            images_result = await db.execute(select(Image).limit(20))
            images = images_result.scalars().all()
            for image in images:
                await cache_manager.set(f"image:{image.id}", image, CacheStrategy.image_data_ttl(image.size_bytes))
        
        logger.info("Cache warming completed")
        
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")


# Background cache maintenance
async def cache_maintenance():
    """Background task for cache maintenance"""
    
    while True:
        try:
            # Clean up expired entries
            now = datetime.now()
            expired_keys = []
            
            for key, entry in cache_manager.memory_cache.items():
                if entry['expires'] <= now:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del cache_manager.memory_cache[key]
            
            # Clean up file cache
            for file_path in cache_manager.file_cache_dir.glob("*.cache"):
                try:
                    with open(file_path, 'rb') as f:
                        cache_entry = pickle.load(f)
                        if cache_entry['expires'] <= now:
                            file_path.unlink()
                except Exception:
                    # If we can't read the file, delete it
                    file_path.unlink()
            
            # Wait 5 minutes before next cleanup
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"Cache maintenance error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error
