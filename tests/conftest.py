import pytest
from httpx import AsyncClient
from api.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
tests/test_auth.py
import jwt
from httpx import AsyncClient

async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
tests/test_agent_integration.py
from httpx import AsyncClient

async def test_ticket_flow(client: AsyncClient):
    r = await client.post("/v1/support/tickets", json={"text": "Как вернуть деньги?"})
    assert r.status_code in (200, 201)
