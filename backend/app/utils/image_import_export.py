"""
Image Import/Export Manager
Handles importing images from external sources and exporting images to various formats
"""

import os
import shutil
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog
import uuid

from app.models.image import Image, ImageFormat, ImageStatus, ImageType
from app.core.config import get_settings

logger = structlog.get_logger()

# Try to import ImageConverter from scripts directory
# Add project root to path if needed
try:
    # Try multiple possible paths for scripts directory
    current_file = Path(__file__).resolve()
    # From backend/app/utils/image_import_export.py -> project root/scripts
    project_root = current_file.parent.parent.parent.parent
    scripts_path = project_root / "scripts"
    
    # Also try relative to current working directory
    if not scripts_path.exists():
        scripts_path = Path.cwd() / "scripts"
    
    # Add project root to Python path if scripts directory exists
    if scripts_path.exists() and (scripts_path / "image_converter.py").exists():
        project_root_str = str(project_root)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)
    
    from scripts.image_converter import ImageConverter, ImageConversionError
except (ImportError, AttributeError, ValueError):
    # Fallback: define minimal ImageConverter if import fails
    logger.warning("Could not import ImageConverter from scripts, using fallback implementation")
    
    class ImageConversionError(Exception):
        """Custom exception for image conversion operations"""
        pass
    
    class ImageConverter:
        """Fallback ImageConverter when scripts module is not available"""
        
        def __init__(self, qemu_img_path: str = "/usr/bin/qemu-img", mock_mode: bool = False):
            self.qemu_img_path = qemu_img_path
            self.mock_mode = mock_mode
        
        def get_image_info(self, image_path: str) -> Dict[str, Any]:
            """Get basic image info (fallback implementation)"""
            if not os.path.exists(image_path):
                raise ImageConversionError(f"Image file not found: {image_path}")
            
            file_size = os.path.getsize(image_path)
            # Try to detect format from extension
            ext = Path(image_path).suffix.lower().lstrip('.')
            format_map = {
                '.vhd': 'vpc',
                '.vhdx': 'vhdx',
                '.raw': 'raw',
                '.qcow2': 'qcow2',
                '.vmdk': 'vmdk',
                '.vdi': 'vdi',
            }
            detected_format = format_map.get(f'.{ext}', 'raw')
            
            return {
                "format": detected_format,
                "virtual-size": file_size,
                "actual-size": file_size,
            }
        
        def convert_image(self, source_path: str, dest_path: str, target_format: str, compress: bool = False):
            """Convert image (fallback: just copy)"""
            if not os.path.exists(source_path):
                raise ImageConversionError(f"Source image not found: {source_path}")
            shutil.copy2(source_path, dest_path)


class ImageImportExportError(Exception):
    """Image import/export error"""
    pass


