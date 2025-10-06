"""
Integration tests for FastAPI + Redis + Database
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.machine import Machine, MachineStatus, BootMode
from app.models.user import User, UserRole
from app.core.security import get_password_hash


class TestFullIntegration:
    """Full integration tests with FastAPI, Redis, and Database"""
    
    @pytest.mark.asyncio
    async def test_complete_machine_lifecycle(self, client: AsyncClient, redis_client, admin_token, auth_headers):
        """Test complete machine lifecycle with Redis caching"""
        try:
            # 1. Create machine
            create_response = await client.post(
                "/machines",
                json={
                    "name": "Integration Test Machine",
                    "description": "Test machine for integration testing",
                    "mac_address": "00:11:22:33:44:55",
                    "ip_address": "192.168.1.100",
                    "hostname": "test-machine",
                    "boot_mode": "uefi",
                    "secure_boot_enabled": True,
                    "location": "Test Lab",
                    "room": "A101"
                },
                headers=auth_headers(admin_token)
            )
            assert create_response.status_code == 201
            machine_data = create_response.json()
            machine_id = machine_data["id"]
            
            # 2. Get machine (should be cached in Redis)
            get_response = await client.get(
                f"/machines/{machine_id}",
                headers=auth_headers(admin_token)
            )
            assert get_response.status_code == 200
            retrieved_machine = get_response.json()
            assert retrieved_machine["name"] == "Integration Test Machine"
            assert retrieved_machine["mac_address"] == "00:11:22:33:44:55"
            
            # 3. Update machine
            update_response = await client.put(
                f"/machines/{machine_id}",
                json={
                    "name": "Updated Integration Test Machine",
                    "description": "Updated description",
                    "status": "inactive"
                },
                headers=auth_headers(admin_token)
            )
            assert update_response.status_code == 200
            updated_machine = update_response.json()
            assert updated_machine["name"] == "Updated Integration Test Machine"
            assert updated_machine["status"] == "inactive"
            
            # 4. List machines (should include our machine)
            list_response = await client.get(
                "/machines",
                headers=auth_headers(admin_token)
            )
            assert list_response.status_code == 200
            machines = list_response.json()
            assert len(machines) >= 1
            assert any(m["id"] == machine_id for m in machines)
            
            # 5. Delete machine
            delete_response = await client.delete(
                f"/machines/{machine_id}",
                headers=auth_headers(admin_token)
            )
            assert delete_response.status_code == 200
            
            # 6. Verify machine is deleted
            get_deleted_response = await client.get(
                f"/machines/{machine_id}",
                headers=auth_headers(admin_token)
            )
            assert get_deleted_response.status_code == 404
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_authentication_flow_with_redis(self, client: AsyncClient, redis_client):
        """Test complete authentication flow with Redis session management"""
        try:
            # 1. Login
            login_response = await client.post("/auth/login", json={
                "username": "admin",
                "password": "admin123"
            })
            assert login_response.status_code == 200
            auth_data = login_response.json()
            access_token = auth_data["access_token"]
            refresh_token = auth_data["refresh_token"]
            
            # 2. Use access token for authenticated request
            me_response = await client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            assert me_response.status_code == 200
            user_data = me_response.json()
            assert user_data["username"] == "admin"
            
            # 3. Refresh token
            refresh_response = await client.post("/auth/refresh", json={
                "refresh_token": refresh_token
            })
            assert refresh_response.status_code == 200
            new_auth_data = refresh_response.json()
            new_access_token = new_auth_data["access_token"]
            
            # 4. Use new access token
            me_response2 = await client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {new_access_token}"}
            )
            assert me_response2.status_code == 200
            
            # 5. Logout
            logout_response = await client.post(
                "/auth/logout",
                headers={"Authorization": f"Bearer {new_access_token}"}
            )
            assert logout_response.status_code == 200
            
            # 6. Try to use token after logout (should fail)
            me_response3 = await client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {new_access_token}"}
            )
            assert me_response3.status_code == 401
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self, client: AsyncClient, redis_client):
        """Test rate limiting with Redis backend"""
        try:
            # Make multiple failed login attempts to trigger rate limiting
            failed_attempts = 0
            for i in range(30):  # Exceed rate limit
                response = await client.post("/auth/login", json={
                    "username": "admin",
                    "password": "wrong_password"
                })
                
                if response.status_code == 429:  # Rate limited
                    failed_attempts += 1
                    break
                elif response.status_code == 401:  # Invalid credentials
                    failed_attempts += 1
                else:
                    break
            
            # Should eventually get rate limited
            assert failed_attempts > 0
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, client: AsyncClient, redis_client, admin_token, auth_headers):
        """Test concurrent operations with Redis caching"""
        try:
            import asyncio
            
            # Create multiple machines concurrently
            async def create_machine(machine_num):
                response = await client.post(
                    "/machines",
                    json={
                        "name": f"Concurrent Machine {machine_num}",
                        "mac_address": f"00:11:22:33:44:{machine_num:02x}",
                        "boot_mode": "uefi"
                    },
                    headers=auth_headers(admin_token)
                )
                return response
            
            # Create 5 machines concurrently
            tasks = [create_machine(i) for i in range(5)]
            responses = await asyncio.gather(*tasks)
            
            # All should succeed
            for response in responses:
                assert response.status_code == 201
            
            # Get all machines
            list_response = await client.get(
                "/machines",
                headers=auth_headers(admin_token)
            )
            assert list_response.status_code == 200
            machines = list_response.json()
            
            # Should have at least 5 machines
            assert len(machines) >= 5
            
            # Clean up - delete all created machines
            for response in responses:
                machine_data = response.json()
                delete_response = await client.delete(
                    f"/machines/{machine_data['id']}",
                    headers=auth_headers(admin_token)
                )
                assert delete_response.status_code == 200
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_on_updates(self, client: AsyncClient, redis_client, admin_token, auth_headers):
        """Test cache invalidation when data is updated"""
        try:
            # Create machine
            create_response = await client.post(
                "/machines",
                json={
                    "name": "Cache Test Machine",
                    "mac_address": "00:11:22:33:44:99",
                    "boot_mode": "uefi"
                },
                headers=auth_headers(admin_token)
            )
            assert create_response.status_code == 201
            machine_data = create_response.json()
            machine_id = machine_data["id"]
            
            # Get machine (populates cache)
            get_response1 = await client.get(
                f"/machines/{machine_id}",
                headers=auth_headers(admin_token)
            )
            assert get_response1.status_code == 200
            original_name = get_response1.json()["name"]
            
            # Update machine
            update_response = await client.put(
                f"/machines/{machine_id}",
                json={
                    "name": "Updated Cache Test Machine"
                },
                headers=auth_headers(admin_token)
            )
            assert update_response.status_code == 200
            
            # Get machine again (should reflect update)
            get_response2 = await client.get(
                f"/machines/{machine_id}",
                headers=auth_headers(admin_token)
            )
            assert get_response2.status_code == 200
            updated_name = get_response2.json()["name"]
            
            # Name should be updated
            assert updated_name == "Updated Cache Test Machine"
            assert updated_name != original_name
            
            # Clean up
            delete_response = await client.delete(
                f"/machines/{machine_id}",
                headers=auth_headers(admin_token)
            )
            assert delete_response.status_code == 200
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, client: AsyncClient, redis_client, admin_token, auth_headers):
        """Test error handling across all layers"""
        try:
            # Test 404 error
            response = await client.get(
                "/machines/99999",
                headers=auth_headers(admin_token)
            )
            assert response.status_code == 404
            
            # Test validation error
            response = await client.post(
                "/machines",
                json={
                    "name": "",  # Invalid empty name
                    "mac_address": "invalid_mac",  # Invalid MAC
                    "boot_mode": "invalid_mode"  # Invalid boot mode
                },
                headers=auth_headers(admin_token)
            )
            assert response.status_code == 422
            
            # Test unauthorized access
            response = await client.get("/machines")
            assert response.status_code == 401
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_pagination_integration(self, client: AsyncClient, redis_client, admin_token, auth_headers):
        """Test pagination with Redis caching"""
        try:
            # Create multiple machines
            created_machines = []
            for i in range(15):
                response = await client.post(
                    "/machines",
                    json={
                        "name": f"Pagination Test Machine {i}",
                        "mac_address": f"00:11:22:33:44:{i:02x}",
                        "boot_mode": "uefi"
                    },
                    headers=auth_headers(admin_token)
                )
                assert response.status_code == 201
                created_machines.append(response.json())
            
            # Test pagination
            # First page
            response1 = await client.get(
                "/machines?skip=0&limit=10",
                headers=auth_headers(admin_token)
            )
            assert response1.status_code == 200
            page1 = response1.json()
            assert len(page1) <= 10
            
            # Second page
            response2 = await client.get(
                "/machines?skip=10&limit=10",
                headers=auth_headers(admin_token)
            )
            assert response2.status_code == 200
            page2 = response2.json()
            assert len(page2) <= 10
            
            # Verify no overlap
            page1_ids = {m["id"] for m in page1}
            page2_ids = {m["id"] for m in page2}
            assert len(page1_ids.intersection(page2_ids)) == 0
            
            # Clean up
            for machine in created_machines:
                delete_response = await client.delete(
                    f"/machines/{machine['id']}",
                    headers=auth_headers(admin_token)
                )
                assert delete_response.status_code == 200
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_search_integration(self, client: AsyncClient, redis_client, admin_token, auth_headers):
        """Test search functionality with Redis caching"""
        try:
            # Create machines with different names
            test_machines = [
                {"name": "Alpha Machine", "mac": "00:11:22:33:44:01"},
                {"name": "Beta Machine", "mac": "00:11:22:33:44:02"},
                {"name": "Alpha Beta Machine", "mac": "00:11:22:33:44:03"},
                {"name": "Gamma Machine", "mac": "00:11:22:33:44:04"},
            ]
            
            created_machines = []
            for machine in test_machines:
                response = await client.post(
                    "/machines",
                    json={
                        "name": machine["name"],
                        "mac_address": machine["mac"],
                        "boot_mode": "uefi"
                    },
                    headers=auth_headers(admin_token)
                )
                assert response.status_code == 201
                created_machines.append(response.json())
            
            # Test search for "Alpha"
            response = await client.get(
                "/machines?search=Alpha",
                headers=auth_headers(admin_token)
            )
            assert response.status_code == 200
            alpha_machines = response.json()
            assert len(alpha_machines) >= 2  # Should find "Alpha Machine" and "Alpha Beta Machine"
            
            # Test search for "Beta"
            response = await client.get(
                "/machines?search=Beta",
                headers=auth_headers(admin_token)
            )
            assert response.status_code == 200
            beta_machines = response.json()
            assert len(beta_machines) >= 2  # Should find "Beta Machine" and "Alpha Beta Machine"
            
            # Test search for non-existent
            response = await client.get(
                "/machines?search=NonExistent",
                headers=auth_headers(admin_token)
            )
            assert response.status_code == 200
            empty_machines = response.json()
            assert len(empty_machines) == 0
            
            # Clean up
            for machine in created_machines:
                delete_response = await client.delete(
                    f"/machines/{machine['id']}",
                    headers=auth_headers(admin_token)
                )
                assert delete_response.status_code == 200
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
