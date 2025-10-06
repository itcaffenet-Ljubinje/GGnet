"""
File upload and conversion endpoints for diskless server
"""

import os
import shutil
import asyncio
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, Request, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict
import structlog
import subprocess
import tempfile
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_operator, log_user_activity
from app.models.user import User
from app.models.image import Image, ImageFormat, ImageStatus
from app.models.audit import AuditAction
from app.core.exceptions import ValidationError, NotFoundError

router = APIRouter()
logger = structlog.get_logger()

# Configuration
UPLOAD_DIR = Path("/opt/ggnet/images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024 * 1024  # 50GB
ALLOWED_EXTENSIONS = {".vhd", ".vhdx", ".iso", ".img", ".raw", ".qcow2"}


class UploadResponse(BaseModel):
    id: int
    filename: str
    original_size: int
    converted_size: Optional[int]
    status: ImageStatus
    format: ImageFormat
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ConversionTask(BaseModel):
    id: str
    image_id: int
    status: str
    progress: int
    message: str
    created_at: datetime


# In-memory storage for conversion tasks (in production, use Redis)
conversion_tasks = {}


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    format: ImageFormat = Form(ImageFormat.VHD),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Upload and convert image file"""
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise ValidationError(f"File too large. Maximum size: {MAX_FILE_SIZE // (1024**3)}GB")
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_')
    filename = f"{safe_name}_{timestamp}{file_ext}"
    file_path = UPLOAD_DIR / filename
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Get file size
        file_size = file_path.stat().st_size
        
        # Create database record
        image = Image(
            name=name,
            description=description,
            filename=filename,
            file_path=str(file_path),
            file_size=file_size,
            format=format,
            status=ImageStatus.UPLOADING,
            created_by=current_user.id
        )
        
        db.add(image)
        await db.commit()
        await db.refresh(image)
        
        # Start conversion in background if needed
        if file_ext in [".vhd", ".vhdx"] and format in [ImageFormat.RAW, ImageFormat.QCOW2]:
            task_id = f"conv_{image.id}_{timestamp}"
            conversion_tasks[task_id] = ConversionTask(
                id=task_id,
                image_id=image.id,
                status="pending",
                progress=0,
                message="Queued for conversion",
                created_at=datetime.now()
            )
            background_tasks.add_task(convert_image, image.id, task_id)
        
        # Log activity
        await log_user_activity(
            action=AuditAction.CREATE,
            message=f"Uploaded image: {name}",
            request=request,
            user=current_user,
            resource_type="images"
        )
        
        logger.info("Image uploaded successfully", 
                   image_id=image.id, 
                   filename=filename, 
                   size=file_size,
                   user_id=current_user.id)
        
        return UploadResponse(
            id=image.id,
            filename=filename,
            original_size=file_size,
            converted_size=None,
            status=image.status,
            format=image.format,
            created_at=image.created_at
        )
        
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        logger.error("Image upload failed", error=str(e), filename=filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


async def convert_image(image_id: int, task_id: str):
    """Convert image format in background"""
    try:
        # Update task status
        if task_id in conversion_tasks:
            conversion_tasks[task_id].status = "converting"
            conversion_tasks[task_id].message = "Converting image format..."
        
        # Get image from database
        from app.core.database import async_engine
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select
        
        async with AsyncSession(async_engine) as db:
            result = await db.execute(select(Image).where(Image.id == image_id))
            image = result.scalar_one_or_none()
            
            if not image:
                raise NotFoundError(f"Image {image_id} not found")
            
            # Update status
            image.status = ImageStatus.CONVERTING
            await db.commit()
            
            # Determine conversion command
            source_path = Path(image.file_path)
            target_format = image.format
            
            if source_path.suffix.lower() == ".vhd" and target_format == ImageFormat.RAW:
                target_path = source_path.with_suffix(".raw")
                cmd = ["qemu-img", "convert", "-f", "vpc", "-O", "raw", str(source_path), str(target_path)]
            elif source_path.suffix.lower() == ".vhdx" and target_format == ImageFormat.RAW:
                target_path = source_path.with_suffix(".raw")
                cmd = ["qemu-img", "convert", "-f", "vhdx", "-O", "raw", str(source_path), str(target_path)]
            elif source_path.suffix.lower() in [".vhd", ".vhdx"] and target_format == ImageFormat.QCOW2:
                target_path = source_path.with_suffix(".qcow2")
                cmd = ["qemu-img", "convert", "-f", "vpc", "-O", "qcow2", str(source_path), str(target_path)]
            else:
                raise ValidationError(f"Unsupported conversion: {source_path.suffix} to {target_format}")
            
            # Run conversion
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Conversion failed: {stderr.decode()}")
            
            # Update image record
            image.file_path = str(target_path)
            image.filename = target_path.name
            image.file_size = target_path.stat().st_size
            image.status = ImageStatus.READY
            await db.commit()
            
            # Remove original file
            if source_path.exists() and source_path != target_path:
                source_path.unlink()
            
            # Update task status
            if task_id in conversion_tasks:
                conversion_tasks[task_id].status = "completed"
                conversion_tasks[task_id].progress = 100
                conversion_tasks[task_id].message = "Conversion completed successfully"
            
            logger.info("Image conversion completed", 
                       image_id=image_id, 
                       target_format=target_format,
                       new_size=image.file_size)
            
    except Exception as e:
        # Update task status on error
        if task_id in conversion_tasks:
            conversion_tasks[task_id].status = "failed"
            conversion_tasks[task_id].message = f"Conversion failed: {str(e)}"
        
        # Update image status
        try:
            from app.core.database import async_engine
            from sqlalchemy.ext.asyncio import AsyncSession
            from sqlalchemy import select
            
            async with AsyncSession(async_engine) as db:
                result = await db.execute(select(Image).where(Image.id == image_id))
                image = result.scalar_one_or_none()
                if image:
                    image.status = ImageStatus.ERROR
                    await db.commit()
        except:
            pass
        
        logger.error("Image conversion failed", 
                    image_id=image_id, 
                    error=str(e))


@router.get("/conversion-tasks/{task_id}", response_model=ConversionTask)
async def get_conversion_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get conversion task status"""
    
    if task_id not in conversion_tasks:
        raise NotFoundError("Conversion task not found")
    
    return conversion_tasks[task_id]


@router.get("/conversion-tasks", response_model=List[ConversionTask])
async def list_conversion_tasks(
    current_user: User = Depends(require_operator)
):
    """List all conversion tasks"""
    
    return list(conversion_tasks.values())


@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    request: Request,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Delete image file and database record"""
    
    # Get image
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    
    if not image:
        raise NotFoundError("Image not found")
    
    # Check if image is in use
    from app.models.session import Session, SessionStatus
    result = await db.execute(
        select(Session).where(
            Session.image_id == image_id,
            Session.status.in_([SessionStatus.ACTIVE, SessionStatus.STARTING])
        )
    )
    if result.scalar_one_or_none():
        raise ValidationError("Cannot delete image that is currently in use")
    
    try:
        # Delete file
        file_path = Path(image.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Delete database record
        await db.delete(image)
        await db.commit()
        
        # Log activity
        await log_user_activity(
            action=AuditAction.DELETE,
            message=f"Deleted image: {image.name}",
            request=request,
            user=current_user,
            resource_type="images"
        )
        
        logger.info("Image deleted successfully", 
                   image_id=image_id, 
                   filename=image.filename,
                   user_id=current_user.id)
        
        return {"message": "Image deleted successfully"}
        
    except Exception as e:
        logger.error("Image deletion failed", error=str(e), image_id=image_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion failed: {str(e)}"
        )


@router.get("/disk-usage")
async def get_disk_usage(
    current_user: User = Depends(get_current_user)
):
    """Get disk usage statistics"""
    
    try:
        # Get total disk space
        total, used, free = shutil.disk_usage(UPLOAD_DIR)
        
        # Get image file sizes
        from app.core.database import async_engine
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select, func
        
        async with AsyncSession(async_engine) as db:
            result = await db.execute(
                select(func.sum(Image.file_size)).where(Image.status == ImageStatus.READY)
            )
            total_image_size = result.scalar() or 0
        
        return {
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "total_images_size": total_image_size,
            "upload_directory": str(UPLOAD_DIR),
            "usage_percentage": round((used / total) * 100, 2)
        }
        
    except Exception as e:
        logger.error("Failed to get disk usage", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get disk usage: {str(e)}"
        )
