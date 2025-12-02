"""
Edge case tests for machine management
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.machine import Machine, MachineStatus, BootMode
from app.core.security import get_password_hash
from app.models.user import User, UserRole


class TestMachineEdgeCases:
    """Test edge cases for machine management"""
    
    @pytest.mark.asyncio
    async def test_create_machine_invalid_mac_formats(self, client: AsyncClient, admin_token, auth_headers):
        """Test machine creation with various invalid MAC address formats"""
        invalid_macs = [
            "",  # Empty
            "00:11:22:33:44",  # Too short
            "00:11:22:33:44:55:66",  # Too long
            "00:11:22:33:44:GG",  # Invalid characters
            "00:11:22:33:44:5g",  # Lowercase invalid char
            "00:11:22:33:44:5G",  # Mixed case invalid char
        ]
        
        valid_macs = [
            "00-11-22-33-44-56",  # Dashes (should be converted)
            "001122334457",  # No separators (should be converted)
        ]
        
        # Test invalid MACs
        for i, invalid_mac in enumerate(invalid_macs):
            response = await client.post(
                "/machines",
                json={
                    "name": f"Test Machine Invalid {i}",
                    "mac_address": invalid_mac,
                    "boot_mode": "uefi"
                },
                headers=auth_headers(admin_token)
            )
            assert response.status_code == 422
        
        # Test valid MACs (should be converted)
        for i, valid_mac in enumerate(valid_macs):
            response = await client.post(
                "/machines",
                json={
                    "name": f"Test Machine Valid {i}",
                    "mac_address": valid_mac,
                    "boot_mode": "uefi"
                },
                headers=auth_headers(admin_token)
            )
            assert response.status_code == 201
    
    @pytest.mark.asyncio
    async def test_create_machine_invalid_ip_formats(self, client: AsyncClient, admin_token, auth_headers):
        """Test machine creation with various invalid IP address formats"""
        invalid_ips = [
            "256.1.1.1",  # Out of range
            "1.256.1.1",  # Out of range
            "1.1.256.1",  # Out of range
            "1.1.1.256",  # Out of range
            "1.1.1",  # Too few octets
            "1.1.1.1.1",  # Too many octets
            "1.1.1.a",  # Non-numeric
            "1.1.1.-1",  # Negative
            "1.1.1.01",  # Leading zero
            "192.168.1",  # Incomplete
        ]
        
        for invalid_ip in invalid_ips:
            response = await client.post(
                "/machines",
                json={
                    "name": f"Test Machine {invalid_ip}",
                    "mac_address": "00:11:22:33:44:55",
                    "ip_address": invalid_ip,
                    "boot_mode": "uefi"
                },
                headers=auth_headers(admin_token)
            )
            
            assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_machine_extreme_values(self, client: AsyncClient, admin_token, auth_headers):
        """Test machine creation with extreme values"""
        # Very long name
        long_name = "A" * 1000
        response = await client.post(
            "/machines",
            json={
                "name": long_name,
                "mac_address": "00:11:22:33:44:55",
                "boot_mode": "uefi"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 422
        
        # Very long description
        long_description = "D" * 1000
        response = await client.post(
            "/machines",
            json={
                "name": "Test Machine",
                "description": long_description,
                "mac_address": "00:11:22:33:44:55",
                "boot_mode": "uefi"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_machine_empty_required_fields(self, client: AsyncClient, admin_token, auth_headers):
        """Test machine creation with empty required fields"""
        # Empty name
        response = await client.post(
            "/machines",
            json={
                "name": "",
                "mac_address": "00:11:22:33:44:55",
                "boot_mode": "uefi"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 422
        
        # Missing name
        response = await client.post(
            "/machines",
            json={
                "mac_address": "00:11:22:33:44:55",
                "boot_mode": "uefi"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 422
        
        # Missing MAC address
        response = await client.post(
            "/machines",
            json={
                "name": "Test Machine",
                "boot_mode": "uefi"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_machine_duplicate_mac(self, client: AsyncClient, admin_token, auth_headers, db_session):
        """Test creating machine with duplicate MAC address"""
        # Create first machine
        machine1 = Machine(
            name="Machine 1",
            mac_address="00:11:22:33:44:55",
            boot_mode=BootMode.UEFI,
            status=MachineStatus.ACTIVE,
            created_by=1  # Admin user ID
        )
        db_session.add(machine1)
        await db_session.commit()
        
        # Try to create second machine with same MAC
        response = await client.post(
            "/machines",
            json={
                "name": "Machine 2",
                "mac_address": "00:11:22:33:44:55",
                "boot_mode": "uefi"
            },
            headers=auth_headers(admin_token)
        )
        
        # Should fail due to unique constraint
        assert response.status_code == 409
    
    @pytest.mark.asyncio
    async def test_update_machine_nonexistent(self, client: AsyncClient, admin_token, auth_headers):
        """Test updating non-existent machine"""
        response = await client.put(
            "/machines/99999",
            json={
                "name": "Updated Machine"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_machine_nonexistent(self, client: AsyncClient, admin_token, auth_headers):
        """Test getting non-existent machine"""
        response = await client.get(
            "/machines/99999",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_machine_nonexistent(self, client: AsyncClient, admin_token, auth_headers):
        """Test deleting non-existent machine"""
        response = await client.delete(
            "/machines/99999",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_machine_pagination_edge_cases(self, client: AsyncClient, admin_token, auth_headers, db_session):
        """Test machine pagination with edge cases"""
        # Create many machines
        for i in range(25):
            machine = Machine(
                name=f"Machine {i}",
                mac_address=f"00:11:22:33:44:{i:02x}",
                boot_mode=BootMode.UEFI,
                status=MachineStatus.ACTIVE,
                created_by=1  # Admin user ID
            )
            db_session.add(machine)
        await db_session.commit()
        
        # Test negative skip
        response = await client.get(
            "/machines?skip=-1",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 422
        
        # Test negative limit
        response = await client.get(
            "/machines?limit=-1",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 422
        
        # Test very large limit (should be rejected)
        response = await client.get(
            "/machines?limit=10000",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 422
        
        # Test skip beyond available data
        response = await client.get(
            "/machines?skip=1000",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_machine_search_edge_cases(self, client: AsyncClient, admin_token, auth_headers, db_session):
        """Test machine search with edge cases"""
        # Create test machines
        machine1 = Machine(
            name="Test Machine Alpha",
            mac_address="00:11:22:33:44:01",
            boot_mode=BootMode.UEFI,
            status=MachineStatus.ACTIVE,
            created_by=1  # Admin user ID
        )
        machine2 = Machine(
            name="Test Machine Beta",
            mac_address="00:11:22:33:44:02",
            boot_mode=BootMode.LEGACY,
            status=MachineStatus.INACTIVE,
            created_by=1  # Admin user ID
        )
        db_session.add_all([machine1, machine2])
        await db_session.commit()
        
        # Test empty search
        response = await client.get(
            "/machines?search=",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        
        # Test search with special characters
        response = await client.get(
            "/machines?search=@#$%",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        
        # Test search with very long string
        long_search = "A" * 1000
        response = await client.get(
            f"/machines?search={long_search}",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_machine_status_transitions(self, client: AsyncClient, admin_token, auth_headers, db_session):
        """Test machine status transitions"""
        # Create machine
        machine = Machine(
            name="Status Test Machine",
            mac_address="00:11:22:33:44:99",
            boot_mode=BootMode.UEFI,
            status=MachineStatus.ACTIVE,
            created_by=1  # Admin user ID
        )
        db_session.add(machine)
        await db_session.commit()
        
        # Test invalid status
        response = await client.put(
            f"/machines/{machine.id}",
            json={
                "status": "invalid_status"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 422
        
        # Test valid status transitions
        valid_statuses = ["active", "inactive", "maintenance"]
        for status in valid_statuses:
            response = await client.put(
                f"/machines/{machine.id}",
                json={
                    "status": status
                },
                headers=auth_headers(admin_token)
            )
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_machine_boot_mode_validation(self, client: AsyncClient, admin_token, auth_headers):
        """Test machine boot mode validation"""
        # Test invalid boot mode
        response = await client.post(
            "/machines",
            json={
                "name": "Boot Mode Test",
                "mac_address": "00:11:22:33:44:88",
                "boot_mode": "invalid_mode"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 422
        
        # Test valid boot modes
        valid_modes = ["uefi", "legacy", "uefi_secure"]
        for i, mode in enumerate(valid_modes):
            response = await client.post(
                "/machines",
                json={
                    "name": f"Boot Mode Test {mode}",
                    "mac_address": f"00:11:22:33:44:{80+i:02x}",
                    "boot_mode": mode
                },
                headers=auth_headers(admin_token)
            )
            assert response.status_code == 201
    
    @pytest.mark.asyncio
    async def test_machine_unauthorized_access(self, client: AsyncClient, viewer_token, auth_headers):
        """Test unauthorized access to machine management"""
        # Viewer should not be able to create machines
        response = await client.post(
            "/machines",
            json={
                "name": "Unauthorized Test",
                "mac_address": "00:11:22:33:44:77",
                "boot_mode": "uefi"
            },
            headers=auth_headers(viewer_token)
        )
        assert response.status_code == 403
        
        # Viewer should not be able to update machines
        response = await client.put(
            "/machines/1",
            json={
                "name": "Updated Name"
            },
            headers=auth_headers(viewer_token)
        )
        assert response.status_code == 403
        
        # Viewer should not be able to delete machines
        response = await client.delete(
            "/machines/1",
            headers=auth_headers(viewer_token)
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_machine_concurrent_operations(self, client: AsyncClient, admin_token, auth_headers, db_session):
        """Test concurrent operations on machines"""
        # Create a machine
        machine = Machine(
            name="Concurrent Test Machine",
            mac_address="00:11:22:33:44:66",
            boot_mode=BootMode.UEFI,
            status=MachineStatus.ACTIVE,
            created_by=1  # Admin user ID
        )
        db_session.add(machine)
        await db_session.commit()
        
        # Simulate concurrent updates (in real scenario, this would be done with multiple clients)
        update_data1 = {"name": "Updated Name 1"}
        update_data2 = {"name": "Updated Name 2"}
        
        # First update
        response1 = await client.put(
            f"/machines/{machine.id}",
            json=update_data1,
            headers=auth_headers(admin_token)
        )
        assert response1.status_code == 200
        
        # Second update
        response2 = await client.put(
            f"/machines/{machine.id}",
            json=update_data2,
            headers=auth_headers(admin_token)
        )
        assert response2.status_code == 200
        
        # Verify final state
        response = await client.get(
            f"/machines/{machine.id}",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name 2"
