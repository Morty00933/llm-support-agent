import pytest
from httpx import AsyncClient


@pytest.mark.auth
@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="function")
class TestAuthentication:
    
    async def test_fr_1_1_register_user_success(self, client: AsyncClient, test_tenant):
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "ValidPass987",
                "full_name": "New User",
                "tenant_id": test_tenant.id,
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["tenant_id"] == test_tenant.id
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
    
    async def test_fr_1_1_register_duplicate_email(self, client: AsyncClient, test_user):
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "ValidPass987",
                "tenant_id": test_user.tenant_id,
            },
        )
        
        assert response.status_code in [400, 409]
        data = response.json()
        # Check for either 'detail', 'message', or 'title' field (RFC 7807)
        error_msg = data.get("detail", data.get("message", data.get("title", ""))).lower()
        assert "already registered" in error_msg or "already exists" in error_msg
    
    async def test_fr_1_1_register_short_password(self, client: AsyncClient, test_tenant):
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "123",
                "tenant_id": test_tenant.id,
            },
        )
        
        assert response.status_code == 422
    
    async def test_fr_1_2_login_json_success(self, client: AsyncClient, test_user):
        response = await client.post(
            "/v1/auth/login/json",
            json={
                "email": test_user.email,
                "password": "Testpass123",
                "tenant_id": test_user.tenant_id,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
    
    async def test_fr_1_2_login_wrong_password(self, client: AsyncClient, test_user):
        response = await client.post(
            "/v1/auth/login/json",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
                "tenant_id": test_user.tenant_id,
            },
        )
        
        assert response.status_code == 401
    
    async def test_fr_1_2_login_nonexistent_user(self, client: AsyncClient, test_tenant):
        response = await client.post(
            "/v1/auth/login/json",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword",
                "tenant_id": test_tenant.id,
            },
        )
        
        assert response.status_code == 401
    
    async def test_fr_1_3_get_current_user(self, client: AsyncClient, auth_headers, test_user):
        response = await client.get("/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id
        assert data["tenant_id"] == test_user.tenant_id
    
    async def test_fr_1_3_get_current_user_unauthorized(self, client: AsyncClient):
        response = await client.get("/v1/auth/me")
        
        assert response.status_code == 401
    
    async def test_fr_1_4_refresh_token(self, client: AsyncClient, test_user):
        login_response = await client.post(
            "/v1/auth/login/json",
            json={
                "email": test_user.email,
                "password": "Testpass123",
                "tenant_id": test_user.tenant_id,
            },
        )
        refresh_token = login_response.json()["refresh_token"]
        
        response = await client.post(
            "/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    async def test_fr_1_5_update_profile(self, client: AsyncClient, auth_headers):
        response = await client.patch(
            "/v1/auth/me",
            headers=auth_headers,
            json={"full_name": "Updated Name"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
    
    async def test_fr_1_6_change_password(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "Testpass123",
                "new_password": "Newpass123",
            },
        )

        assert response.status_code == 200
    
    async def test_fr_1_6_change_password_wrong_current(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "wrongpassword",
                "new_password": "newpass123",
            },
        )
        
        assert response.status_code in [400, 409]
