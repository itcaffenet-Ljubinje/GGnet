"""
Tests for image conversion functionality
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image import Image, ImageStatus, ImageFormat, ImageType
from app.core.exceptions import ValidationError, NotFoundError


class TestImageConversion:
    """Test image conversion functionality"""
    
    @pytest.mark.asyncio
    async def test_trigger_conversion_success(self, client: AsyncClient, admin_token, auth_headers, db_session):
        """Test successful conversion trigger"""
        # Create a test image
        image = Image(
            name="Test Image",
            filename="test.vhdx",
            file_path="/tmp/test.vhdx",
            format=ImageFormat.VHDX,
            size_bytes=1024*1024*100,  # 100MB
            status=ImageStatus.READY,
            image_type=ImageType.SYSTEM,
            created_by=1
        )
        db_session.add(image)
        await db_session.commit()
        await db_session.refresh(image)
        
        # Trigger conversion
        response = await client.post(
            f"/images/{image.id}/convert",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Conversion triggered successfully"
        assert data["image_id"] == image.id
        
        # Verify status changed to PROCESSING
        await db_session.refresh(image)
        assert image.status == ImageStatus.PROCESSING
    
    @pytest.mark.asyncio
    async def test_trigger_conversion_invalid_status(self, client: AsyncClient, admin_token, auth_headers, db_session):
        """Test conversion trigger with invalid status"""
        # Create a test image with PROCESSING status
        image = Image(
            name="Test Image",
            filename="test.vhdx",
            file_path="/tmp/test.vhdx",
            format=ImageFormat.VHDX,
            size_bytes=1024*1024*100,
            status=ImageStatus.PROCESSING,
            image_type=ImageType.SYSTEM,
            created_by=1
        )
        db_session.add(image)
        await db_session.commit()
        await db_session.refresh(image)
        
        # Try to trigger conversion
        response = await client.post(
            f"/images/{image.id}/convert",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "must be in READY or ERROR status" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_trigger_conversion_nonexistent_image(self, client: AsyncClient, admin_token, auth_headers):
        """Test conversion trigger for nonexistent image"""
        response = await client.post(
            "/images/99999/convert",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_get_conversion_status(self, client: AsyncClient, admin_token, auth_headers, db_session):
        """Test getting conversion status"""
        # Create a test image
        image = Image(
            name="Test Image",
            filename="test.vhdx",
            file_path="/tmp/test.vhdx",
            format=ImageFormat.VHDX,
            size_bytes=1024*1024*100,
            status=ImageStatus.PROCESSING,
            image_type=ImageType.SYSTEM,
            processing_log='{"progress": 50, "duration": 120}',
            created_by=1
        )
        db_session.add(image)
        await db_session.commit()
        await db_session.refresh(image)
        
        # Get conversion status
        response = await client.get(
            f"/images/{image.id}/conversion-status",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["image_id"] == image.id
        assert data["name"] == "Test Image"
        assert data["status"] == "processing"
        assert data["format"] == "vhdx"
        assert data["processing_info"]["progress"] == 50
    
    @pytest.mark.asyncio
    async def test_get_conversion_status_nonexistent(self, client: AsyncClient, admin_token, auth_headers):
        """Test getting conversion status for nonexistent image"""
        response = await client.get(
            "/images/99999/conversion-status",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


class TestQemuImageConverter:
    """Test qemu-img wrapper functionality"""
    
    @pytest.mark.asyncio
    async def test_qemu_img_check_available(self):
        """Test qemu-img availability check"""
        from scripts.qemu_convert import QemuImageConverter
        
        # Mock subprocess to simulate qemu-img being available
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "qemu-img version 6.2.0"
            
            converter = QemuImageConverter()
            assert converter._check_qemu_img() is True
    
    @pytest.mark.asyncio
    async def test_qemu_img_check_unavailable(self):
        """Test qemu-img availability check when not available"""
        from scripts.qemu_convert import QemuImageConverter
        
        # Mock subprocess to simulate qemu-img not being available
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("qemu-img not found")
            
            converter = QemuImageConverter()
            assert converter._check_qemu_img() is False
    
    @pytest.mark.asyncio
    async def test_get_image_info_success(self):
        """Test successful image info retrieval"""
        from scripts.qemu_convert import QemuImageConverter
        
        mock_info = {
            "virtual-size": 1073741824,
            "format": "vhdx",
            "actual-size": 536870912
        }
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock successful subprocess
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (
                str(mock_info).replace("'", '"').encode(),
                b""
            )
            mock_subprocess.return_value = mock_process
            
            converter = QemuImageConverter()
            info = await converter.get_image_info("/tmp/test.vhdx")
            
            assert info["virtual-size"] == 1073741824
            assert info["format"] == "vhdx"
    
    @pytest.mark.asyncio
    async def test_convert_image_success(self):
        """Test successful image conversion"""
        from scripts.qemu_convert import QemuImageConverter
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock successful conversion
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"", b"")
            mock_subprocess.return_value = mock_process
            
            # Mock file operations
            with patch('os.path.exists', return_value=True), \
                 patch('os.makedirs'), \
                 patch('os.path.getsize', return_value=1024*1024*50), \
                 patch('asyncio.get_event_loop') as mock_loop:
                
                mock_loop.return_value.time.side_effect = [0, 10]  # 10 second conversion
                
                converter = QemuImageConverter()
                result = await converter.convert_image(
                    "/tmp/input.vhdx",
                    "/tmp/output.img",
                    "raw"
                )
                
                assert result["success"] is True
                assert result["input_path"] == "/tmp/input.vhdx"
                assert result["output_path"] == "/tmp/output.img"
                assert result["output_format"] == "raw"
                assert result["duration_seconds"] == 10
    
    @pytest.mark.asyncio
    async def test_convert_image_failure(self):
        """Test image conversion failure"""
        from scripts.qemu_convert import QemuImageConverter
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock failed conversion
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (
                b"",
                b"qemu-img: error: cannot open input file"
            )
            mock_subprocess.return_value = mock_process
            
            # Mock file operations
            with patch('os.path.exists', return_value=True), \
                 patch('os.makedirs'), \
                 patch('os.path.exists', side_effect=lambda x: x == "/tmp/input.vhdx"):
                
                converter = QemuImageConverter()
                
                with pytest.raises(RuntimeError, match="qemu-img convert failed"):
                    await converter.convert_image(
                        "/tmp/input.vhdx",
                        "/tmp/output.img",
                        "raw"
                    )


class TestImageConversionWorker:
    """Test background worker functionality"""
    
    @pytest.mark.asyncio
    async def test_worker_initialization(self):
        """Test worker initialization"""
        from worker.convert import ImageConversionWorker
        
        with patch('app.core.config.get_settings') as mock_settings:
            mock_settings.return_value.IMAGE_STORAGE_PATH = Path("/tmp/storage")
            mock_settings.return_value.TEMP_STORAGE_PATH = Path("/tmp/storage/temp")
            
            with patch('pathlib.Path.mkdir'):
                worker = ImageConversionWorker()
                assert str(worker.storage_path) == str(Path("/tmp/storage"))
                assert str(worker.temp_path) == str(Path("/tmp/storage/temp"))
    
    @pytest.mark.asyncio
    async def test_convert_image_success(self, db_session, admin_user):
        """Test successful image conversion by worker"""
        from worker.convert import ImageConversionWorker
        
        # Create test image
        image = Image(
            name="Test Image",
            filename="test.vhdx",
            file_path="/tmp/test.vhdx",
            format=ImageFormat.VHDX,
            size_bytes=1024*1024*100,
            status=ImageStatus.PROCESSING,
            image_type=ImageType.SYSTEM,
            created_by=admin_user.id
        )
        db_session.add(image)
        await db_session.commit()
        await db_session.refresh(image)
        
        # Mock worker dependencies
        with patch('worker.convert.get_db') as mock_get_db, \
             patch('scripts.qemu_convert.QemuImageConverter') as mock_converter_class, \
             patch('os.path.exists', return_value=True):
            
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            mock_converter = AsyncMock()
            mock_converter.convert_image.return_value = {
                "success": True,
                "output_size": 1024*1024*50,
                "duration_seconds": 30
            }
            mock_converter_class.return_value = mock_converter
            
            worker = ImageConversionWorker()
            result = await worker.convert_image(image)
            
            assert result["success"] is True
            assert result["output_size"] == 1024*1024*50
    
    @pytest.mark.asyncio
    async def test_convert_image_file_not_found(self, db_session, admin_user):
        """Test image conversion when file not found"""
        from worker.convert import ImageConversionWorker
        
        # Create test image
        image = Image(
            name="Test Image",
            filename="test.vhdx",
            file_path="/tmp/nonexistent.vhdx",
            format=ImageFormat.VHDX,
            size_bytes=1024*1024*100,
            status=ImageStatus.PROCESSING,
            image_type=ImageType.SYSTEM,
            created_by=admin_user.id
        )
        db_session.add(image)
        await db_session.commit()
        await db_session.refresh(image)
        
        # Mock worker dependencies
        with patch('worker.convert.get_db') as mock_get_db, \
             patch('os.path.exists', return_value=False):
            
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            worker = ImageConversionWorker()
            
            with pytest.raises(FileNotFoundError):
                await worker.convert_image(image)


class TestImageUploadWithConversion:
    """Test image upload with automatic conversion"""
    
    @pytest.mark.asyncio
    async def test_upload_vhdx_triggers_conversion(self, client: AsyncClient, admin_token, auth_headers):
        """Test that uploading VHDX file triggers conversion"""
        # Create a test VHDX file
        test_content = b"fake vhdx content" * 1000  # 17KB
        
        with patch('aiofiles.open') as mock_open, \
             patch('pathlib.Path.mkdir'), \
             patch('app.routes.images.validate_image_file') as mock_validate:
            
            mock_validate.return_value = ImageFormat.VHDX
            
            # Mock file operations
            mock_file = AsyncMock()
            mock_file.read.side_effect = [test_content, b""]  # Read content then EOF
            mock_open.return_value.__aenter__.return_value = mock_file
            
            # Mock database operations
            with patch('app.routes.images.get_db') as mock_get_db, \
                 patch('app.routes.images.log_user_activity') as mock_log, \
                 patch('app.routes.images.process_image_background') as mock_process:
                mock_db = AsyncMock()
                mock_get_db.return_value.__aenter__.return_value = mock_db
                mock_log.return_value = None
                mock_process.return_value = None
                
                # Mock image creation
                mock_image = Image(
                    id=1,
                    name="Test VHDX",
                    filename="test.vhdx",
                    file_path="/tmp/test.vhdx",
                    format=ImageFormat.VHDX,
                    size_bytes=len(test_content),
                    status=ImageStatus.PROCESSING,
                    image_type=ImageType.SYSTEM,
                    created_by=1
                )
                mock_db.execute.return_value.scalar_one_or_none.return_value = None  # No existing image
                mock_db.add.return_value = None
                mock_db.commit.return_value = None
                mock_db.refresh.return_value = None
                
                # Upload file
                response = await client.post(
                    "/images/upload",
                    files={"file": ("test.vhdx", test_content, "application/octet-stream")},
                    data={
                        "name": "Test VHDX",
                        "description": "Test VHDX file",
                        "image_type": "system"
                    },
                    headers=auth_headers(admin_token)
                )
                
                # Should succeed and trigger conversion
                assert response.status_code == 201
                data = response.json()
                assert data["name"] == "Test VHDX"
                assert data["format"] == "vhdx"
                # Status should be UPLOADING initially, then PROCESSING in background
                assert data["status"] == "uploading"
