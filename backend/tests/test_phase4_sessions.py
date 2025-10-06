"""
Tests for Phase 4: Session Orchestration and PXE/iPXE
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.main import app
from app.models.machine import Machine, MachineStatus
from app.models.image import Image, ImageStatus, ImageFormat
from app.models.target import Target, TargetStatus
from app.models.session import Session, SessionStatus, SessionType
from app.models.user import User, UserRole


class TestSessionOrchestration:
    """Test session orchestration functionality"""
    
    
    @pytest_asyncio.fixture
    async def test_machine(self, db_session):
        machine = Machine(
            id=1,
            name="test-workstation",
            mac_address="00:11:22:33:44:55",
            ip_address="192.168.1.101",
            status=MachineStatus.ACTIVE,
            boot_mode="LEGACY",
            created_by=1
        )
        db_session.add(machine)
        await db_session.commit()
        return machine
    
    @pytest_asyncio.fixture
    async def test_image(self, db_session):
        image = Image(
            id=1,
            name="test-image",
            filename="test.vhdx",
            file_path="/storage/images/test.vhdx",
            format=ImageFormat.VHDX,
            status=ImageStatus.READY,
            size_bytes=1024*1024*1024,  # 1GB
            created_by=1
        )
        db_session.add(image)
        await db_session.commit()
        return image
    
    @pytest_asyncio.fixture
    async def test_target(self, db_session, test_machine, test_image):
        target = Target(
            id=1,
            target_id="target-001",
            machine_id=test_machine.id,
            image_id=test_image.id,
            iqn="iqn.2025.ggnet:target-001",
            image_path="/storage/images/test.vhdx",
            initiator_iqn="iqn.2025.ggnet:initiator-001122334455",
            lun_id=0,
            status=TargetStatus.ACTIVE,
            created_by=1
        )
        db_session.add(target)
        await db_session.commit()
        return target
    
    @pytest.mark.asyncio
    async def test_start_session_success(self, client: AsyncClient, admin_user, admin_token, test_machine, test_image):
        """Test successful session start"""
        
        # Use proper authentication headers
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Mock targetcli operations
        with patch("app.api.sessions.create_target_for_machine") as mock_create_target:
            mock_create_target.return_value = {
                "target_id": "target-001",
                "iqn": "iqn.2025.ggnet:target-001",
                "initiator_iqn": "iqn.2025.ggnet:initiator-001122334455",
                "portal_ip": "192.168.1.10",
                "portal_port": 3260,
                "lun_id": 0
            }
            
            # Mock iPXE script generation
            with patch("app.api.sessions.iPXEScriptGenerator") as mock_ipxe:
                mock_generator = MagicMock()
                mock_generator.generate_machine_boot_script.return_value = "#!ipxe\necho Booting...\nsanboot iscsi:192.168.1.10::0:iqn.2025.ggnet:target-001"
                mock_generator.get_machine_script_filename.return_value = "machines/00-11-22-33-44-55.ipxe"
                mock_ipxe.return_value = mock_generator
                
                # Mock TFTP operations
                with patch("app.api.sessions.save_boot_script_to_tftp") as mock_tftp:
                    mock_tftp.return_value = "/var/lib/tftpboot/machines/00-11-22-33-44-55.ipxe"
                    
                    # Mock DHCP operations
                    with patch("app.api.sessions.add_machine_to_dhcp") as mock_dhcp:
                        mock_dhcp.return_value = True
                        
                        # Make request
                        response = await client.post(
                            "/api/v1/sessions/start",
                            json={
                                "machine_id": test_machine.id,
                                "image_id": test_image.id,
                                "session_type": "diskless_boot",
                                "description": "Test session"
                            },
                            headers=headers
                        )
                        
                        # Verify response
                        print(f"Response status: {response.status_code}")
                        print(f"Response body: {response.text}")
                        assert response.status_code == 201
                        data = response.json()
                        
                        assert "session" in data
                        assert "target_info" in data
                        assert "boot_script" in data
                        assert "ipxe_script_url" in data
                        assert "iscsi_details" in data
                        
                        # Verify session was created
                        assert data["session"]["machine_id"] == test_machine.id
                        assert data["session"]["target_id"] == 1
                        assert data["session"]["status"] == "active"
                        assert data["session"]["session_type"] == "diskless_boot"
                        
                        # Verify target info
                        assert data["target_info"]["iqn"] == "iqn.2025.ggnet:target-001"
                        
                        # Verify boot script
                        assert "#!ipxe" in data["boot_script"]
                        assert "sanboot iscsi:" in data["boot_script"]
    
    @pytest.mark.asyncio
    async def test_start_session_machine_not_found(self, client: AsyncClient, admin_user, admin_token):
        """Test session start with non-existent machine"""
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.post(
            "/api/v1/sessions/start",
            json={
                "machine_id": 999,
                "image_id": 1,
                "session_type": "diskless_boot"
            },
            headers=headers
        )
        
        assert response.status_code == 404
        assert "Machine with ID 999 not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_start_session_image_not_ready(self, client: AsyncClient, admin_user, admin_token, test_machine, db_session):
        """Test session start with image not in READY status"""
        
        # Create image with PROCESSING status
        image = Image(
            id=1,
            name="test-image",
            filename="test.vhdx",
            file_path="/storage/images/test.vhdx",
            format=ImageFormat.VHDX,
            status=ImageStatus.PROCESSING,  # Not ready
            size_bytes=1024*1024*1024,
            created_by=1
        )
        db_session.add(image)
        await db_session.commit()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.post(
            "/api/v1/sessions/start",
            json={
                "machine_id": 1,
                "image_id": 1,
                "session_type": "diskless_boot"
            },
            headers=headers
        )
        
        assert response.status_code == 400
        assert "Image must be in READY status" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_stop_session_success(self, client: AsyncClient, admin_user, admin_token, test_machine, test_image, db_session):
        """Test successful session stop"""
        
        # Create target first (let database assign ID)
        target = Target(
            target_id="target-stop-001",
            iqn="iqn.2025.ggnet:target-stop-001",
            machine_id=test_machine.id,
            image_id=test_image.id,
            image_path="/storage/images/test-stop.vhdx",
            initiator_iqn="iqn.2025.ggnet:initiator-stop-001",
            lun_id=0,
            status=TargetStatus.ACTIVE,
            created_by=1
        )
        db_session.add(target)
        await db_session.flush()  # Get the ID without committing
        
        # Create active session (let database assign ID)
        session = Session(
            session_id="test-session-stop-1",
            machine_id=test_machine.id,
            target_id=target.id,
            session_type=SessionType.DISKLESS_BOOT,
            status=SessionStatus.ACTIVE,
            started_at=datetime.utcnow(),
            server_ip="192.168.1.10"
        )
        db_session.add(session)
        await db_session.commit()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Mock cleanup operations
        with patch("app.api.sessions.delete_target_for_machine") as mock_delete_target:
            mock_delete_target.return_value = True
            
            with patch("app.api.sessions.remove_machine_from_dhcp") as mock_remove_dhcp:
                mock_remove_dhcp.return_value = True
                
                with patch("app.adapters.tftp.TFTPAdapter.remove_boot_script") as mock_remove_script:
                    mock_remove_script.return_value = True
                    
                    response = await client.post(f"/api/v1/sessions/{session.id}/stop", headers=headers)
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    assert data["message"] == "Session stopped successfully"
                    assert data["session_id"] == 1
                    assert data["machine_id"] == 1
    
    @pytest.mark.asyncio
    async def test_list_sessions(self, client: AsyncClient, admin_user, admin_token, db_session):
        """Test listing sessions"""
        
        # Create test sessions
        session1 = Session(
            id=1,
            session_id="test-session-1",
            machine_id=1,
            target_id=1,
            session_type=SessionType.DISKLESS_BOOT,
            status=SessionStatus.ACTIVE,
            started_at=datetime.utcnow(),
            server_ip="192.168.1.10"
        )
        session2 = Session(
            id=2,
            session_id="test-session-2",
            machine_id=2,
            target_id=2,
            session_type=SessionType.DISKLESS_BOOT,
            status=SessionStatus.STOPPED,
            started_at=datetime.utcnow(),
            ended_at=datetime.utcnow(),
            server_ip="192.168.1.10"
        )
        db_session.add_all([session1, session2])
        await db_session.commit()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.get("/api/v1/sessions/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sessions" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        
        assert len(data["sessions"]) == 2
        assert data["total"] == 2
    
    @pytest.mark.asyncio
    async def test_get_machine_boot_script(self, client: AsyncClient, admin_user, admin_token, test_machine, test_image, db_session):
        """Test getting boot script for a machine"""
        
        # Create active session
        session = Session(
            id=1,
            session_id="test-session-1",
            machine_id=1,
            target_id=1,
            session_type=SessionType.DISKLESS_BOOT,
            status=SessionStatus.ACTIVE,
            started_at=datetime.utcnow(),
            server_ip="192.168.1.10"
        )
        db_session.add(session)
        
        # Create target
        target = Target(
            id=1,
            target_id="target-001",
            iqn="iqn.2025.ggnet:target-001",
            machine_id=1,
            image_id=1,
            image_path="/storage/images/test.vhdx",
            initiator_iqn="iqn.2025.ggnet:initiator-001122334455",
            lun_id=0,
            status=TargetStatus.ACTIVE,
            created_by=1
        )
        db_session.add(target)
        await db_session.commit()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Mock iPXE script generation
        with patch("app.adapters.ipxe.iPXEScriptGenerator") as mock_ipxe:
            mock_generator = MagicMock()
            mock_generator.generate_machine_boot_script.return_value = "#!ipxe\necho Booting...\nsanboot iscsi:192.168.1.10::0:iqn.2025.ggnet:target-001"
            mock_generator.get_machine_script_filename.return_value = "machines/00-11-22-33-44-55.ipxe"
            mock_ipxe.return_value = mock_generator
            
            response = await client.get("/api/v1/sessions/machine/1/boot-script", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["machine_id"] == 1
            assert "script_content" in data
            assert "script_url" in data
            assert "iscsi_details" in data
            
            assert "#!ipxe" in data["script_content"]
            assert "sanboot iscsi:" in data["script_content"]
    
    @pytest.mark.asyncio
    async def test_get_session_stats(self, client: AsyncClient, admin_user, admin_token, db_session):
        """Test getting session statistics"""
        
        # Create test image first (let database assign ID)
        image = Image(
            name="test-image-stats",
            filename="test-stats.vhdx",
            file_path="/storage/images/test-stats.vhdx",
            format=ImageFormat.VHDX,
            status=ImageStatus.READY,
            size_bytes=1024*1024*1024,
            created_by=1
        )
        db_session.add(image)
        await db_session.flush()  # Get the ID without committing
        
        # Create test machines (let database assign IDs)
        machines = [
            Machine(name="machine-stats-1", mac_address="00:11:22:33:44:60", ip_address="192.168.1.110", status=MachineStatus.ACTIVE, boot_mode="LEGACY", created_by=1),
            Machine(name="machine-stats-2", mac_address="00:11:22:33:44:61", ip_address="192.168.1.111", status=MachineStatus.ACTIVE, boot_mode="LEGACY", created_by=1),
            Machine(name="machine-stats-3", mac_address="00:11:22:33:44:62", ip_address="192.168.1.112", status=MachineStatus.ACTIVE, boot_mode="LEGACY", created_by=1),
        ]
        db_session.add_all(machines)
        await db_session.flush()  # Get the IDs without committing
        
        # Create test targets (let database assign IDs)
        targets = [
            Target(target_id="target-stats-1", iqn="iqn.2025.ggnet:target-stats-1", machine_id=machines[0].id, image_id=image.id, image_path="/storage/images/test-stats1.vhdx", initiator_iqn="iqn.2025.ggnet:initiator-stats-1", lun_id=0, status=TargetStatus.ACTIVE, created_by=1),
            Target(target_id="target-stats-2", iqn="iqn.2025.ggnet:target-stats-2", machine_id=machines[1].id, image_id=image.id, image_path="/storage/images/test-stats2.vhdx", initiator_iqn="iqn.2025.ggnet:initiator-stats-2", lun_id=0, status=TargetStatus.ACTIVE, created_by=1),
            Target(target_id="target-stats-3", iqn="iqn.2025.ggnet:target-stats-3", machine_id=machines[2].id, image_id=image.id, image_path="/storage/images/test-stats3.vhdx", initiator_iqn="iqn.2025.ggnet:initiator-stats-3", lun_id=0, status=TargetStatus.ACTIVE, created_by=1),
        ]
        db_session.add_all(targets)
        await db_session.flush()  # Get the IDs without committing
        
        # Create test sessions with different statuses (let database assign IDs)
        sessions = [
            Session(session_id="session-stats-1", machine_id=machines[0].id, target_id=targets[0].id, session_type=SessionType.DISKLESS_BOOT, status=SessionStatus.ACTIVE, started_at=datetime.utcnow(), server_ip="192.168.1.10"),
            Session(session_id="session-stats-2", machine_id=machines[1].id, target_id=targets[1].id, session_type=SessionType.DISKLESS_BOOT, status=SessionStatus.STOPPED, started_at=datetime.utcnow(), ended_at=datetime.utcnow(), server_ip="192.168.1.10"),
            Session(session_id="session-stats-3", machine_id=machines[2].id, target_id=targets[2].id, session_type=SessionType.DISKLESS_BOOT, status=SessionStatus.ERROR, started_at=datetime.utcnow(), server_ip="192.168.1.10"),
        ]
        db_session.add_all(sessions)
        await db_session.commit()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.get("/api/v1/sessions/stats", headers=headers)
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_sessions" in data
        assert "active_sessions" in data
        assert "status_counts" in data
        
        assert data["total_sessions"] == 3
        assert data["active_sessions"] == 1
        assert data["status_counts"]["active"] == 1
        assert data["status_counts"]["stopped"] == 1
        assert data["status_counts"]["error"] == 1


class TestiPXEScriptGeneration:
    """Test iPXE script generation"""
    
    def test_generate_machine_boot_script(self):
        """Test generating boot script for a machine"""
        from app.adapters.ipxe import iPXEScriptGenerator
        from app.models.machine import Machine, MachineStatus
        from app.models.target import Target, TargetStatus
        from app.models.image import Image, ImageStatus, ImageFormat
        
        # Create test objects
        machine = Machine(
            id=1,
            name="test-workstation",
            mac_address="00:11:22:33:44:55",
            ip_address="192.168.1.101",
            status=MachineStatus.ACTIVE,
            boot_mode="bios",
            created_by=1
        )
        
        target = Target(
            id=1,
            target_id="target-001",
            iqn="iqn.2025.ggnet:target-001",
            machine_id=1,
            image_id=1,
            image_path="/storage/images/test.vhdx",
            initiator_iqn="iqn.2025.ggnet:initiator-001122334455",
            lun_id=0,
            status=TargetStatus.ACTIVE,
            created_by=1
        )
        
        image = Image(
            id=1,
            name="test-image",
            filename="test.vhdx",
            file_path="/storage/images/test.vhdx",
            format=ImageFormat.VHDX,
            status=ImageStatus.READY,
            size_bytes=1024*1024*1024,
        )
        
        # Generate script
        generator = iPXEScriptGenerator()
        script = generator.generate_machine_boot_script(machine, target, image)
        
        # Verify script content
        assert "#!ipxe" in script
        assert "Booting test-workstation" in script
        assert "sanboot iscsi:" in script
        assert "iqn.2025.ggnet:target-001" in script
        assert "192.168.1.10" in script  # Default portal IP
    
    def test_generate_generic_boot_script(self):
        """Test generating generic boot script"""
        from app.adapters.ipxe import iPXEScriptGenerator
        
        generator = iPXEScriptGenerator()
        script = generator.generate_generic_boot_script()
        
        # Verify script content
        assert "#!ipxe" in script
        assert "Welcome to GGnet Diskless System" in script
        assert "chain tftp://" in script
        assert "machines/" in script
    
    def test_get_machine_script_filename(self):
        """Test getting machine script filename"""
        from app.adapters.ipxe import iPXEScriptGenerator
        from app.models.machine import Machine, MachineStatus
        
        machine = Machine(
            id=1,
            name="test-workstation",
            mac_address="00:11:22:33:44:55",
            ip_address="192.168.1.101",
            status=MachineStatus.ACTIVE,
            boot_mode="bios",
            created_by=1
        )
        
        generator = iPXEScriptGenerator()
        filename = generator.get_machine_script_filename(machine)
        
        assert filename == "machines/00-11-22-33-44-55.ipxe"
    
    def test_validate_script_syntax(self):
        """Test script syntax validation"""
        from app.adapters.ipxe import iPXEScriptGenerator
        
        generator = iPXEScriptGenerator()
        
        # Valid script
        valid_script = """#!ipxe