class ImageImportExportManager:
    """
    Manager for image import and export operations
    Async version
    """
    
    def __init__(self):
        """Initialize image import/export manager"""
        self.settings = get_settings()
        self.image_converter = ImageConverter(
            qemu_img_path=str(self.settings.QEMU_IMG_PATH),
            mock_mode=False
        )
        self.import_dir = Path(self.settings.IMAGE_STORAGE_PATH) / "imports"
        self.export_dir = Path(self.settings.IMAGE_STORAGE_PATH) / "exports"
        self.import_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    async def import_image(
        self,
        db: AsyncSession,
        name: str,
        source_path: str,
        image_type: ImageType = ImageType.SYSTEM,
        description: Optional[str] = None,
        created_by: int = 1,
    ) -> Image:
        """
        Import an image from external source
        
        Args:
            db: Async database session
            name: Image name
            source_path: Source file path
            image_type: Image type
            description: Optional description
            created_by: User ID who created the import
            
        Returns:
            Created Image model
            
        Raises:
            ImageImportExportError: If import fails
        """
        # Verify source path exists
        if not os.path.exists(source_path):
            raise ImageImportExportError(f"Source path not found: {source_path}")
        
        try:
            # Get image info
            image_info = await asyncio.to_thread(self.image_converter.get_image_info, source_path)
            
            # Determine format
            detected_format = image_info.get("format", "raw")
            try:
                image_format = ImageFormat(detected_format)
            except ValueError:
                # Map qemu-img format names to our enum
                format_map = {
                    "vpc": ImageFormat.VHD,
                    "vhdx": ImageFormat.VHDX,
                    "raw": ImageFormat.RAW,
                    "qcow2": ImageFormat.QCOW2,
                    "vmdk": ImageFormat.VMDK,
                    "vdi": ImageFormat.VDI,
                }
                image_format = format_map.get(detected_format, ImageFormat.RAW)
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_ext = Path(source_path).suffix or f".{detected_format}"
            unique_filename = f"{file_id}{file_ext}"
            
            # Destination path in storage
            dest_path = self.settings.IMAGE_STORAGE_PATH / unique_filename
            
            # Copy file to storage (in thread pool for large files)
            await asyncio.to_thread(shutil.copy2, source_path, dest_path)
            
            # Get file size
            file_size = os.path.getsize(dest_path)
            virtual_size = image_info.get("virtual-size", file_size)
            
            # Create image record
            image = Image(
                name=name,
                description=description,
                filename=unique_filename,
                file_path=str(dest_path),
                original_filename=Path(source_path).name,
                format=image_format,
                size_bytes=file_size,
                virtual_size_bytes=virtual_size,
                image_type=image_type,
                status=ImageStatus.READY,
                created_by=created_by,
            )
            
            db.add(image)
            await db.commit()
            await db.refresh(image)
            
            logger.info(
                "Image imported",
                image_id=image.id,
                name=name,
                format=image_format.value,
                size_mb=round(file_size / 1024 / 1024, 2)
            )
            
            return image
            
        except ImageConversionError as e:
            raise ImageImportExportError(f"Failed to get image info: {e}") from e
        except Exception as e:
            await db.rollback()
            raise ImageImportExportError(f"Failed to import image: {e}") from e
    
    async def export_image(
        self,
        db: AsyncSession,
        image_id: int,
        destination_path: Optional[str] = None,
        target_format: Optional[ImageFormat] = None,
        compress: bool = False,
    ) -> Dict[str, Any]:
        """
        Export an image to external destination
        
        Args:
            db: Async database session
            image_id: Image ID
            destination_path: Optional destination path (if None, uses export dir)
            target_format: Optional target format (if None, keeps original format)
            compress: Enable compression
            
        Returns:
            Export result dictionary
            
        Raises:
            ImageImportExportError: If export fails
        """
        # Get image
        stmt = select(Image).where(Image.id == image_id)
        result = await db.execute(stmt)
        image = result.scalar_one_or_none()
        
        if not image:
            raise ImageImportExportError(f"Image {image_id} not found")
        
        if not os.path.exists(image.file_path):
            raise ImageImportExportError(f"Image file not found: {image.file_path}")
        
        try:
            # Determine destination path
            if not destination_path:
                export_filename = f"{image.name}_{image_id}.{image.format.value}"
                destination_path = str(self.export_dir / export_filename)
            else:
                # Ensure destination directory exists
                dest_dir = Path(destination_path).parent
                dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine if conversion is needed
            needs_conversion = target_format and target_format != image.format
            
            if needs_conversion:
                # Convert image format
                target_format_str = target_format.value
                logger.info(
                    "Converting image for export",
                    image_id=image_id,
                    from_format=image.format.value,
                    to_format=target_format_str
                )
                
                await asyncio.to_thread(
                    self.image_converter.convert_image,
                    image.file_path,
                    destination_path,
                    target_format_str,
                    compress
                )
            else:
                # Just copy the file
                await asyncio.to_thread(shutil.copy2, image.file_path, destination_path)
            
            # Get exported file size
            exported_size = os.path.getsize(destination_path)
            
            result = {
                "image_id": image_id,
                "image_name": image.name,
                "destination_path": destination_path,
                "format": target_format.value if target_format else image.format.value,
                "size_bytes": exported_size,
                "size_mb": round(exported_size / 1024 / 1024, 2),
                "compressed": compress,
                "status": "completed",
            }
            
            logger.info(
                "Image exported",
                image_id=image_id,
                destination=destination_path,
                size_mb=result["size_mb"]
            )
            
            return result
            
        except ImageConversionError as e:
            raise ImageImportExportError(f"Failed to convert image: {e}") from e
        except Exception as e:
            raise ImageImportExportError(f"Failed to export image: {e}") from e
    
    async def export_image_for_download(
        self,
        db: AsyncSession,
        image_id: int,
        target_format: Optional[ImageFormat] = None,
        compress: bool = False,
    ) -> Dict[str, Any]:
        """
        Export image to temporary location for download
        
        Args:
            db: Async database session
            image_id: Image ID
            target_format: Optional target format
            compress: Enable compression
            
        Returns:
            Export result with download path
        """
        # Get image
        stmt = select(Image).where(Image.id == image_id)
        result = await db.execute(stmt)
        image = result.scalar_one_or_none()
        
        if not image:
            raise ImageImportExportError(f"Image {image_id} not found")
        
        # Generate export filename
        format_ext = target_format.value if target_format else image.format.value
        export_filename = f"{image.name}_{image_id}.{format_ext}"
        export_path = self.export_dir / export_filename
        
        # Export image
        result = await self.export_image(
            db=db,
            image_id=image_id,
            destination_path=str(export_path),
            target_format=target_format,
            compress=compress,
        )
        
        # Add download URL
        result["download_url"] = f"/api/v1/images/import-export/{image_id}/export/download/{export_filename}"
        result["filename"] = export_filename
        
        return result
    
    async def get_export_status(
        self,
        db: AsyncSession,
        image_id: int,
    ) -> Dict[str, Any]:
        """
        Get export status for an image
        
        Args:
            db: Async database session
            image_id: Image ID
            
        Returns:
            Export status dictionary
        """
        # Get image
        stmt = select(Image).where(Image.id == image_id)
        result = await db.execute(stmt)
        image = result.scalar_one_or_none()
        
        if not image:
            raise ImageImportExportError(f"Image {image_id} not found")
        
        # Check for exported files
        exported_files = []
        for file in self.export_dir.glob(f"{image.name}_{image_id}.*"):
            exported_files.append({
                "filename": file.name,
                "path": str(file),
                "size_bytes": file.stat().st_size,
                "size_mb": round(file.stat().st_size / 1024 / 1024, 2),
                "created_at": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
            })
        
        return {
            "image_id": image_id,
            "image_name": image.name,
            "status": "idle",
            "exported_files": exported_files,
            "export_count": len(exported_files),
        }

