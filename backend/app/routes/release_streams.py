"""
Release streams API endpoints
Provides endpoints for managing release streams
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import structlog

from app.core.dependencies import get_db, get_current_user, require_operator
from app.models.user import User

router = APIRouter(prefix="/server/releaseStreams", tags=["server-release-streams"])
logger = structlog.get_logger()


class ReleaseStream(BaseModel):
    """Release stream model"""
    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    selected: bool = False
    available: bool = True


# In-memory release streams storage (in production, use database)
_release_streams: List[Dict[str, Any]] = [
    {
        "name": "stable",
        "description": "Stable release stream",
        "version": "1.0.0",
        "selected": True,
        "available": True
    },
    {
        "name": "beta",
        "description": "Beta release stream",
        "version": "1.1.0-beta",
        "selected": False,
        "available": True
    },
    {
        "name": "alpha",
        "description": "Alpha release stream",
        "version": "1.2.0-alpha",
        "selected": False,
        "available": True
    }
]


@router.get("", response_model=List[ReleaseStream])
async def list_release_streams(
    current_user: User = Depends(get_current_user)
):
    """
    List available release streams
    """
    try:
        return [ReleaseStream(**stream) for stream in _release_streams]
    except Exception as e:
        logger.error("Failed to list release streams", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list release streams: {str(e)}"
        )


@router.post("/{name}/select", response_model=Dict[str, Any])
async def select_release_stream(
    name: str,
    current_user: User = Depends(require_operator)
):
    """
    Select a release stream
    """
    try:
        # Find release stream
        stream = next((s for s in _release_streams if s["name"] == name), None)
        if not stream:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Release stream '{name}' not found"
            )
        
        if not stream["available"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Release stream '{name}' is not available"
            )
        
        # Deselect all streams
        for s in _release_streams:
            s["selected"] = False
        
        # Select the requested stream
        stream["selected"] = True
        
        logger.info("Release stream selected", stream_name=name, user_id=current_user.id)
        
        return {
            "name": name,
            "selected": True,
            "message": f"Release stream '{name}' selected successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to select release stream", stream_name=name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to select release stream: {str(e)}"
        )

