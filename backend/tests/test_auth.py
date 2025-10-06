"""
Test authentication endpoints
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


class TestAuth:
    """Test authentication functionality."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, admin_user):
        """Test successful login."""
        response = await client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient, admin_user):
        """Test login with invalid credentials."""
        response = await client.post("/auth/login", json={
            "username": "admin",
            "password": "wrong_password"
        })
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "authentication_error"
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user."""
        response = await client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "password"
        })
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "authentication_error"
    
    @pytest.mark.asyncio
    async def test_login_validation_error(self, client: AsyncClient):
        """Test login with invalid data."""
        response = await client.post("/auth/login", json={
            "username": "",
            "password": "123"
        })
        
        # Should return 401 for invalid credentials (empty username)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, admin_token, auth_headers):
        """Test getting current user info."""
        response = await client.get(
            "/auth/me",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == "admin"
        assert data["role"] == "admin"
        assert data["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/auth/me")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient, auth_headers):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/auth/me",
            headers=auth_headers("invalid_token")
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, admin_user):
        """Test token refresh."""
        # First login
        login_response = await client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        
        # Refresh token
        refresh_response = await client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        
        assert "access_token" in refresh_data
        assert "refresh_token" in refresh_data
        assert refresh_data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post("/auth/refresh", json={
            "refresh_token": "invalid_refresh_token"
        })
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient, admin_token, auth_headers):
        """Test logout."""
        response = await client.post(
            "/auth/logout",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    @pytest.mark.asyncio
    async def test_logout_unauthorized(self, client: AsyncClient):
        """Test logout without token."""
        response = await client.post("/auth/logout")
        
        assert response.status_code == 401


class TestRoleBasedAccess:
    """Test role-based access control."""
    
    @pytest.mark.asyncio
    async def test_admin_access(self, client: AsyncClient, admin_token, auth_headers):
        """Test admin can access admin endpoints."""
        response = await client.get(
            "/auth/me",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
    
    @pytest.mark.asyncio
    async def test_operator_access(self, client: AsyncClient, operator_token, auth_headers):
        """Test operator can access operator endpoints."""
        response = await client.get(
            "/auth/me",
            headers=auth_headers(operator_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "operator"
    
    @pytest.mark.asyncio
    async def test_viewer_access(self, client: AsyncClient, viewer_token, auth_headers):
        """Test viewer can access viewer endpoints."""
        response = await client.get(
            "/auth/me",
            headers=auth_headers(viewer_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "viewer"

