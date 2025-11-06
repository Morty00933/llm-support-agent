import sys
from pathlib import Path

import pytest
from httpx import AsyncClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.api.main import app


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c


async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200


async def test_ticket_flow(client: AsyncClient):
    r = await client.post("/v1/support/tickets", json={"text": "Как вернуть деньги?"})
    assert r.status_code in (200, 201)
