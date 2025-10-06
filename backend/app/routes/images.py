"""
Image management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Request, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, ConfigDict
import structlog
import os
import hashlib
from datetime import datetime
try:
    import magic
except ImportError:
    magic = None
from pathlib import Path
import aiofiles
import uuid

from app.core.database import get_db
from app.core.config import get_settings
from app.core.dependencies import get_current_user, require_admin, log_user_activity
from app.core.cache import cached, invalidate_cache, CacheStrategy
from app.models.user import User
from app.models.image import Image, ImageFormat, ImageStatus, ImageType
from app.models.target import Target
from app.models.audit import AuditAction, AuditSeverity
from app.core.exceptions import ValidationError, StorageError, NotFoundError

router = APIRouter()
logger = structlog.get_logger()
settings = get_settings()


# Pydantic models
class ImageResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    filename: str
    format: ImageFormat
    size_bytes: int
    virtual_size_bytes: Optional[int]
    status: ImageStatus
    image_type: ImageType
    checksum_md5: Optional[str]
    checksum_sha256: Optional[str]
    created_at: datetime
    created_by_username: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ImageCreate(BaseModel):
    name: str
    description: Optional[str] = None
    image_type: ImageType = ImageType.SYSTEM


class ImageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_type: Optional[ImageType] = None


class ImageConvert(BaseModel):
    target_format: ImageFormat
    compress: bool = False


def validate_image_file(file: UploadFile) -> ImageFormat:
    """Validate uploaded image file"""
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower().lstrip('.')
    if file_ext not in settings.allowed_image_formats_list:
        raise ValidationError(f"Unsupported file format: {file_ext}")
    
    # Map extension to format
    format_map = {
        'vhd': ImageFormat.VHD,
        'vhdx': ImageFormat.VHDX,
        'raw': ImageFormat.RAW,
        'qcow2': ImageFormat.QCOW2,
        'vmdk': ImageFormat.VMDK,
        'vdi': ImageFormat.VDI
    }
    
    return format_map.get(file_ext, ImageFormat.RAW)


async def calculate_checksums(file_path: Path) -> tuple:
    """Calculate MD5 and SHA256 checksums for file"""
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()
    
    async with aiofiles.open(file_path, 'rb') as f:
        while chunk := await f.read(8192):
            md5_hash.update(chunk)
            sha256_hash.update(chunk)
    
    return md5_hash.hexdigest(), sha256_hash.hexdigest()


async def process_image_background(image_id: int, file_path: Path, db: AsyncSession):
    """Background task to process uploaded image and trigger conversion"""
    try:
        # Get image record
        result = await db.execute(select(Image).where(Image.id == image_id))
        image = result.scalar_one_or_none()
        
        if not image:
            logger.error("Image not found for processing", image_id=image_id)
            return
        
        # Update status to processing
        image.status = ImageStatus.PROCESSING
        await db.commit()
        
        # Calculate checksums
        md5_checksum, sha256_checksum = await calculate_checksums(file_path)
        
        # Get file size
        file_size = file_path.stat().st_size
        
        # Update image with calculated values
        image.size_bytes = file_size
        image.checksum_md5 = md5_checksum
        image.checksum_sha256 = sha256_checksum
        
        # For VHDX files, keep status as PROCESSING to trigger conversion
        # For other formats, mark as READY
        if image.format == ImageFormat.VHDX:
            image.status = ImageStatus.PROCESSING  # Will be converted by worker
        else:
            image.status = ImageStatus.READY
        
        await db.commit()
        
        logger.info(
            "Image processing completed",
            image_id=image_id,
            size_mb=round(file_size / 1024 / 1024, 2),
            md5=md5_checksum[:8],
            status=image.status.value
        )
        
    except Exception as e:
        logger.error("Image processing failed", image_id=image_id, error=str(e))
        
        # Update image status to error
        try:
            result = await db.execute(select(Image).where(Image.id == image_id))
            image = result.scalar_one_or_none()
            if image:
                image.status = ImageStatus.ERROR
                image.error_message = str(e)
                await db.commit()
        except Exception as db_error:
            logger.error("Failed to update image error status", error=str(db_error))


@router.post("/upload", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
@invalidate_cache(pattern="images:*")
async def upload_image(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    image_type: ImageType = Form(ImageType.SYSTEM),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Upload a new disk image"""
    
    # Validate file
    if not file.filename:
        raise ValidationError("No file provided")
    
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024 / 1024:.1f}GB")
    
    # Validate format
    image_format = validate_image_file(file)
    
    # Check if image name already exists
    result = await db.execute(select(Image).where(Image.name == name))
    if result.scalar_one_or_none():
        raise ValidationError(f"Image with name '{name}' already exists")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix
    unique_filename = f"{file_id}{file_ext}"
    file_path = settings.UPLOAD_DIR / unique_filename
    
    try:
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(8192):
                await f.write(chunk)
        
        # Create image record
        image = Image(
            name=name,
            description=description,
            filename=unique_filename,
            file_path=str(file_path),
            original_filename=file.filename,
            format=image_format,
            image_type=image_type,
            status=ImageStatus.UPLOADING,
            size_bytes=0,  # Will be calculated in background
            created_by=current_user.id
        )
        
        db.add(image)
        await db.commit()
        await db.refresh(image)
        
        # Start background processing
        background_tasks.add_task(process_image_background, image.id, file_path, db)
        
        # Log activity
        await log_user_activity(
            action=AuditAction.IMAGE_UPLOADED,
            message=f"Image '{name}' uploaded",
            request=request,
            user=current_user,
            resource_type="image",
            resource_id=image.id,
            resource_name=name,
            db=db
        )
        
        logger.info(
            "Image upload started",
            image_id=image.id,
            name=name,
            filename=file.filename,
            format=image_format,
            user_id=current_user.id
        )
        
        # Return response with created_by_username
        response_data = ImageResponse.model_validate(image)
        response_data.created_by_username = current_user.username
        
        return response_data
        
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        
        logger.error("Image upload failed", error=str(e), filename=file.filename)
        raise StorageError(f"Failed to upload image: {str(e)}")


