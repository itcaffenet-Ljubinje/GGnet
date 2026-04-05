"""
Settings management endpoints
Provides endpoints for managing various system settings (trim, boot, network, images)
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import structlog

from app.core.dependencies import get_db, get_current_user, require_operator
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["settings"])
logger = structlog.get_logger()


# Pydantic models for settings
class TrimSettings(BaseModel):
    """TRIM settings model"""
    enabled: bool = False
    schedule: Optional[str] = None  # Cron expression
    last_run: Optional[str] = None
    next_run: Optional[str] = None


class BootSettings(BaseModel):
    """Boot settings model"""
    default_boot_mode: Optional[str] = "uefi"  # uefi, legacy
    secure_boot_enabled: bool = True
    timeout_seconds: int = 30
    auto_boot_enabled: bool = True


class NetworkSettings(BaseModel):
    """Network settings model"""
    bridge_name: Optional[str] = "virbr0"
    dhcp_enabled: bool = True
    tftp_enabled: bool = True
    dns_servers: Optional[list] = None
    gateway: Optional[str] = None
    subnet_mask: Optional[str] = None


class ImageSettings(BaseModel):
    """Image settings model"""
    default_storage_path: Optional[str] = "/var/lib/ggnet/images"
    max_image_size_gb: int = 100
    allowed_formats: Optional[list] = None
    compression_enabled: bool = False
    auto_cleanup_enabled: bool = True


# In-memory settings storage (in production, this should be in database)
_settings_cache: Dict[str, Any] = {
    "trim": {
        "enabled": False,
        "schedule": None,
        "last_run": None,
        "next_run": None
    },
    "boot": {
        "default_boot_mode": "uefi",
        "secure_boot_enabled": True,
        "timeout_seconds": 30,
        "auto_boot_enabled": True
    },
    "network": {
        "bridge_name": "virbr0",
        "dhcp_enabled": True,
        "tftp_enabled": True,
        "dns_servers": ["8.8.8.8", "8.8.4.4"],
        "gateway": None,
        "subnet_mask": None
    },
    "images": {
        "default_storage_path": "/var/lib/ggnet/images",
        "max_image_size_gb": 100,
        "allowed_formats": ["vhd", "vhdx", "raw", "qcow2"],
        "compression_enabled": False,
        "auto_cleanup_enabled": True
    }
}


@router.get("/trim", response_model=TrimSettings)
async def get_trim_settings(
    current_user: User = Depends(get_current_user)
):
    """
    Get TRIM configuration settings
    """
    try:
        settings = _settings_cache.get("trim", {})
        return TrimSettings(**settings)
    except Exception as e:
        logger.error("Failed to get TRIM settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get TRIM settings: {str(e)}"
        )


@router.put("/trim", response_model=TrimSettings)
async def update_trim_settings(
    settings: TrimSettings,
    current_user: User = Depends(require_operator)
):
    """
    Update TRIM configuration settings
    """
    try:
        _settings_cache["trim"] = settings.model_dump()
        logger.info("TRIM settings updated", user_id=current_user.id, settings=settings.model_dump())
        return settings
    except Exception as e:
        logger.error("Failed to update TRIM settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update TRIM settings: {str(e)}"
        )


@router.get("/boot", response_model=BootSettings)
async def get_boot_settings(
    current_user: User = Depends(get_current_user)
):
    """
    Get boot configuration settings
    """
    try:
        settings = _settings_cache.get("boot", {})
        return BootSettings(**settings)
    except Exception as e:
        logger.error("Failed to get boot settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get boot settings: {str(e)}"
        )


@router.put("/boot", response_model=BootSettings)
async def update_boot_settings(
    settings: BootSettings,
    current_user: User = Depends(require_operator)
):
    """
    Update boot configuration settings
    """
    try:
        _settings_cache["boot"] = settings.model_dump()
        logger.info("Boot settings updated", user_id=current_user.id, settings=settings.model_dump())
        return settings
    except Exception as e:
        logger.error("Failed to update boot settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update boot settings: {str(e)}"
        )


@router.get("/network", response_model=NetworkSettings)
async def get_network_settings(
    current_user: User = Depends(get_current_user)
):
    """
    Get network configuration settings
    """
    try:
        settings = _settings_cache.get("network", {})
        return NetworkSettings(**settings)
    except Exception as e:
        logger.error("Failed to get network settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get network settings: {str(e)}"
        )


@router.put("/network", response_model=NetworkSettings)
async def update_network_settings(
    settings: NetworkSettings,
    current_user: User = Depends(require_operator)
):
    """
    Update network configuration settings
    """
    try:
        _settings_cache["network"] = settings.model_dump()
        logger.info("Network settings updated", user_id=current_user.id, settings=settings.model_dump())
        return settings
    except Exception as e:
        logger.error("Failed to update network settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update network settings: {str(e)}"
        )


@router.get("/images", response_model=ImageSettings)
async def get_image_settings(
    current_user: User = Depends(get_current_user)
):
    """
    Get image configuration settings
    """
    try:
        settings = _settings_cache.get("images", {})
        return ImageSettings(**settings)
    except Exception as e:
        logger.error("Failed to get image settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get image settings: {str(e)}"
        )


@router.put("/images", response_model=ImageSettings)
async def update_image_settings(
    settings: ImageSettings,
    current_user: User = Depends(require_operator)
):
    """
    Update image configuration settings
    """
    try:
        _settings_cache["images"] = settings.model_dump()
        logger.info("Image settings updated", user_id=current_user.id, settings=settings.model_dump())
        return settings
    except Exception as e:
        logger.error("Failed to update image settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update image settings: {str(e)}"
        )

