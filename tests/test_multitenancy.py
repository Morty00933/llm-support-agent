import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="function")
class TestMultiTenancy:
    
    async def test_fr_5_1_get_current_tenant(
        self, client: AsyncClient, auth_headers, test_tenant
    ):
        response = await client.get(
            "/v1/tenants/current", headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_tenant.id
        assert data["name"] == test_tenant.name
        assert data["slug"] == test_tenant.slug
        assert data["is_active"] is True
    
    async def test_fr_5_2_get_tenant_stats(
        self, client: AsyncClient, auth_headers, test_ticket, test_kb_chunks
    ):
        response = await client.get(
            "/v1/tenants/current/stats", headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tickets_by_status" in data
        assert "total_tickets" in data
        assert "total_users" in data
        assert "total_kb_chunks" in data
        assert isinstance(data["tickets_by_status"], dict)
        assert isinstance(data["total_tickets"], int)
        assert isinstance(data["total_users"], int)
        assert isinstance(data["total_kb_chunks"], int)
    
    async def test_fr_5_3_tenant_data_isolation_tickets(
        self,
        client: AsyncClient,
        test_ticket,
        second_tenant_headers,
    ):
        response = await client.get(
            f"/v1/tickets/{test_ticket.id}",
            headers=second_tenant_headers,
        )
        
        assert response.status_code == 404
    
    async def test_fr_5_3_tenant_data_isolation_kb_chunks(
        self,
        client: AsyncClient,
        test_kb_chunks,
        second_tenant_headers,
    ):
        response = await client.get(
            "/v1/kb/chunks",
            headers=second_tenant_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        chunk_ids = [chunk["id"] for chunk in data]
        test_chunk_ids = [chunk.id for chunk in test_kb_chunks]
        
        for test_id in test_chunk_ids:
            assert test_id not in chunk_ids
    
    async def test_fr_5_3_tenant_isolation_create_ticket(
        self,
        client: AsyncClient,
        auth_headers,
        second_tenant_headers,
        test_user,
        second_tenant_user,
    ):
        response1 = await client.post(
            "/v1/tickets",
            headers=auth_headers,
            json={"title": "Ticket from tenant 1"},
        )
        assert response1.status_code == 201
        ticket1_id = response1.json()["id"]
        
        response2 = await client.post(
            "/v1/tickets",
            headers=second_tenant_headers,
            json={"title": "Ticket from tenant 2"},
        )
        assert response2.status_code == 201
        ticket2_id = response2.json()["id"]
        
        get_response = await client.get(
            f"/v1/tickets/{ticket2_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404
        
        get_response2 = await client.get(
            f"/v1/tickets/{ticket1_id}",
            headers=second_tenant_headers,
        )
        assert get_response2.status_code == 404
    
    async def test_fr_5_3_tenant_isolation_messages(
        self,
        client: AsyncClient,
        test_ticket,
        second_tenant_headers,
    ):
        response = await client.get(
            f"/v1/tickets/{test_ticket.id}/messages",
            headers=second_tenant_headers,
        )
        
        assert response.status_code == 404
    
    async def test_fr_5_list_all_tenants_as_admin(
        self,
        client: AsyncClient,
        admin_headers,
        test_tenant,
        second_tenant,
    ):
        response = await client.get(
            "/v1/tenants",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        
        tenant_ids = [t["id"] for t in data]
        assert test_tenant.id in tenant_ids
        assert second_tenant.id in tenant_ids
    
    async def test_fr_5_list_all_tenants_as_user_forbidden(
        self,
        client: AsyncClient,
        auth_headers,
    ):
        response = await client.get(
            "/v1/tenants",
            headers=auth_headers,
        )
        
        assert response.status_code == 403
    
    async def test_fr_5_users_cannot_access_other_tenant_users(
        self,
        client: AsyncClient,
        test_user,
        second_tenant_user,
        auth_headers,
    ):
        response = await client.get(
            "/v1/auth/me",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == test_user.tenant_id
        assert data["tenant_id"] != second_tenant_user.tenant_id
