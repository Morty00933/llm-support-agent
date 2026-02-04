"""Tests for users router and role management."""
import pytest
from httpx import AsyncClient


@pytest.mark.users
@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="function")
class TestUsersRouter:
    """Tests for /v1/users endpoints."""

    async def test_list_users_as_admin(
        self, client: AsyncClient, admin_headers, test_user, test_admin
    ):
        """Test admin can list users."""
        response = await client.get("/v1/users", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least test_user and test_admin

    async def test_list_users_as_user_forbidden(
        self, client: AsyncClient, auth_headers
    ):
        """Test user cannot list users."""
        response = await client.get("/v1/users", headers=auth_headers)

        assert response.status_code == 403

    async def test_create_user_as_admin(
        self, client: AsyncClient, admin_headers, test_tenant
    ):
        """Test admin can create new user."""
        response = await client.post(
            "/v1/users",
            headers=admin_headers,
            json={
                "email": "newuser@test.com",
                "password": "SecurePass123",
                "full_name": "New User",
                "role": "user",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "user"
        assert data["tenant_id"] == test_tenant.id

    async def test_create_agent_as_admin(
        self, client: AsyncClient, admin_headers
    ):
        """Test admin can create agent."""
        response = await client.post(
            "/v1/users",
            headers=admin_headers,
            json={
                "email": "newagent@test.com",
                "password": "SecurePass123",
                "full_name": "New Agent",
                "role": "agent",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "agent"

    async def test_create_admin_as_admin(
        self, client: AsyncClient, admin_headers
    ):
        """Test admin can create another admin."""
        response = await client.post(
            "/v1/users",
            headers=admin_headers,
            json={
                "email": "newadmin@test.com",
                "password": "SecurePass123",
                "full_name": "New Admin",
                "role": "admin",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "admin"

    async def test_create_superadmin_forbidden(
        self, client: AsyncClient, admin_headers
    ):
        """Test cannot create superadmin via API.

        Note: Pydantic schema validates role before reaching business logic,
        so we get 422 (validation error) instead of 403 (forbidden).
        """
        response = await client.post(
            "/v1/users",
            headers=admin_headers,
            json={
                "email": "superadmin@test.com",
                "password": "SecurePass123",
                "role": "superadmin",
            },
        )

        # 422 because Pydantic schema only allows user/agent/admin roles
        assert response.status_code == 422

    async def test_create_user_as_user_forbidden(
        self, client: AsyncClient, auth_headers
    ):
        """Test user cannot create users."""
        response = await client.post(
            "/v1/users",
            headers=auth_headers,
            json={
                "email": "another@test.com",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 403

    async def test_get_user_by_id_as_admin(
        self, client: AsyncClient, admin_headers, test_user
    ):
        """Test admin can get user by ID."""
        response = await client.get(
            f"/v1/users/{test_user.id}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    async def test_get_user_not_found(
        self, client: AsyncClient, admin_headers
    ):
        """Test get non-existent user returns 404."""
        response = await client.get(
            "/v1/users/99999",
            headers=admin_headers,
        )

        assert response.status_code == 404

    async def test_update_user_as_admin(
        self, client: AsyncClient, admin_headers, test_user
    ):
        """Test admin can update user."""
        response = await client.patch(
            f"/v1/users/{test_user.id}",
            headers=admin_headers,
            json={"full_name": "Updated Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"

    async def test_deactivate_user_as_admin(
        self, client: AsyncClient, admin_headers, test_user
    ):
        """Test admin can deactivate user."""
        response = await client.delete(
            f"/v1/users/{test_user.id}",
            headers=admin_headers,
        )

        assert response.status_code == 204


@pytest.mark.users
@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="function")
class TestRoleManagement:
    """Tests for role change functionality."""

    async def test_change_user_role_to_agent(
        self, client: AsyncClient, admin_headers, test_user
    ):
        """Test admin can promote user to agent."""
        response = await client.patch(
            f"/v1/users/{test_user.id}/role",
            headers=admin_headers,
            json={"role": "agent"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "agent"

    async def test_change_agent_role_to_admin(
        self, client: AsyncClient, admin_headers, db_session, test_tenant
    ):
        """Test admin can promote agent to admin."""
        from src.domain.repos import UserRepository
        from src.core.security import get_password_hash

        # Create agent user
        user_repo = UserRepository(db_session)
        agent = await user_repo.create(
            tenant_id=test_tenant.id,
            email="agent_to_promote@test.com",
            hashed_password=get_password_hash("Password123"),
            full_name="Agent To Promote",
            role="agent",
        )
        await db_session.commit()

        response = await client.patch(
            f"/v1/users/{agent.id}/role",
            headers=admin_headers,
            json={"role": "admin"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"

    async def test_cannot_change_own_role(
        self, client: AsyncClient, admin_headers, test_admin
    ):
        """Test admin cannot change their own role."""
        response = await client.patch(
            f"/v1/users/{test_admin.id}/role",
            headers=admin_headers,
            json={"role": "user"},
        )

        assert response.status_code == 400
        # Check error is present in response
        data = response.json()
        assert "title" in data or "detail" in data

    async def test_cannot_set_superadmin_role(
        self, client: AsyncClient, admin_headers, test_user
    ):
        """Test cannot set superadmin role via API.

        Note: Pydantic schema validates role before reaching business logic,
        so we get 422 (validation error) instead of 403 (forbidden).
        """
        response = await client.patch(
            f"/v1/users/{test_user.id}/role",
            headers=admin_headers,
            json={"role": "superadmin"},
        )

        # 422 because Pydantic schema only allows user/agent/admin roles
        assert response.status_code == 422

    async def test_user_cannot_change_roles(
        self, client: AsyncClient, auth_headers, test_admin
    ):
        """Test regular user cannot change roles."""
        response = await client.patch(
            f"/v1/users/{test_admin.id}/role",
            headers=auth_headers,
            json={"role": "user"},
        )

        assert response.status_code == 403


@pytest.mark.users
@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="function")
class TestKBRoleProtection:
    """Tests for KB router role protection."""

    async def test_user_cannot_create_kb_chunks(
        self, client: AsyncClient, auth_headers
    ):
        """Test regular user cannot create KB chunks."""
        response = await client.post(
            "/v1/kb/chunks",
            headers=auth_headers,
            json={
                "source": "test.md",
                "chunks": [{"content": "Test content"}],
            },
        )

        assert response.status_code == 403

    async def test_agent_can_create_kb_chunks(
        self, client: AsyncClient, db_session, test_tenant
    ):
        """Test agent can create KB chunks."""
        from src.domain.repos import UserRepository
        from src.core.security import get_password_hash

        # Create agent user
        user_repo = UserRepository(db_session)
        agent = await user_repo.create(
            tenant_id=test_tenant.id,
            email="kbagent@test.com",
            hashed_password=get_password_hash("Password123"),
            role="agent",
        )
        await db_session.commit()

        # Login as agent
        login_response = await client.post(
            "/v1/auth/login/json",
            json={
                "email": "kbagent@test.com",
                "password": "Password123",
                "tenant_id": test_tenant.id,
            },
        )
        agent_token = login_response.json()["access_token"]
        agent_headers = {"Authorization": f"Bearer {agent_token}"}

        response = await client.post(
            "/v1/kb/chunks",
            headers=agent_headers,
            json={
                "source": "test.md",
                "chunks": [{"content": "Test content from agent"}],
            },
        )

        assert response.status_code == 201

    async def test_user_cannot_delete_kb_source(
        self, client: AsyncClient, auth_headers
    ):
        """Test regular user cannot delete KB source."""
        response = await client.delete(
            "/v1/kb/sources/test.md",
            headers=auth_headers,
        )

        assert response.status_code == 403

    async def test_admin_can_delete_kb_source(
        self, client: AsyncClient, admin_headers
    ):
        """Test admin can delete KB source."""
        response = await client.delete(
            "/v1/kb/sources/nonexistent.md",
            headers=admin_headers,
        )

        # 200 even if source doesn't exist (idempotent delete)
        assert response.status_code == 200

    async def test_user_can_read_kb_chunks(
        self, client: AsyncClient, auth_headers
    ):
        """Test regular user CAN read KB chunks."""
        response = await client.get(
            "/v1/kb/chunks",
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_user_can_search_kb(
        self, client: AsyncClient, auth_headers
    ):
        """Test regular user CAN search KB."""
        response = await client.post(
            "/v1/kb/search",
            headers=auth_headers,
            json={"query": "password reset", "limit": 5},
        )

        assert response.status_code == 200
