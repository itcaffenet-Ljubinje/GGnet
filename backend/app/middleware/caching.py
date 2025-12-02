"""
Caching middleware for FastAPI with Redis support
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional, Dict, Any
import hashlib
import json
import time
from datetime import datetime, timedelta
import redis.asyncio as redis
import structlog

logger = structlog.get_logger()


class CacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to cache GET responses in Redis for improved performance
    """
    
    def __init__(
        self, 
        app, 
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 300,  # 5 minutes
        cache_paths: Optional[Dict[str, int]] = None
    ):
        super().__init__(app)
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.cache_paths = cache_paths or {
            "/api/images": 300,
            "/api/machines": 300,
            "/api/storage/info": 60,
            "/api/health": 30,
            "/api/monitoring/metrics": 10,
        }
        self.redis_client = None
    
    async def _get_redis(self) -> Optional[redis.Redis]:
        """Get or create Redis connection"""
        if not self.redis_client:
            try:
                self.redis_client = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                return None
        return self.redis_client
    
    def _should_cache(self, request: Request) -> bool:
        """Determine if request should be cached"""
        if request.method != "GET":
            return False
        
        # Check if path matches any cache patterns
        path = str(request.url.path)
        for cache_path in self.cache_paths.keys():
            if path.startswith(cache_path):
                return True
        
        return False
    
    def _get_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        # Include query parameters in cache key
        url = str(request.url)
        # Include auth header to separate cache per user
        auth = request.headers.get("Authorization", "")
        
        key_data = f"{request.method}:{url}:{auth}"
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()
        
        return f"cache:{key_hash}"
    
    def _get_ttl(self, request: Request) -> int:
        """Get TTL for specific path"""
        path = str(request.url.path)
        for cache_path, ttl in self.cache_paths.items():
            if path.startswith(cache_path):
                return ttl
        return self.default_ttl
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip caching if not applicable
        if not self._should_cache(request):
            return await call_next(request)
        
        # Get Redis client
        redis_client = await self._get_redis()
        if not redis_client:
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._get_cache_key(request)
        
        try:
            # Check cache
            cached = await redis_client.get(cache_key)
            if cached:
                cached_data = json.loads(cached)
                
                # Check if cache is still valid
                if cached_data.get("expires", 0) > time.time():
                    logger.debug(f"Cache hit for {request.url.path}")
                    
                    return Response(
                        content=cached_data["body"],
                        status_code=cached_data["status_code"],
                        headers={
                            **cached_data["headers"],
                            "X-Cache": "HIT",
                            "X-Cache-Key": cache_key[-8:],
                            "Cache-Control": f"max-age={self._get_ttl(request)}"
                        },
                        media_type=cached_data.get("media_type", "application/json")
                    )
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        # Cache miss - get response
        response = await call_next(request)
        
        # Only cache successful responses
        if 200 <= response.status_code < 300:
            try:
                # Read response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                # Cache response
                ttl = self._get_ttl(request)
                cache_data = {
                    "body": body.decode("utf-8") if body else "",
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "media_type": response.media_type,
                    "expires": time.time() + ttl,
                    "cached_at": datetime.utcnow().isoformat()
                }
                
                await redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(cache_data)
                )
                
                logger.debug(f"Cached response for {request.url.path} (TTL: {ttl}s)")
                
                # Return response with cache headers
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers={
                        **dict(response.headers),
                        "X-Cache": "MISS",
                        "Cache-Control": f"max-age={ttl}",
                        "Vary": "Accept-Encoding, Authorization"
                    },
                    media_type=response.media_type
                )
                
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
        
        return response
    
    async def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries"""
        redis_client = await self._get_redis()
        if not redis_client:
            return
        
        try:
            if pattern:
                keys = await redis_client.keys(f"cache:*{pattern}*")
            else:
                keys = await redis_client.keys("cache:*")
            
            if keys:
                await redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")