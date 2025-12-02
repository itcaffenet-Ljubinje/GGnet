"""
Tests for targetcli adapter
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
import tempfile
import os
from pathlib import Path

from app.adapters.targetcli import TargetCLIAdapter, TargetCLIError, create_target_for_machine, delete_target_for_machine


class TestTargetCLIAdapter:
    """Tests for TargetCLIAdapter class"""

    @pytest.fixture
    def adapter(self):
        """Create TargetCLIAdapter instance for testing"""
        with patch('app.adapters.targetcli.get_settings') as mock_settings:
            mock_settings.return_value.TARGETCLI_PATH = "/usr/bin/targetcli"
            mock_settings.return_value.ISCSI_TARGET_PREFIX = "iqn.2025.ggnet"
            mock_settings.return_value.ISCSI_PORTAL_IP = "0.0.0.0"
            mock_settings.return_value.ISCSI_PORTAL_PORT = 3260
            return TargetCLIAdapter()

    @pytest.mark.asyncio
    async def test_adapter_initialization(self, adapter):
        """Test adapter initialization"""
        assert adapter.targetcli_path == "/usr/bin/targetcli"
        assert adapter.iscsi_prefix == "iqn.2025.ggnet"
        assert adapter.portal_ip == "0.0.0.0"
        assert adapter.portal_port == 3260

    @pytest.mark.asyncio
    async def test_check_targetcli_available(self, adapter):
        """Test targetcli availability check"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "targetcli version 2.1.53"
            
            result = adapter._check_targetcli()
            assert result is True
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_targetcli_unavailable(self, adapter):
        """Test targetcli unavailability check"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            result = adapter._check_targetcli()
            assert result is False

    @pytest.mark.asyncio
    async def test_run_targetcli_command_success(self, adapter):
        """Test successful targetcli command execution"""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess, \
             patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
             patch('os.unlink') as mock_unlink:
            
            # Mock temporary file
            mock_file = MagicMock()
            mock_file.name = "/tmp/test_script.py"
            mock_tempfile.return_value.__enter__.return_value = mock_file
            
            # Mock subprocess
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"success", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            stdout, stderr, returncode = await adapter._run_targetcli_command(["ls"])
            
            assert stdout == "success"
            assert stderr == ""
            assert returncode == 0
            mock_unlink.assert_called_once_with("/tmp/test_script.py")

    @pytest.mark.asyncio
    async def test_run_targetcli_command_timeout(self, adapter):
        """Test targetcli command timeout"""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess, \
             patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
             patch('os.unlink') as mock_unlink:
            
            # Mock temporary file
            mock_file = MagicMock()
            mock_file.name = "/tmp/test_script.py"
            mock_tempfile.return_value.__enter__.return_value = mock_file
            
            # Mock subprocess that times out
            mock_process = AsyncMock()
            mock_process.communicate.side_effect = TimeoutError()
            mock_subprocess.return_value = mock_process
            
            with pytest.raises(TargetCLIError, match="Command timed out"):
                await adapter._run_targetcli_command(["ls"], timeout=1)

    @pytest.mark.asyncio
    async def test_create_fileio_backstore_success(self, adapter):
        """Test successful fileio backstore creation"""
        with patch.object(adapter, '_run_targetcli_command') as mock_run, \
             patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=1024*1024*100):
            
            mock_run.return_value = ("", "", 0)
            
            result = await adapter.create_fileio_backstore("test_backstore", "/tmp/test.img")
            
            assert result["name"] == "test_backstore"
            assert result["type"] == "fileio"
            assert result["file_path"] == "/tmp/test.img"
            assert result["size"] == 1024*1024*100

    @pytest.mark.asyncio
    async def test_create_fileio_backstore_file_not_exists(self, adapter):
        """Test fileio backstore creation with non-existent file"""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(TargetCLIError, match="File does not exist"):
                await adapter.create_fileio_backstore("test_backstore", "/tmp/nonexistent.img")

    @pytest.mark.asyncio
    async def test_create_fileio_backstore_with_size(self, adapter):
        """Test fileio backstore creation with size parameter"""
        with patch.object(adapter, '_run_targetcli_command') as mock_run, \
             patch('os.path.exists', return_value=False), \
             patch('builtins.open', create=True) as mock_open, \
             patch('os.path.getsize', return_value=1024*1024*50):
            
            mock_run.return_value = ("", "", 0)
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = await adapter.create_fileio_backstore("test_backstore", "/tmp/test.img", 1024*1024*50)
            
            assert result["name"] == "test_backstore"
            mock_file.truncate.assert_called_once_with(1024*1024*50)

    @pytest.mark.asyncio
    async def test_create_iscsi_target_success(self, adapter):
        """Test successful iSCSI target creation"""
        with patch.object(adapter, '_run_targetcli_command') as mock_run:
            mock_run.return_value = ("", "", 0)
            
            result = await adapter.create_iscsi_target("test123", "Test target")
            
            assert result["iqn"] == "iqn.2025.ggnet:target-test123"
            assert result["target_id"] == "test123"
            assert result["description"] == "Test target"
            assert result["portal_ip"] == "0.0.0.0"
            assert result["portal_port"] == 3260

    @pytest.mark.asyncio
    async def test_create_iscsi_target_failure(self, adapter):
        """Test iSCSI target creation failure"""
        with patch.object(adapter, '_run_targetcli_command') as mock_run:
            mock_run.return_value = ("", "Target already exists", 1)
            
            with pytest.raises(TargetCLIError, match="Failed to create iSCSI target"):
                await adapter.create_iscsi_target("test123")

    @pytest.mark.asyncio
    async def test_create_lun_success(self, adapter):
        """Test successful LUN creation"""
        with patch.object(adapter, '_run_targetcli_command') as mock_run:
            mock_run.return_value = ("", "", 0)
            
            result = await adapter.create_lun("iqn.2025.ggnet:target-test", "/backstores/fileio/test", 0)
            
            assert result["lun_id"] == 0
            assert result["iqn"] == "iqn.2025.ggnet:target-test"
            assert result["backstore_path"] == "/backstores/fileio/test"

    @pytest.mark.asyncio
    async def test_create_acl_success(self, adapter):
        """Test successful ACL creation"""
        with patch.object(adapter, '_run_targetcli_command') as mock_run:
            mock_run.return_value = ("", "", 0)
            
            result = await adapter.create_acl("iqn.2025.ggnet:target-test", "iqn.2025.ggnet:initiator-abc123")
            
            assert result["iqn"] == "iqn.2025.ggnet:target-test"
            assert result["initiator_iqn"] == "iqn.2025.ggnet:initiator-abc123"

    @pytest.mark.asyncio
    async def test_enable_target_portal_success(self, adapter):
        """Test successful portal enabling"""
        with patch.object(adapter, '_run_targetcli_command') as mock_run:
            mock_run.return_value = ("", "", 0)
            
            result = await adapter.enable_target_portal("iqn.2025.ggnet:target-test")
            
            assert result["iqn"] == "iqn.2025.ggnet:target-test"
            assert result["ip"] == "0.0.0.0"
            assert result["port"] == 3260

    @pytest.mark.asyncio
    async def test_enable_target_portal_custom_ip_port(self, adapter):
        """Test portal enabling with custom IP and port"""
        with patch.object(adapter, '_run_targetcli_command') as mock_run:
            mock_run.return_value = ("", "", 0)
            
            result = await adapter.enable_target_portal("iqn.2025.ggnet:target-test", "192.168.1.100", 3261)
            
            assert result["ip"] == "192.168.1.100"
            assert result["port"] == 3261

    @pytest.mark.asyncio
    async def test_create_complete_target_success(self, adapter):
        """Test successful complete target creation"""
        with patch.object(adapter, 'create_fileio_backstore') as mock_backstore, \
             patch.object(adapter, 'create_iscsi_target') as mock_target, \
             patch.object(adapter, 'create_lun') as mock_lun, \
             patch.object(adapter, 'create_acl') as mock_acl, \
             patch.object(adapter, 'enable_target_portal') as mock_portal, \
             patch.object(adapter, 'save_config') as mock_save:
            
            # Mock all the individual operations
            mock_backstore.return_value = {"name": "img_test123", "type": "fileio", "file_path": "/tmp/test.img", "size": 1024*1024*100}
            mock_target.return_value = {"iqn": "iqn.2025.ggnet:target-test123", "target_id": "test123", "description": "Test", "portal_ip": "0.0.0.0", "portal_port": 3260}
            mock_lun.return_value = {"lun_id": 0, "iqn": "iqn.2025.ggnet:target-test123", "backstore_path": "/backstores/fileio/img_test123"}
            mock_acl.return_value = {"iqn": "iqn.2025.ggnet:target-test123", "initiator_iqn": "iqn.2025.ggnet:initiator-abc123"}
            mock_portal.return_value = {"iqn": "iqn.2025.ggnet:target-test123", "ip": "0.0.0.0", "port": 3260}
            mock_save.return_value = True
            
            result = await adapter.create_complete_target(
                target_id="test123",
                image_path="/tmp/test.img",
                initiator_iqn="iqn.2025.ggnet:initiator-abc123",
                description="Test target"
            )
            
            assert result["target_id"] == "test123"
            assert result["iqn"] == "iqn.2025.ggnet:target-test123"
            assert result["image_path"] == "/tmp/test.img"
            assert result["initiator_iqn"] == "iqn.2025.ggnet:initiator-abc123"
            assert "created_at" in result

    @pytest.mark.asyncio
    async def test_create_complete_target_cleanup_on_failure(self, adapter):
        """Test cleanup when complete target creation fails"""
        with patch.object(adapter, 'create_fileio_backstore') as mock_backstore, \
             patch.object(adapter, 'create_iscsi_target') as mock_target, \
             patch.object(adapter, 'delete_target') as mock_delete:
            
            # Mock successful backstore creation but failed target creation
            mock_backstore.return_value = {"name": "img_test123", "type": "fileio", "file_path": "/tmp/test.img", "size": 1024*1024*100}
            mock_target.side_effect = TargetCLIError("Target creation failed")
            mock_delete.return_value = True
            
            with pytest.raises(TargetCLIError, match="Target creation failed"):
                await adapter.create_complete_target(
                    target_id="test123",
                    image_path="/tmp/test.img",
                    initiator_iqn="iqn.2025.ggnet:initiator-abc123"
                )
            
            # Verify cleanup was attempted
            mock_delete.assert_called_once_with("test123")

    @pytest.mark.asyncio
    async def test_delete_target_success(self, adapter):
        """Test successful target deletion"""
        with patch.object(adapter, '_run_targetcli_command') as mock_run, \
             patch.object(adapter, 'save_config') as mock_save:
            
            # Mock successful deletion commands
            mock_run.return_value = ("", "", 0)
            mock_save.return_value = True
            
            result = await adapter.delete_target("test123")
            
            assert result is True
            # Verify all deletion commands were called
            assert mock_run.call_count == 4  # ACL, LUN, target, backstore

    @pytest.mark.asyncio
    async def test_list_targets_success(self, adapter):
        """Test successful target listing"""
        with patch.object(adapter, '_run_targetcli_command') as mock_run:
            mock_output = """
