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
        
        # Skip compression for small responses or non-compressible content
        if (
            response.status_code < 200 or
            response.status_code >= 300 or
            'Content-Encoding' in response.headers or
            int(response.headers.get('Content-Length', 0)) < self.minimum_size
        ):
            return response
        
        # Check Accept-Encoding header
        accept_encoding = request.headers.get('Accept-Encoding', '')
        
        # Prefer Brotli over Gzip
        if 'br' in accept_encoding:
            return await self._compress_brotli(response)
        elif 'gzip' in accept_encoding:
            return await self._compress_gzip(response)
        
        return response
    
    async def _compress_gzip(self, response: Response) -> Response:
        """Compress response using gzip"""
        if isinstance(response, StreamingResponse):
            # Handle streaming responses
            async def compressed_stream():
                compressor = gzip.GzipFile(mode='wb', fileobj=io.BytesIO())
                async for chunk in response.body_iterator:
                    compressor.write(chunk)
                    yield compressor.fileobj.getvalue()
                    compressor.fileobj.seek(0)
                    compressor.fileobj.truncate()
                compressor.close()
            
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
        else:
            # Handle regular responses
            body = b''
            async for chunk in response.body_iterator:
                body += chunk
            
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
    
    async def _compress_brotli(self, response: Response) -> Response:
        """Compress response using brotli"""
        if isinstance(response, StreamingResponse):
            # Handle streaming responses
            async def compressed_stream():
                compressor = brotli.Compressor(quality=4, mode=brotli.MODE_TEXT)
                async for chunk in response.body_iterator:
                    compressed_chunk = compressor.process(chunk)
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
        else:
            # Handle regular responses
            body = b''
            async for chunk in response.body_iterator:
                body += chunk
            
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