import pytest
from httpx import AsyncClient
from unittest.mock import patch


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio(loop_scope="function")
class TestE2EScenarios:
    
    async def test_e2e_complete_ticket_flow(
        self, client: AsyncClient, test_tenant
    ):
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "e2e@example.com",
                "password": "Pass123456",
                "tenant_id": test_tenant.id,
            },
        )
        assert response.status_code == 201

        login_response = await client.post(
            "/v1/auth/login/json",
            json={
                "email": "e2e@example.com",
                "password": "Pass123456",
                "tenant_id": test_tenant.id,
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        ticket_response = await client.post(
            "/v1/tickets",
            headers=headers,
            json={
                "title": "Need help with password",
                "description": "I forgot my password",
                "priority": "medium",
                "auto_respond": False,
            },
        )
        assert ticket_response.status_code == 201
        ticket_id = ticket_response.json()["id"]

        message_response = await client.post(
            f"/v1/tickets/{ticket_id}/messages",
            headers=headers,
            json={
                "content": "How do I reset my password?",
                "role": "user",
                "auto_respond": False,
            },
        )
        assert message_response.status_code == 201

        messages_response = await client.get(
            f"/v1/tickets/{ticket_id}/messages",
            headers=headers,
        )
        assert messages_response.status_code == 200
        assert len(messages_response.json()) >= 1

        update_response = await client.patch(
            f"/v1/tickets/{ticket_id}",
            headers=headers,
            json={"status": "resolved"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "resolved"
    
    @patch("src.services.ollama.OllamaClient.generate")
    @patch("src.services.ollama.OllamaClient.embed")
    async def test_e2e_ai_assisted_support(
        self, mock_embed, mock_generate, client: AsyncClient, admin_headers, test_admin
    ):
        """Test AI-assisted support flow using admin user (has KB access)."""
        mock_embed.return_value = [0.1] * 768
        mock_generate.return_value = "To reset your password, click Forgot Password."

        # Add KB chunks (requires agent/admin role)
        kb_response = await client.post(
            "/v1/kb/chunks",
            headers=admin_headers,
            json={
                "source": "faq.md",
                "chunks": [
                    {"content": "To reset password, click Forgot Password link."}
                ],
            },
        )
        assert kb_response.status_code in [200, 201]  # Accept both OK and Created

        # Create ticket with auto_respond
        ticket_response = await client.post(
            "/v1/tickets",
            headers=admin_headers,
            json={
                "title": "Password reset",
                "auto_respond": True,
            },
        )
        assert ticket_response.status_code == 201
        ticket_id = ticket_response.json()["id"]

        # Check AI response was generated
        messages_response = await client.get(
            f"/v1/tickets/{ticket_id}/messages",
            headers=admin_headers,
        )
        messages = messages_response.json()
        assistant_messages = [m for m in messages if m["role"] == "assistant"]
        assert len(assistant_messages) >= 1
    
    async def test_e2e_multi_tenant_isolation(
        self, client: AsyncClient, test_tenant, second_tenant
    ):
        user1_response = await client.post(
            "/v1/auth/register",
            json={
                "email": "tenant1@example.com",
                "password": "ValidPass987",
                "tenant_id": test_tenant.id,
            },
        )
        assert user1_response.status_code == 201

        user2_response = await client.post(
            "/v1/auth/register",
            json={
                "email": "tenant2@example.com",
                "password": "ValidPass987",
                "tenant_id": second_tenant.id,
            },
        )
        assert user2_response.status_code == 201

        login1 = await client.post(
            "/v1/auth/login/json",
            json={
                "email": "tenant1@example.com",
                "password": "ValidPass987",
                "tenant_id": test_tenant.id,
            },
        )
        token1 = login1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        login2 = await client.post(
            "/v1/auth/login/json",
            json={
                "email": "tenant2@example.com",
                "password": "ValidPass987",
                "tenant_id": second_tenant.id,
            },
        )
        token2 = login2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        ticket1 = await client.post(
            "/v1/tickets",
            headers=headers1,
            json={"title": "Tenant 1 ticket"},
        )
        ticket1_id = ticket1.json()["id"]
        
        ticket2 = await client.post(
            "/v1/tickets",
            headers=headers2,
            json={"title": "Tenant 2 ticket"},
        )
        ticket2_id = ticket2.json()["id"]
        
        cross_access1 = await client.get(
            f"/v1/tickets/{ticket2_id}",
            headers=headers1,
        )
        assert cross_access1.status_code == 404
        
        cross_access2 = await client.get(
            f"/v1/tickets/{ticket1_id}",
            headers=headers2,
        )
        assert cross_access2.status_code == 404
    
    @patch("src.services.ollama.OllamaClient.generate")
    @patch("src.services.ollama.OllamaClient.embed")
    async def test_e2e_escalation_workflow(
        self, mock_embed, mock_generate, client: AsyncClient, auth_headers, test_ticket
    ):
        mock_embed.return_value = [0.1] * 768
        mock_generate.return_value = "I will forward your refund request."

        message_response = await client.post(
            f"/v1/tickets/{test_ticket.id}/messages",
            headers=auth_headers,
            json={
                "content": "I want a refund immediately!",
                "auto_respond": True,
            },
        )
        assert message_response.status_code == 201

        ticket_response = await client.get(
            f"/v1/tickets/{test_ticket.id}",
            headers=auth_headers,
        )
        ticket = ticket_response.json()
        assert ticket["status"] in ["escalated", "open"]
    
    async def test_e2e_password_change_flow(
        self, client: AsyncClient, test_tenant
    ):
        register_response = await client.post(
            "/v1/auth/register",
            json={
                "email": "pwchange@example.com",
                "password": "Oldpass123",
                "tenant_id": test_tenant.id,
            },
        )
        assert register_response.status_code == 201

        login1 = await client.post(
            "/v1/auth/login/json",
            json={
                "email": "pwchange@example.com",
                "password": "Oldpass123",
                "tenant_id": test_tenant.id,
            },
        )
        assert login1.status_code == 200
        token = login1.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        change_response = await client.post(
            "/v1/auth/change-password",
            headers=headers,
            json={
                "current_password": "Oldpass123",
                "new_password": "Newpass123",
            },
        )
        assert change_response.status_code == 200

        login_old = await client.post(
            "/v1/auth/login/json",
            json={
                "email": "pwchange@example.com",
                "password": "Oldpass123",
                "tenant_id": test_tenant.id,
            },
        )
        assert login_old.status_code == 401

        login_new = await client.post(
            "/v1/auth/login/json",
            json={
                "email": "pwchange@example.com",
                "password": "Newpass123",
                "tenant_id": test_tenant.id,
            },
        )
        assert login_new.status_code == 200