iscsi/iqn.2025.ggnet:target-test123 [tpg1]
iscsi/iqn.2025.ggnet:target-test456 [tpg1]
"""
            mock_run.return_value = (mock_output, "", 0)
            
            result = await adapter.list_targets()
            
            assert len(result) == 2
            assert result[0]["iqn"] == "iqn.2025.ggnet:target-test123"
            assert result[0]["target_id"] == "test123"
            assert result[1]["iqn"] == "iqn.2025.ggnet:target-test456"
            assert result[1]["target_id"] == "test456"

    @pytest.mark.asyncio
    async def test_save_config_success(self, adapter):
        """Test successful configuration save"""
        with patch.object(adapter, '_run_targetcli_command') as mock_run:
            mock_run.return_value = ("", "", 0)
            
            result = await adapter.save_config()
            
            assert result is True

    @pytest.mark.asyncio
    async def test_get_target_status_success(self, adapter):
        """Test successful target status retrieval"""
        with patch.object(adapter, '_run_targetcli_command') as mock_run:
            mock_output = """
tpg1 [active]
 luns
  lun0 [fileio/img_test123]
 acls
  iqn.2025.ggnet:initiator-abc123
 portals
  0.0.0.0:3260
"""
            mock_run.return_value = (mock_output, "", 0)
            
            result = await adapter.get_target_status("test123")
            
            assert result["target_id"] == "test123"
            assert result["iqn"] == "iqn.2025.ggnet:target-test123"
            assert result["status"] == "active"
            assert len(result["luns"]) > 0
            assert len(result["acls"]) > 0
            assert len(result["portals"]) > 0

    @pytest.mark.asyncio
    async def test_get_target_status_not_found(self, adapter):
        """Test target status for non-existent target"""
        with patch.object(adapter, '_run_targetcli_command') as mock_run:
            mock_run.return_value = ("", "Target not found", 1)
            
            result = await adapter.get_target_status("nonexistent")
            
            assert result["target_id"] == "nonexistent"
            assert result["status"] == "not_found"
            assert "error" in result


class TestTargetCLIConvenienceFunctions:
    """Tests for convenience functions"""

    @pytest.mark.asyncio
    async def test_create_target_for_machine(self):
        """Test create_target_for_machine convenience function"""
        with patch('app.adapters.targetcli.TargetCLIAdapter') as mock_adapter_class:
            mock_adapter = AsyncMock()
            mock_adapter_class.return_value = mock_adapter
            
            mock_adapter.create_complete_target.return_value = {
                "target_id": "machine_123",
                "iqn": "iqn.2025.ggnet:target-machine_123",
                "initiator_iqn": "iqn.2025.ggnet:initiator-abc123def456",
                "created_at": "2025-01-01T00:00:00"
            }
            
            result = await create_target_for_machine(
                machine_id=123,
                machine_mac="ab:c1:23:de:f4:56",
                image_path="/tmp/test.img",
                description="Test machine target"
            )
            
            assert result["target_id"] == "machine_123"
            assert result["iqn"] == "iqn.2025.ggnet:target-machine_123"
            assert result["initiator_iqn"] == "iqn.2025.ggnet:initiator-abc123def456"
            
            # Verify adapter was called with correct parameters
            mock_adapter.create_complete_target.assert_called_once_with(
                target_id="machine_123",
                image_path="/tmp/test.img",
                initiator_iqn="iqn.2025.ggnet:initiator-abc123def456",
                description="Test machine target"
            )

    @pytest.mark.asyncio
    async def test_delete_target_for_machine(self):
        """Test delete_target_for_machine convenience function"""
        with patch('app.adapters.targetcli.TargetCLIAdapter') as mock_adapter_class:
            mock_adapter = AsyncMock()
            mock_adapter_class.return_value = mock_adapter
            
            mock_adapter.delete_target.return_value = True
            
            result = await delete_target_for_machine(machine_id=123)
            
            assert result is True
            mock_adapter.delete_target.assert_called_once_with("machine_123")
