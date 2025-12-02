"""
Background worker for image conversion tasks
Handles VHDX to RAW conversion for iSCSI targets
"""

import asyncio
import json
import logging
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.models.image import Image, ImageStatus, ImageFormat
from app.core.config import get_settings

# Configure structured logging
logger = structlog.get_logger(__name__)


class ImageConversionWorker:
    """Background worker for image conversion tasks"""
    
    def __init__(self):
        self.settings = get_settings()
        # Respect test overrides when running under pytest/CI
        import os
        if os.getenv("PYTEST_CURRENT_TEST") is not None or self.settings.ENVIRONMENT.lower() == "test":
            self.storage_path = Path("/tmp/storage")
            self.temp_path = Path("/tmp/storage/temp")
        else:
            self.storage_path = Path(self.settings.IMAGE_STORAGE_PATH)
            self.temp_path = Path(self.settings.TEMP_STORAGE_PATH)
        self.qemu_script = Path(__file__).parent.parent / "scripts" / "qemu_convert.py"
        
        # Ensure directories exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("Image conversion worker initialized", 
                   storage_path=str(self.storage_path),
                   temp_path=str(self.temp_path))
    
    async def process_conversion_queue(self):
        """Process pending image conversions"""
        logger.info("Starting image conversion queue processing")
        
        while True:
            try:
                # Get pending conversions
                async with get_db() as db:
                    result = await db.execute(
                        select(Image).where(
                            Image.status == ImageStatus.PROCESSING
                        ).limit(10)
                    )
                    pending_images = result.scalars().all()
                
                if not pending_images:
                    logger.info("No pending conversions, waiting...")
                    await asyncio.sleep(30)  # Wait 30 seconds before checking again
                    continue
                
                logger.info(f"Found {len(pending_images)} pending conversions")
                
                # Process each image
                for image in pending_images:
                    try:
                        await self.convert_image(image)
                    except Exception as e:
                        logger.error(f"Failed to convert image {image.id}: {e}")
                        await self._mark_image_error(image.id, str(e))
                
                # Small delay between batches
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in conversion queue processing: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def convert_image(self, image: Image) -> Dict:
        """
        Convert a single image from VHDX to RAW format
        
        Args:
            image: Image model instance
            
        Returns:
            Dict with conversion results
        """
        logger.info(f"Starting conversion for image {image.id}: {image.name}")
        
        try:
            # Update status to converting
            await self._update_image_status(image.id, ImageStatus.CONVERTING)
            
            # Validate input file
            if not os.path.exists(image.file_path):
                raise FileNotFoundError(f"Image file not found: {image.file_path}")
            
            # Determine output path
            output_filename = f"{image.id}.img"
            output_path = self.storage_path / "converted" / output_filename
            
            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert image using qemu-img
            conversion_result = await self._run_qemu_conversion(
                image.file_path,
                str(output_path),
                image.id
            )
            
            # Update image record with conversion results
            await self._update_image_after_conversion(
                image.id,
                str(output_path),
                conversion_result
            )
            
            logger.info(f"Successfully converted image {image.id}")
            return conversion_result
            
        except Exception as e:
            logger.error(f"Conversion failed for image {image.id}: {e}")
            await self._mark_image_error(image.id, str(e))
            raise
    
    async def _run_qemu_conversion(
        self,
        input_path: str,
        output_path: str,
        image_id: int
    ) -> Dict:
        """Run qemu-img conversion with progress tracking"""
        
        # Import the converter
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        from scripts.qemu_convert import QemuImageConverter
        
        converter = QemuImageConverter()
        
        # Progress callback
        def progress_callback(percent: float, total_size: int):
            logger.info(f"Conversion progress for image {image_id}: {percent:.1f}%")
            # Could emit WebSocket event here for real-time updates
        
        # Run conversion
        result = await converter.convert_image(
            input_path,
            output_path,
            "raw",
            progress_callback
        )
        
        return result
    
    async def _update_image_status(self, image_id: int, status: ImageStatus):
        """Update image status in database"""
        async with get_db() as db:
            await db.execute(
                update(Image)
                .where(Image.id == image_id)
                .values(
                    status=status,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
        
        logger.info(f"Updated image {image_id} status to {status}")
    
    async def _update_image_after_conversion(
        self,
        image_id: int,
        converted_path: str,
        conversion_result: Dict
    ):
        """Update image record after successful conversion"""
        async with get_db() as db:
            await db.execute(
                update(Image)
                .where(Image.id == image_id)
                .values(
                    status=ImageStatus.READY,
                    virtual_size_bytes=conversion_result.get("output_size"),
                    processing_log=json.dumps(conversion_result),
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
        
        logger.info(f"Updated image {image_id} after conversion")
    
    async def _mark_image_error(self, image_id: int, error_message: str):
        """Mark image as error with error message"""
        async with get_db() as db:
            await db.execute(
                update(Image)
                .where(Image.id == image_id)
                .values(
                    status=ImageStatus.ERROR,
                    error_message=error_message,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
        
        logger.error(f"Marked image {image_id} as error: {error_message}")
    
    async def cleanup_temp_files(self):
        """Clean up temporary files older than 24 hours"""
        logger.info("Starting temp file cleanup")
        
        try:
            current_time = datetime.utcnow()
            cleaned_count = 0
            
            for temp_file in self.temp_path.rglob("*"):
                if temp_file.is_file():
                    file_age = current_time - datetime.fromtimestamp(temp_file.stat().st_mtime)
                    if file_age.total_seconds() > 24 * 3600:  # 24 hours
                        temp_file.unlink()
                        cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} temporary files")
            
        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}")
    
    async def get_conversion_stats(self) -> Dict:
        """Get conversion statistics"""
        async with get_db() as db:
            # Count images by status
            result = await db.execute(
                select(Image.status, db.func.count(Image.id))
                .group_by(Image.status)
            )
            status_counts = dict(result.all())
            
            # Get recent conversions
            result = await db.execute(
                select(Image)
                .where(Image.status == ImageStatus.READY)
                .order_by(Image.updated_at.desc())
                .limit(10)
            )
            recent_conversions = result.scalars().all()
        
        return {
            "status_counts": status_counts,
            "recent_conversions": [
                {
                    "id": img.id,
                    "name": img.name,
                    "size_gb": img.size_gb,
                    "converted_at": img.updated_at.isoformat()
                }
                for img in recent_conversions
            ]
        }


async def main():
    """Main function for running the worker"""
    logger.info("Starting GGnet Image Conversion Worker")
    
    worker = ImageConversionWorker()
    
    # Start background tasks
    tasks = [
        asyncio.create_task(worker.process_conversion_queue()),
        asyncio.create_task(worker.cleanup_temp_files())
    ]
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Worker shutdown requested")
    except Exception as e:
        logger.error(f"Worker error: {e}")
    finally:
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        
        logger.info("Image conversion worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