@router.get("", response_model=List[ImageResponse])
@cached(ttl=300, key_prefix="images")
async def list_images(
    skip: int = 0,
    limit: int = 100,
    image_type: Optional[ImageType] = None,
    status: Optional[ImageStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all images"""
    
    # Build query
    query = select(Image).join(User, Image.created_by == User.id)
    
    # Add filters
    filters = []
    if image_type:
        filters.append(Image.image_type == image_type)
    if status:
        filters.append(Image.status == status)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Add pagination
    query = query.offset(skip).limit(limit).order_by(Image.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    images = result.scalars().all()
    
    # Build response with usernames
    response_images = []
    for image in images:
        # Get creator username
        creator_result = await db.execute(select(User).where(User.id == image.created_by))
        creator = creator_result.scalar_one_or_none()
        
        response_data = ImageResponse.model_validate(image)
        response_data.created_by_username = creator.username if creator else "Unknown"
        response_images.append(response_data)
    
    return response_images


@router.get("/{image_id}", response_model=ImageResponse)
@cached(ttl=600, key_prefix="image")
async def get_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get image by ID"""
    
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    
    if not image:
        raise NotFoundError(f"Image with ID {image_id} not found")
    
    # Get creator username
    creator_result = await db.execute(select(User).where(User.id == image.created_by))
    creator = creator_result.scalar_one_or_none()
    
    response_data = ImageResponse.model_validate(image)
    response_data.created_by_username = creator.username if creator else "Unknown"
    
    return response_data


@router.put("/{image_id}", response_model=ImageResponse)
@invalidate_cache(key="image:{image_id}")
async def update_image(
    image_id: int,
    image_update: ImageUpdate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update image metadata"""
    
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    
    if not image:
        raise NotFoundError(f"Image with ID {image_id} not found")
    
    # Store old values for audit
    old_values = {
        "name": image.name,
        "description": image.description,
        "image_type": image.image_type
    }
    
    # Update fields
    if image_update.name is not None:
        # Check if new name already exists
        result = await db.execute(
            select(Image).where(and_(Image.name == image_update.name, Image.id != image_id))
        )
        if result.scalar_one_or_none():
            raise ValidationError(f"Image with name '{image_update.name}' already exists")
        image.name = image_update.name
    
    if image_update.description is not None:
        image.description = image_update.description
    
    if image_update.image_type is not None:
        image.image_type = image_update.image_type
    
    await db.commit()
    await db.refresh(image)
    
    # Log activity
    new_values = {
        "name": image.name,
        "description": image.description,
        "image_type": image.image_type
    }
    
    await log_user_activity(
        action=AuditAction.IMAGE_UPDATED,
        message=f"Image '{image.name}' updated",
        request=request,
        user=current_user,
        resource_type="image",
        resource_id=image.id,
        resource_name=image.name,
        db=db
    )
    
    logger.info("Image updated", image_id=image_id, user_id=current_user.id)
    
    # Get creator username for response
    creator_result = await db.execute(select(User).where(User.id == image.created_by))
    creator = creator_result.scalar_one_or_none()
    
    response_data = ImageResponse.model_validate(image)
    response_data.created_by_username = creator.username if creator else "Unknown"
    
    return response_data


@router.delete("/{image_id}")
@invalidate_cache(pattern="images:*", key="image:{image_id}")
async def delete_image(
    image_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete an image"""
    
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    
    if not image:
        raise NotFoundError(f"Image with ID {image_id} not found")
    
    # Check if image is being used by any targets
    # Check for active targets using this image
    active_targets_result = await db.execute(
        select(Target).where(
            Target.image_id == image_id,
            Target.is_active == True
        )
    )
    active_targets = active_targets_result.scalars().all()
    
    if active_targets:
        target_names = [target.name for target in active_targets]
        raise ValidationError(
            f"Cannot delete image '{image.name}' - it is being used by active targets: {', '.join(target_names)}"
        )
    
    # Delete file from disk
    file_path = Path(image.file_path)
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            logger.error("Failed to delete image file", image_id=image_id, error=str(e))
    
    # Update status to deleted (soft delete)
    image.status = ImageStatus.DELETED
    
    await db.commit()
    
    # Log activity
    await log_user_activity(
        action=AuditAction.IMAGE_DELETED,
        message=f"Image '{image.name}' deleted",
        request=request,
        user=current_user,
        resource_type="image",
        resource_id=image.id,
        resource_name=image.name,
        db=db
    )
    
    logger.info("Image deleted", image_id=image_id, name=image.name, user_id=current_user.id)
    
    return {"message": f"Image '{image.name}' deleted successfully"}


@router.post("/{image_id}/convert")
async def trigger_conversion(
    image_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger image conversion"""
    
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    
    if not image:
        raise NotFoundError(f"Image with ID {image_id} not found")
    
    if image.status not in [ImageStatus.READY, ImageStatus.ERROR]:
        raise ValidationError(f"Image must be in READY or ERROR status to convert. Current status: {image.status}")
    
    # Update status to processing to trigger conversion
    image.status = ImageStatus.PROCESSING
    await db.commit()
    
    await log_user_activity(
        action=AuditAction.IMAGE_UPLOADED,
        message=f"Conversion triggered for image '{image.name}'",
        request=request,
        user=current_user,
        resource_type="image",
        resource_id=image.id,
        resource_name=image.name,
        db=db
    )
    
    logger.info(f"Conversion triggered for image {image_id} by user {current_user.username}")
    
    return {"message": "Conversion triggered successfully", "image_id": image_id}


@router.get("/{image_id}/conversion-status")
async def get_conversion_status(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversion status and progress for an image"""
    
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    
    if not image:
        raise NotFoundError(f"Image with ID {image_id} not found")
    
    # Parse processing log if available
    processing_info = {}
    if image.processing_log:
        try:
            import json
            processing_info = json.loads(image.processing_log)
        except (json.JSONDecodeError, TypeError):
            processing_info = {"raw_log": image.processing_log}
    
    return {
        "image_id": image.id,
        "name": image.name,
        "status": image.status,
        "format": image.format,
        "size_bytes": image.size_bytes,
        "virtual_size_bytes": image.virtual_size_bytes,
        "error_message": image.error_message,
        "processing_info": processing_info,
        "created_at": image.created_at.isoformat(),
        "updated_at": image.updated_at.isoformat()
    }

