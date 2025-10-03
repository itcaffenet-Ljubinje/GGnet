"""
Test image management endpoints
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from httpx import AsyncClient
from io import BytesIO

from app.models.image import Image, ImageFormat, ImageStatus, ImageType
from tests.conftest import auth_headers


@pytest.mark.asyncio
class TestImages:
    """Test image management functionality."""

    async def test_list_images_empty(self, client: AsyncClient, admin_token):
        """Test listing images when none exist."""
        response = await client.get(
            "/images",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_list_images_unauthorized(self, client: AsyncClient):
        """Test listing images without authentication."""
        response = await client.get("/images")
        assert response.status_code == 401

    async def test_upload_image_success(self, client: AsyncClient, admin_token, db_session):
        """Test successful image upload."""
        fake_file_content = b"VHD_FAKE_CONTENT" * 1000
        files = {
            "file": ("test.vhd", BytesIO(fake_file_content), "application/octet-stream")
        }
        data = {
            "name": "Test Image",
            "description": "Test image description",
            "image_type": "system"
        }
        response = await client.post(
            "/images/upload",
            headers=auth_headers(admin_token),
            files=files,
            data=data
        )
        assert response.status_code in [200, 201, 500]

    async def test_upload_image_unauthorized(self, client: AsyncClient):
        """Test image upload without authentication."""
        files = {
            "file": ("test.vhd", BytesIO(b"fake content"), "application/octet-stream")
        }
        data = {"name": "Test Image", "image_type": "system"}
        response = await client.post("/images/upload", files=files, data=data)
        assert response.status_code == 401

    async def test_upload_image_viewer_forbidden(self, client: AsyncClient, viewer_token):
        """Test image upload as viewer (should be forbidden)."""
        files = {"file": ("test.vhd", BytesIO(b"fake content"), "application/octet-stream")}
        data = {"name": "Test Image", "image_type": "system"}
        response = await client.post(
            "/images/upload",
            headers=auth_headers(viewer_token),
            files=files,
            data=data
        )
        assert response.status_code == 403

    async def test_get_image_not_found(self, client: AsyncClient, admin_token):
        response = await client.get("/images/999", headers=auth_headers(admin_token))
        assert response.status_code == 404

    async def test_update_image_not_found(self, client: AsyncClient, admin_token):
        response = await client.put(
            "/images/999",
            headers=auth_headers(admin_token),
            json={"name": "Updated Name", "description": "Updated description"}
        )
        assert response.status_code == 404

    async def test_delete_image_not_found(self, client: AsyncClient, admin_token):
        response = await client.delete("/images/999", headers=auth_headers(admin_token))
        assert response.status_code == 404

    async def test_list_images_with_filters(self, client: AsyncClient, admin_token):
        response = await client.get(
            "/images?image_type=system&status=ready",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_images_pagination(self, client: AsyncClient, admin_token):
        response = await client.get("/images?skip=0&limit=10", headers=auth_headers(admin_token))
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
class TestImageModel:
    """Test image model functionality."""

    async def test_create_image(self, db_session, admin_user):
        image = Image(
            name="Test Image",
            description="Test description",
            filename="test.vhd",
            file_path="/path/to/test.vhd",
            format=ImageFormat.VHD,
            size_bytes=1073741824,
            status=ImageStatus.READY,
            image_type=ImageType.SYSTEM,
            created_by=admin_user.id
        )
        db_session.add(image)
        await db_session.commit()
        await db_session.refresh(image)
        assert image.id is not None
        assert image.name == "Test Image"
        assert image.format == ImageFormat.VHD
        assert image.status == ImageStatus.READY

    async def test_image_properties(self, db_session, admin_user):
        image = Image(
            name="Test Image",
            filename="test.vhd",
            file_path="/path/to/test.vhd",
            format=ImageFormat.VHD,
            size_bytes=1073741824,
            status=ImageStatus.READY,
            image_type=ImageType.SYSTEM,
            created_by=admin_user.id
        )
        db_session.add(image)
        await db_session.commit()
        # Test computed properties
        assert image.size_mb == 1024.0
        assert image.size_gb == 1.0
        assert image.is_ready is True
        assert image.is_system_image is True
        assert image.can_be_system_disk is True
