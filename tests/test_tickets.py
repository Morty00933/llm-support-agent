import pytest
from httpx import AsyncClient
from unittest.mock import patch


@pytest.mark.tickets
@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="function")
class TestTickets:
    
    async def test_fr_2_1_create_ticket(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/v1/tickets",
            headers=auth_headers,
            json={
                "title": "Cannot login to account",
                "description": "I forgot my password",
                "priority": "high",
                "auto_respond": False,
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Cannot login to account"
        assert data["description"] == "I forgot my password"
        assert data["status"] == "open"
        assert data["priority"] == "high"
        assert "id" in data
        assert "tenant_id" in data
    
    async def test_fr_2_1_create_ticket_with_auto_respond(
        self, client: AsyncClient, auth_headers, test_kb_chunks
    ):
        response = await client.post(
            "/v1/tickets",
            headers=auth_headers,
            json={
                "title": "How to recover password?",
                "auto_respond": True,
            },
        )
        
        assert response.status_code == 201
    
    async def test_fr_2_2_list_tickets(
        self, client: AsyncClient, auth_headers, test_ticket
    ):
        response = await client.get("/v1/tickets", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["title"] == test_ticket.title
    
    async def test_fr_2_2_list_tickets_filtered_by_status(
        self, client: AsyncClient, auth_headers, test_ticket
    ):
        response = await client.get(
            "/v1/tickets?status=open", headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(t["status"] == "open" for t in data)
    
    async def test_fr_2_2_list_tickets_with_pagination(
        self, client: AsyncClient, auth_headers
    ):
        response = await client.get(
            "/v1/tickets?skip=0&limit=10", headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10
    
    async def test_fr_2_3_get_ticket_by_id(
        self, client: AsyncClient, auth_headers, test_ticket
    ):
        response = await client.get(
            f"/v1/tickets/{test_ticket.id}", headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_ticket.id
        assert data["title"] == test_ticket.title
    
    async def test_fr_2_3_get_ticket_not_found(
        self, client: AsyncClient, auth_headers
    ):
        response = await client.get("/v1/tickets/99999", headers=auth_headers)
        
        assert response.status_code == 404
    
    async def test_fr_2_4_update_ticket_status(
        self, client: AsyncClient, auth_headers, test_ticket
    ):
        response = await client.patch(
            f"/v1/tickets/{test_ticket.id}",
            headers=auth_headers,
            json={"status": "in_progress", "priority": "urgent"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["priority"] == "urgent"
    
    async def test_fr_2_4_update_ticket_valid_statuses(
        self, client: AsyncClient, auth_headers, test_ticket
    ):
        valid_statuses = [
            "open", "in_progress", "pending_customer", "pending_agent",
            "escalated", "resolved", "closed", "reopened"
        ]
        
        for status in valid_statuses:
            response = await client.patch(
                f"/v1/tickets/{test_ticket.id}",
                headers=auth_headers,
                json={"status": status},
            )
            assert response.status_code == 200
            assert response.json()["status"] == status
    
    async def test_fr_2_5_delete_ticket_as_admin(
        self, client: AsyncClient, admin_headers, test_ticket
    ):
        response = await client.delete(
            f"/v1/tickets/{test_ticket.id}", headers=admin_headers
        )
        
        assert response.status_code == 204
    
    async def test_fr_2_5_delete_ticket_as_user_forbidden(
        self, client: AsyncClient, auth_headers, test_ticket
    ):
        response = await client.delete(
            f"/v1/tickets/{test_ticket.id}", headers=auth_headers
        )
        
        assert response.status_code == 403
    
    async def test_fr_2_6_add_message_to_ticket(
        self, client: AsyncClient, auth_headers, test_ticket
    ):
        response = await client.post(
            f"/v1/tickets/{test_ticket.id}/messages",
            headers=auth_headers,
            json={
                "content": "Please help me!",
                "role": "user",
                "auto_respond": False,
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Please help me!"
        assert data["role"] == "user"
        assert data["ticket_id"] == test_ticket.id
    
    @patch("src.services.agent.get_ollama_client")
    async def test_fr_2_6_add_message_with_auto_respond(
        self, mock_get_ollama, client: AsyncClient, auth_headers, test_ticket, test_kb_chunks
    ):
        from unittest.mock import MagicMock
        mock_ollama = MagicMock()
        mock_ollama.embed.return_value = [0.1] * 768
        mock_ollama.generate.return_value = "To reset your password, click Forgot Password."
        mock_get_ollama.return_value = mock_ollama

        response = await client.post(
            f"/v1/tickets/{test_ticket.id}/messages",
            headers=auth_headers,
            json={
                "content": "How to reset password?",
                "role": "user",
                "auto_respond": True,
            },
        )

        assert response.status_code == 201
    
    async def test_fr_2_7_get_ticket_messages(
        self, client: AsyncClient, auth_headers, test_ticket, db_session
    ):
        from src.domain.repos import create_message
        
        await create_message(
            db_session,
            ticket_id=test_ticket.id,
            content="User message",
            role="user",
        )
        await create_message(
            db_session,
            ticket_id=test_ticket.id,
            content="Agent response",
            role="assistant",
        )
        await db_session.commit()
        
        response = await client.get(
            f"/v1/tickets/{test_ticket.id}/messages", headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert data[0]["role"] in ["user", "assistant"]
