"""
Compression middleware for FastAPI
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
import gzip
import brotli
from typing import Callable, AsyncGenerator
import io


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to compress responses using gzip or brotli based on Accept-Encoding header
    """
    
    def __init__(self, app, minimum_size: int = 1024):
        super().__init__(app)
        self.minimum_size = minimum_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Skip compression for error responses or already compressed content
        if (
            response.status_code < 200 or
            response.status_code >= 300 or
            'Content-Encoding' in response.headers
        ):
            return response
        
        # Check Accept-Encoding header - if not present, skip compression
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if not accept_encoding:
            return response
        
        # Handle StreamingResponse differently - compress the stream
        if isinstance(response, StreamingResponse):
            # Prefer Brotli over Gzip
            if 'br' in accept_encoding:
                return await self._compress_brotli_stream(response)
            elif 'gzip' in accept_encoding:
                return await self._compress_gzip_stream(response)
            return response
        
        # Handle regular Response - read body to check size
        body = b''
        async for chunk in response.body_iterator:
            body += chunk
        
        # Skip compression for small responses
        if len(body) < self.minimum_size:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        
        # Prefer Brotli over Gzip
        if 'br' in accept_encoding:
            return self._compress_brotli(body, response)
        elif 'gzip' in accept_encoding:
            return self._compress_gzip(body, response)
        
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
    
    def _compress_gzip(self, body: bytes, response: Response) -> Response:
        """Compress response using gzip"""
        compressed = gzip.compress(body, compresslevel=6)
        
        return Response(
            content=compressed,
            status_code=response.status_code,
            headers={
                **dict(response.headers),
                'Content-Encoding': 'gzip',
                'Content-Length': str(len(compressed)),
                'Vary': 'Accept-Encoding'
            },
            media_type=response.media_type
        )
    
    def _compress_brotli(self, body: bytes, response: Response) -> Response:
        """Compress response using brotli"""
        compressed = brotli.compress(body, quality=4, mode=brotli.MODE_TEXT)
        
        return Response(
            content=compressed,
            status_code=response.status_code,
            headers={
                **dict(response.headers),
                'Content-Encoding': 'br',
                'Content-Length': str(len(compressed)),
                'Vary': 'Accept-Encoding'
            },
            media_type=response.media_type
        )
    
    async def _compress_gzip_stream(self, response: StreamingResponse) -> StreamingResponse:
        """Compress streaming response using gzip"""
        async def compressed_stream() -> AsyncGenerator[bytes, None]:
            buffer = io.BytesIO()
            compressor = gzip.GzipFile(mode='wb', fileobj=buffer, compresslevel=6)
            try:
                async for chunk in response.body_iterator:
                    chunk_bytes = chunk if isinstance(chunk, bytes) else chunk.encode()
                    compressor.write(chunk_bytes)
                    # Flush to ensure data is written to buffer
                    compressor.flush()
                    # Get compressed data from buffer
                    compressed_data = buffer.getvalue()
                    if compressed_data:
                        yield compressed_data
                    # Reset buffer for next iteration
                    buffer.seek(0)
                    buffer.truncate()
            finally:
                compressor.close()
                # Yield any remaining data after closing
                final_data = buffer.getvalue()
                if final_data:
                    yield final_data
        
        return StreamingResponse(
            compressed_stream(),
            status_code=response.status_code,
            headers={
                **dict(response.headers),
                'Content-Encoding': 'gzip',
                'Vary': 'Accept-Encoding'
            },
            media_type=response.media_type
        )
    
    async def _compress_brotli_stream(self, response: StreamingResponse) -> StreamingResponse:
        """Compress streaming response using brotli"""
        async def compressed_stream() -> AsyncGenerator[bytes, None]:
            compressor = brotli.Compressor(quality=4, mode=brotli.MODE_TEXT)
            async for chunk in response.body_iterator:
                chunk_bytes = chunk if isinstance(chunk, bytes) else chunk.encode()
                compressed_chunk = compressor.process(chunk_bytes)
                if compressed_chunk:
                    yield compressed_chunk
            final_chunk = compressor.finish()
            if final_chunk:
                yield final_chunk
        
        return StreamingResponse(
            compressed_stream(),
            status_code=response.status_code,
            headers={
                **dict(response.headers),
                'Content-Encoding': 'br',
                'Vary': 'Accept-Encoding'
            },
            media_type=response.media_type
        )