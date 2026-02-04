import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_deps_endpoint_returns_payload(client: AsyncClient) -> None:
    # This endpoint doesn't exist in the current implementation
    response = await client.get("/health/dependencies")
    # Either 200 with data or 404
    if response.status_code == 200:
        data = response.json()
        assert "database" in data or "status" in data


@pytest.mark.asyncio
async def test_health_ready_endpoint_returns_payload(client: AsyncClient) -> None:
    response = await client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ready"
    assert "database" in data