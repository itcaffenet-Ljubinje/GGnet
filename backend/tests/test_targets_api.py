"""
Tests for iSCSI targets API endpoints
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.models.target import Target, TargetStatus
from app.models.machine import Machine, MachineStatus, BootMode
from app.models.image import Image, ImageFormat, ImageStatus, ImageType
from app.models.user import User, UserRole, UserStatus
from app.core.exceptions import NotFoundError, ValidationError


class TestTargetsAPI:
    """Tests for iSCSI targets API endpoints"""

    @pytest_asyncio.fixture
    async def test_machine(self, db_session: AsyncSession):
        """Create test machine"""
        machine = Machine(
            name="Test Machine",
            description="Test machine for targets",
            mac_address="aa:bb:cc:dd:ee:ff",
            ip_address="192.168.1.100",
            boot_mode=BootMode.UEFI,
            status=MachineStatus.ACTIVE,
            created_by=1
        )
        db_session.add(machine)
        await db_session.commit()
        await db_session.refresh(machine)
        return machine

    @pytest_asyncio.fixture
    async def test_image(self, db_session: AsyncSession):
        """Create test image"""
        image = Image(
            name="Test Image",
            description="Test image for targets",
            filename="test.img",
            file_path="/tmp/test.img",
            format=ImageFormat.RAW,
            size_bytes=1024*1024*100,
            status=ImageStatus.READY,
            image_type=ImageType.SYSTEM,
            created_by=1
        )
        db_session.add(image)
        await db_session.commit()
        await db_session.refresh(image)
        return image

    @pytest_asyncio.fixture
    async def test_target(self, db_session: AsyncSession, test_machine: Machine, test_image: Image):
        """Create test target"""
        target = Target(
            target_id="machine_1",
            iqn="iqn.2025.ggnet:target-machine_1",
            machine_id=test_machine.id,
            image_id=test_image.id,
            image_path=test_image.file_path,
            initiator_iqn="iqn.2025.ggnet:initiator-aabbccddeeff",
            lun_id=0,
            status=TargetStatus.ACTIVE,
            description="Test target",
            created_by=1
        )
        db_session.add(target)
        await db_session.commit()
        await db_session.refresh(target)
        return target

    @pytest.mark.asyncio
    async def test_create_target_success(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        db_session: AsyncSession,
        test_machine: Machine,
        test_image: Image
    ):
        """Test successful target creation"""
        with patch('app.api.targets.create_target_for_machine') as mock_create_target:
            mock_create_target.return_value = {
                "target_id": "machine_1",
                "iqn": "iqn.2025.ggnet:target-machine_1",
                "initiator_iqn": "iqn.2025.ggnet:initiator-aabbccddeeff",
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = await client.post(
                "/api/v1/targets/",
                json={
                    "machine_id": test_machine.id,
                    "image_id": test_image.id,
                    "description": "Test target",
                    "lun_id": 0
                },
                headers=auth_headers(admin_token)
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["machine_id"] == test_machine.id
            assert data["image_id"] == test_image.id
            assert data["target_id"] == "machine_1"
            assert data["iqn"] == "iqn.2025.ggnet:target-machine_1"
            assert data["status"] == TargetStatus.ACTIVE.value

    @pytest.mark.asyncio
    async def test_create_target_machine_not_found(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        test_image: Image
    ):
        """Test target creation with non-existent machine"""
        response = await client.post(
            "/api/v1/targets/",
            json={
                "machine_id": 999,
                "image_id": test_image.id,
                "description": "Test target"
            },
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 400
        assert "Machine with ID 999 not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_target_image_not_found(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        test_machine: Machine
    ):
        """Test target creation with non-existent image"""
        response = await client.post(
            "/api/v1/targets/",
            json={
                "machine_id": test_machine.id,
                "image_id": 999,
                "description": "Test target"
            },
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 400
        assert "Image with ID 999 not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_target_image_not_ready(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        db_session: AsyncSession,
        test_machine: Machine
    ):
        """Test target creation with image not in READY status"""
        # Create image with PROCESSING status
        image = Image(
            name="Processing Image",
            filename="processing.img",
            file_path="/tmp/processing.img",
            format=ImageFormat.VHDX,
            size_bytes=1024*1024*100,
            status=ImageStatus.PROCESSING,  # Not ready
            image_type=ImageType.SYSTEM,
            created_by=1
        )
        db_session.add(image)
        await db_session.commit()
        await db_session.refresh(image)
        
        response = await client.post(
            "/api/v1/targets/",
            json={
                "machine_id": test_machine.id,
                "image_id": image.id,
                "description": "Test target"
            },
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 400
        assert "Image must be in READY status" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_target_already_exists(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        test_machine: Machine,
        test_image: Image,
        test_target: Target
    ):
        """Test target creation when target already exists for machine"""
        response = await client.post(
            "/api/v1/targets/",
            json={
                "machine_id": test_machine.id,
                "image_id": test_image.id,
                "description": "Test target"
            },
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 400
        assert f"Target already exists for machine {test_machine.id}" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_target_targetcli_error(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        test_machine: Machine,
        test_image: Image
    ):
        """Test target creation with targetcli error"""
        with patch('app.api.targets.create_target_for_machine') as mock_create_target:
            from app.core.exceptions import TargetCLIError
            mock_create_target.side_effect = TargetCLIError("targetcli command failed")
            
            response = await client.post(
                "/api/v1/targets/",
                json={
                    "machine_id": test_machine.id,
                    "image_id": test_image.id,
                    "description": "Test target"
                },
                headers=auth_headers(admin_token)
            )
            
            assert response.status_code == 500
            assert "Target creation failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_targets_success(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        test_target: Target
    ):
        """Test successful target listing"""
        response = await client.get(
            "/api/v1/targets/",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["targets"]) == 1
        assert data["targets"][0]["id"] == test_target.id
        assert data["targets"][0]["target_id"] == test_target.target_id

    @pytest.mark.asyncio
    async def test_list_targets_pagination(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        db_session: AsyncSession,
        test_machine: Machine,
        test_image: Image
    ):
        """Test target listing with pagination"""
        # Create multiple targets
        for i in range(5):
            target = Target(
                target_id=f"machine_{i}",
                iqn=f"iqn.2025.ggnet:target-machine_{i}",
                machine_id=test_machine.id,
                image_id=test_image.id,
                image_path=test_image.file_path,
                initiator_iqn=f"iqn.2025.ggnet:initiator-{i:012x}",
                lun_id=0,
                status=TargetStatus.ACTIVE,
                created_by=1
            )
            db_session.add(target)
        await db_session.commit()
        
        # Test first page
        response = await client.get(
            "/api/v1/targets/?skip=0&limit=2",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["targets"]) == 2
        assert data["page"] == 1
        assert data["per_page"] == 2

    @pytest.mark.asyncio
    async def test_get_target_success(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        test_target: Target
    ):
        """Test successful target retrieval"""
        response = await client.get(
            f"/api/v1/targets/{test_target.id}",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_target.id
        assert data["target_id"] == test_target.target_id
        assert data["iqn"] == test_target.iqn

    @pytest.mark.asyncio
    async def test_get_target_not_found(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict
    ):
        """Test target retrieval for non-existent target"""
        response = await client.get(
            "/api/v1/targets/999",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 404
        assert "Target with ID 999 not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_target_status_success(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        test_target: Target
    ):
        """Test successful target status retrieval"""
        with patch('app.api.targets.TargetCLIAdapter') as mock_adapter_class:
            mock_adapter = AsyncMock()
            mock_adapter_class.return_value = mock_adapter
            
            mock_adapter.get_target_status.return_value = {
                "target_id": test_target.target_id,
                "iqn": test_target.iqn,
                "status": "active",
                "luns": ["lun0 [fileio/img_test]"],
                "acls": ["iqn.2025.ggnet:initiator-abc123"],
                "portals": ["0.0.0.0:3260"]
            }
            
            response = await client.get(
                f"/api/v1/targets/{test_target.id}/status",
                headers=auth_headers(admin_token)
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["target_id"] == test_target.target_id
            assert data["iqn"] == test_target.iqn
            assert data["status"] == "active"
            assert len(data["luns"]) == 1
            assert len(data["acls"]) == 1
            assert len(data["portals"]) == 1

    @pytest.mark.asyncio
    async def test_get_target_status_error(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        test_target: Target
    ):
        """Test target status retrieval with error"""
        with patch('app.api.targets.TargetCLIAdapter') as mock_adapter_class:
            mock_adapter = AsyncMock()
            mock_adapter_class.return_value = mock_adapter
            
            mock_adapter.get_target_status.side_effect = Exception("targetcli error")
            
            response = await client.get(
                f"/api/v1/targets/{test_target.id}/status",
                headers=auth_headers(admin_token)
            )
            
            assert response.status_code == 500
            assert "Failed to get target status" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_target_success(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        test_target: Target
    ):
        """Test successful target deletion"""
        with patch('app.api.targets.TargetCLIAdapter') as mock_adapter_class:
            mock_adapter = AsyncMock()
            mock_adapter_class.return_value = mock_adapter
            
            mock_adapter.delete_target.return_value = True
            
            response = await client.delete(
                f"/api/v1/targets/{test_target.id}",
                headers=auth_headers(admin_token)
            )
            
            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_target_not_found(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict
    ):
        """Test target deletion for non-existent target"""
        response = await client.delete(
            "/api/v1/targets/999",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 404
        assert "Target with ID 999 not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_target_targetcli_error(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        test_target: Target
    ):
        """Test target deletion with targetcli error"""
        with patch('app.api.targets.TargetCLIAdapter') as mock_adapter_class:
            mock_adapter = AsyncMock()
            mock_adapter_class.return_value = mock_adapter
            
            from app.core.exceptions import TargetCLIError
            mock_adapter.delete_target.side_effect = TargetCLIError("targetcli error")
            
            response = await client.delete(
                f"/api/v1/targets/{test_target.id}",
                headers=auth_headers(admin_token)
            )
            
            assert response.status_code == 500
            assert "Target deletion failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_target_by_machine_success(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        test_target: Target,
        test_machine: Machine
    ):
        """Test successful target retrieval by machine"""
        response = await client.get(
            f"/api/v1/targets/machine/{test_machine.id}",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_target.id
        assert data["machine_id"] == test_machine.id

    @pytest.mark.asyncio
    async def test_get_target_by_machine_not_found(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict
    ):
        """Test target retrieval by machine when no target exists"""
        response = await client.get(
            "/api/v1/targets/machine/999",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 404
        assert "No target found for machine 999" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_restart_target_success(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        test_target: Target
    ):
        """Test successful target restart"""
        with patch('app.api.targets.TargetCLIAdapter') as mock_adapter_class, \
             patch('app.api.targets.create_target_for_machine') as mock_create_target:
            
            mock_adapter = AsyncMock()
            mock_adapter_class.return_value = mock_adapter
            
            mock_adapter.delete_target.return_value = True
            mock_create_target.return_value = {
                "target_id": test_target.target_id,
                "iqn": "iqn.2025.ggnet:target-machine_1",
                "initiator_iqn": "iqn.2025.ggnet:initiator-aabbccddeeff",
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = await client.post(
                f"/api/v1/targets/{test_target.id}/restart",
                headers=auth_headers(admin_token)
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Target restarted successfully"
            assert data["target_id"] == test_target.target_id

    @pytest.mark.asyncio
    async def test_restart_target_not_found(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict
    ):
        """Test target restart for non-existent target"""
        response = await client.post(
            "/api/v1/targets/999/restart",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 404
        assert "Target with ID 999 not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_restart_target_error(
        self, 
        client: AsyncClient, 
        admin_token: str, 
        auth_headers: dict,
        test_target: Target
    ):
        """Test target restart with error"""
        with patch('app.api.targets.TargetCLIAdapter') as mock_adapter_class:
            mock_adapter = AsyncMock()
            mock_adapter_class.return_value = mock_adapter
            
            mock_adapter.delete_target.side_effect = Exception("Restart failed")
            
            response = await client.post(
                f"/api/v1/targets/{test_target.id}/restart",
                headers=auth_headers(admin_token)
            )
            
            assert response.status_code == 500
            assert "Failed to restart target" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_target_unauthorized(
        self, 
        client: AsyncClient, 
        viewer_token: str, 
        auth_headers: dict,
        test_machine: Machine,
        test_image: Image
    ):
        """Test target creation with insufficient permissions"""
        response = await client.post(
            "/api/v1/targets/",
            json={
                "machine_id": test_machine.id,
                "image_id": test_image.id,
                "description": "Test target"
            },
            headers=auth_headers(viewer_token)
        )
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_target_unauthorized(
        self, 
        client: AsyncClient, 
        viewer_token: str, 
        auth_headers: dict,
        test_target: Target
    ):
        """Test target deletion with insufficient permissions"""
        response = await client.delete(
            f"/api/v1/targets/{test_target.id}",
            headers=auth_headers(viewer_token)
        )
        
        assert response.status_code == 403
