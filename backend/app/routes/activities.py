"""
Activity Logging API Routes
Activity logs and audit trail
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import structlog

from app.core.dependencies import get_db, require_operator, get_current_user
from app.models.audit import AuditLog
from app.models.user import User
from app.utils.activity_logger import ActivityLogger, ActivityType, ActivityLevel

router = APIRouter(prefix="/activities", tags=["activities"])
logger = structlog.get_logger()


class ActivityResponse(BaseModel):
    id: int
    action: str
    severity: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    message: str
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    resource_name: Optional[str] = None
    timestamp: str
    
    class Config:
        from_attributes = True


class ActivityStatsResponse(BaseModel):
    total: int
    by_level: dict
    by_type: dict


@router.get("", response_model=List[ActivityResponse])
async def get_activities(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    level: Optional[str] = Query(None, description="Filter by level (info, warning, error, critical)"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get activity logs with filters"""
    try:
        activity_logger = ActivityLogger(db)
        
        # Parse activity type
        parsed_activity_type = None
        if activity_type:
            try:
                parsed_activity_type = ActivityType(activity_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid activity_type: {activity_type}"
                )
        
        # Parse level
        parsed_level = None
        if level:
            try:
                parsed_level = ActivityLevel(level)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid level: {level}"
                )
        
        activities = await activity_logger.get_activities(
            user_id=user_id,
            activity_type=parsed_activity_type,
            level=parsed_level,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return [
            ActivityResponse(
                id=activity.id,
                action=activity.action.value,
                severity=activity.severity.value,
                user_id=activity.user_id,
                username=activity.username,
                message=activity.message,
                details=activity.details,
                ip_address=activity.ip_address,
                user_agent=activity.user_agent,
                resource_type=activity.resource_type,
                resource_id=activity.resource_id,
                resource_name=activity.resource_name,
                timestamp=activity.timestamp.isoformat()
            )
            for activity in activities
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get activities", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get activities: {str(e)}"
        )


@router.get("/stats", response_model=ActivityStatsResponse)
async def get_activity_stats(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Get activity statistics"""
    try:
        activity_logger = ActivityLogger(db)
        stats = await activity_logger.get_activity_stats(
            start_date=start_date,
            end_date=end_date
        )
        
        return ActivityStatsResponse(**stats)
    except Exception as e:
        logger.error("Failed to get activity stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get activity stats: {str(e)}"
        )


@router.get("/types")
async def get_activity_types(
    current_user: User = Depends(get_current_user)
):
    """Get list of available activity types"""
    return {
        "activity_types": [activity_type.value for activity_type in ActivityType],
        "levels": [level.value for level in ActivityLevel]
    }