echo Booting...
sanboot iscsi:192.168.1.10::0:iqn.2025.ggnet:target-001"""
        
        assert generator.validate_script_syntax(valid_script) == True
        
        # Invalid script (missing shebang)
        invalid_script = """echo Booting...
sanboot iscsi:192.168.1.10::0:iqn.2025.ggnet:target-001"""
        
        assert generator.validate_script_syntax(invalid_script) == False
        
        # Invalid script (missing sanboot)
        invalid_script2 = """#!ipxe
echo Booting..."""
        
        assert generator.validate_script_syntax(invalid_script2) == False


class TestDHCPConfiguration:
    """Test DHCP configuration management"""
    
    @pytest.mark.asyncio
    async def test_generate_dhcp_config_entry(self):
        """Test generating DHCP configuration entry"""
        from app.adapters.dhcp import generate_dhcp_config_entry
        from app.models.machine import Machine, MachineStatus
        
        machine = Machine(
            id=1,
            name="test-workstation",
            mac_address="00:11:22:33:44:55",
            ip_address="192.168.1.101",
            status=MachineStatus.ACTIVE,
            boot_mode="bios",
            created_by=1
        )
        
        config_entry = generate_dhcp_config_entry(machine)
        
        assert "host test-workstation" in config_entry
        assert "hardware ethernet 00:11:22:33:44:55" in config_entry
        assert "fixed-address 192.168.1.101" in config_entry
        assert "filename \"machines/00-11-22-33-44-55.ipxe\"" in config_entry
    
    @pytest.mark.asyncio
    async def test_dhcp_adapter_status(self):
        """Test DHCP adapter status checking"""
        from app.adapters.dhcp import DHCPAdapter
        
        adapter = DHCPAdapter()
        
        # Mock systemctl command
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "active"
            
            # Mock file operations
            with patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = True
                
                with patch("builtins.open", mock_open("test content")):
                    status = await adapter.get_dhcp_status()
                    
                    assert "service_running" in status
                    assert "config_file_exists" in status
                    assert "machines_configured" in status


class TestTFTPManagement:
    """Test TFTP file management"""
    
    @pytest.mark.asyncio
    async def test_tftp_adapter_status(self):
        """Test TFTP adapter status checking"""
        from app.adapters.tftp import TFTPAdapter
        
        adapter = TFTPAdapter()
        
        # Mock systemctl command
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "active"
            
            # Mock file operations
            with patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = True
                
                with patch("pathlib.Path.iterdir") as mock_iterdir:
                    mock_iterdir.return_value = []
                    
                    status = await adapter.get_tftp_status()
                    
                    assert "service_running" in status
                    assert "tftp_root_exists" in status
                    assert "machines_dir_exists" in status
                    assert "boot_dir_exists" in status
    
    def test_extract_mac_from_filename(self):
        """Test extracting MAC address from filename"""
        from app.adapters.tftp import TFTPAdapter
        
        adapter = TFTPAdapter()
        
        # Valid filename
        mac = adapter._extract_mac_from_filename("00-11-22-33-44-55.ipxe")
        assert mac == "00:11:22:33:44:55"
        
        # Invalid filename
        mac = adapter._extract_mac_from_filename("invalid.ipxe")
        assert mac is None


# Helper function for mocking file operations
def mock_open(content):
    """Mock file open operation"""
    from unittest.mock import mock_open as mock_open_func
    return mock_open_func(read_data=content)
