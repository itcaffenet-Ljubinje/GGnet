"""
Image Import/Export API endpoints
Import images from external sources and export images to various formats
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import structlog

from app.core.dependencies import get_db, require_operator, get_current_user
from app.models.user import User
from app.models.image import Image, ImageFormat, ImageType
from app.utils.image_import_export import ImageImportExportManager, ImageImportExportError

router = APIRouter(prefix="/images/import-export", tags=["image-import-export"])
logger = structlog.get_logger()


class ImageImportRequest(BaseModel):
    """Image import request"""
    name: str
    source_path: str
    image_type: ImageType = ImageType.SYSTEM
    description: Optional[str] = None


class ImageExportRequest(BaseModel):
    """Image export request"""
    destination_path: Optional[str] = None
    format: Optional[ImageFormat] = None
    compress: bool = False


class ImageExportDownloadRequest(BaseModel):
    """Image export for download request"""
    format: Optional[ImageFormat] = None
    compress: bool = False


@router.post("/import", response_model=Dict[str, Any])
async def import_image(
    request: ImageImportRequest = Body(...),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Import an image from external source
    
    Args:
        request: Import request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Import result with image ID
    """
    try:
        manager = ImageImportExportManager()
        image = await manager.import_image(
            db=db,
            name=request.name,
            source_path=request.source_path,
            image_type=request.image_type,
            description=request.description,
            created_by=current_user.id
        )
        
        return {
            "id": image.id,
            "name": image.name,
            "format": image.format.value,
            "size_bytes": image.size_bytes,
            "status": image.status.value,
            "message": "Image imported successfully",
        }
    except ImageImportExportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to import image", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import image: {str(e)}"
        )


@router.post("/import/upload", response_model=Dict[str, Any])
async def import_image_upload(
    file: UploadFile = File(...),
    name: str = Body(...),
    image_type: ImageType = Body(ImageType.SYSTEM),
    description: Optional[str] = Body(None),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Import an image by uploading a file
    
    Args:
        file: Image file to upload
        name: Image name
        image_type: Image type
        description: Optional description
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Import result with image ID
    """
    try:
        from app.core.config import get_settings
        import aiofiles
        import uuid
        from pathlib import Path
        
        settings = get_settings()
        import_dir = Path(settings.IMAGE_STORAGE_PATH) / "imports"
        import_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file temporarily
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        temp_path = import_dir / f"{file_id}{file_ext}"
        
        async with aiofiles.open(temp_path, 'wb') as f:
            while chunk := await file.read(8192):
                await f.write(chunk)
        
        # Import from temporary path
        manager = ImageImportExportManager()
        image = await manager.import_image(
            db=db,
            name=name,
            source_path=str(temp_path),
            image_type=image_type,
            description=description,
            created_by=current_user.id
        )
        
        # Clean up temporary file
        try:
            temp_path.unlink()
        except Exception:
            pass
        
        return {
            "id": image.id,
            "name": image.name,
            "format": image.format.value,
            "size_bytes": image.size_bytes,
            "status": image.status.value,
            "message": "Image imported successfully",
        }
    except ImageImportExportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to import image from upload", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import image: {str(e)}"
        )


@router.post("/{image_id}/export", response_model=Dict[str, Any])
async def export_image(
    image_id: int,
    request: ImageExportRequest = Body(...),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Export an image to external destination
    
    Args:
        image_id: Image ID
        request: Export request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Export result
    """
    try:
        manager = ImageImportExportManager()
        result = await manager.export_image(
            db=db,
            image_id=image_id,
            destination_path=request.destination_path,
            target_format=request.format,
            compress=request.compress,
        )
        
        return result
    except ImageImportExportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to export image", image_id=image_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export image: {str(e)}"
        )


@router.post("/{image_id}/export/download", response_model=Dict[str, Any])
async def export_image_download(
    image_id: int,
    request: ImageExportDownloadRequest = Body(...),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Export image and return download URL
    
    Args:
        image_id: Image ID
        request: Export request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Download URL and export info
    """
    try:
        manager = ImageImportExportManager()
        result = await manager.export_image_for_download(
            db=db,
            image_id=image_id,
            target_format=request.format,
            compress=request.compress,
        )
        
        return result
    except ImageImportExportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to export image for download", image_id=image_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export image: {str(e)}"
        )


@router.get("/{image_id}/export/status", response_model=Dict[str, Any])
async def get_export_status(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get export status for an image
    
    Args:
        image_id: Image ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Export status
    """
    try:
        manager = ImageImportExportManager()
        return await manager.get_export_status(db, image_id)
    except ImageImportExportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to get export status", image_id=image_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get export status: {str(e)}"
        )


@router.get("/{image_id}/export/download/{filename}")
async def download_exported_image(
    image_id: int,
    filename: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download an exported image file
    
    Args:
        image_id: Image ID
        filename: Export filename
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        File response
    """
    try:
        from fastapi.responses import FileResponse
        from app.core.config import get_settings
        from pathlib import Path
        
        settings = get_settings()
        export_dir = Path(settings.IMAGE_STORAGE_PATH) / "exports"
        file_path = export_dir / filename
        
        # Verify file exists and belongs to image
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exported file not found"
            )
        
        # Verify filename matches image
        if not filename.startswith(f"image_{image_id}_") and not filename.startswith(f"{image_id}."):
            # Additional check: get image name
            from sqlalchemy import select
            from app.models.image import Image
            
            stmt = select(Image).where(Image.id == image_id)
            result = await db.execute(stmt)
            image = result.scalar_one_or_none()
            
            if not image or filename not in [f"{image.name}_{image_id}.{ext}" for ext in ["vhd", "vhdx", "raw", "qcow2", "vmdk", "vdi"]]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="File does not belong to this image"
                )
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to download exported image", image_id=image_id, filename=filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download exported image: {str(e)}"
        )

