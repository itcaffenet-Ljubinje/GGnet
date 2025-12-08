"""
Tests for compression middleware
"""

import pytest
import gzip
import brotli
from fastapi import FastAPI, Response
from httpx import AsyncClient
from app.middleware.compression import CompressionMiddleware


@pytest.fixture
def app_with_compression():
    """Create FastAPI app with compression middleware"""
    app = FastAPI()
    
    @app.get("/large")
    async def get_large_response():
        # Generate response larger than minimum_size
        large_data = "x" * 2000
        return {"data": large_data}
    
    @app.get("/small")
    async def get_small_response():
        return {"data": "small"}
    
    @app.get("/error")
    async def get_error():
        return Response(status_code=404, content="Not found")
    
    app.add_middleware(CompressionMiddleware, minimum_size=1024)
    
    return app


@pytest.mark.asyncio
async def test_compression_middleware_gzip(app_with_compression):
    """Test gzip compression"""
    async with AsyncClient(app=app_with_compression, base_url="http://test") as client:
        response = await client.get(
            "/large",
            headers={"Accept-Encoding": "gzip"}
        )
        assert response.status_code == 200
        assert response.headers.get("Content-Encoding") == "gzip"
        assert "Vary" in response.headers
        assert response.headers["Vary"] == "Accept-Encoding"
        
        # Verify content is compressed
        compressed_data = response.content
        decompressed = gzip.decompress(compressed_data)
        assert len(compressed_data) < len(decompressed)


@pytest.mark.asyncio
async def test_compression_middleware_brotli(app_with_compression):
    """Test brotli compression"""
    async with AsyncClient(app=app_with_compression, base_url="http://test") as client:
        response = await client.get(
            "/large",
            headers={"Accept-Encoding": "br, gzip"}
        )
        assert response.status_code == 200
        assert response.headers.get("Content-Encoding") == "br"
        assert "Vary" in response.headers
        
        # Verify content is compressed
        compressed_data = response.content
        decompressed = brotli.decompress(compressed_data)
        assert len(compressed_data) < len(decompressed)


@pytest.mark.asyncio
async def test_compression_middleware_no_compression_when_not_requested(app_with_compression):
    """Test that compression is not applied when not requested"""
    async with AsyncClient(app=app_with_compression, base_url="http://test") as client:
        response = await client.get("/large")
        assert response.status_code == 200
        assert "Content-Encoding" not in response.headers


@pytest.mark.asyncio
async def test_compression_middleware_skips_small_responses(app_with_compression):
    """Test that small responses are not compressed"""
    async with AsyncClient(app=app_with_compression, base_url="http://test") as client:
        response = await client.get(
            "/small",
            headers={"Accept-Encoding": "gzip"}
        )
        assert response.status_code == 200
        # Small responses should not be compressed
        assert "Content-Encoding" not in response.headers


@pytest.mark.asyncio
async def test_compression_middleware_skips_error_responses(app_with_compression):
    """Test that error responses are not compressed"""
    async with AsyncClient(app=app_with_compression, base_url="http://test") as client:
        response = await client.get(
            "/error",
            headers={"Accept-Encoding": "gzip"}
        )
        assert response.status_code == 404
        # Error responses should not be compressed
        assert "Content-Encoding" not in response.headers


@pytest.mark.asyncio
async def test_compression_middleware_skips_already_compressed(app_with_compression):
    """Test that already compressed responses are not re-compressed"""
    app = FastAPI()
    
    @app.get("/precompressed")
    async def get_precompressed():
        return Response(
            content=gzip.compress(b"compressed data"),
            headers={"Content-Encoding": "gzip"}
        )
    
    app.add_middleware(CompressionMiddleware, minimum_size=1024)
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/precompressed",
            headers={"Accept-Encoding": "gzip"}
        )
        assert response.status_code == 200
        # Should not add another Content-Encoding header
        assert response.headers.get("Content-Encoding") == "gzip"


@pytest.mark.asyncio
async def test_compression_middleware_prefers_brotli_over_gzip(app_with_compression):
    """Test that brotli is preferred over gzip when both are accepted"""
    async with AsyncClient(app=app_with_compression, base_url="http://test") as client:
        response = await client.get(
            "/large",
            headers={"Accept-Encoding": "gzip, br"}
        )
        assert response.status_code == 200
        # Brotli should be preferred
        assert response.headers.get("Content-Encoding") == "br"


@pytest.mark.asyncio
async def test_compression_middleware_content_length_header(app_with_compression):
    """Test that Content-Length header is set correctly"""
    async with AsyncClient(app=app_with_compression, base_url="http://test") as client:
        response = await client.get(
            "/large",
            headers={"Accept-Encoding": "gzip"}
        )
        assert response.status_code == 200
        assert "Content-Length" in response.headers
        content_length = int(response.headers["Content-Length"])
        assert content_length == len(response.content)

