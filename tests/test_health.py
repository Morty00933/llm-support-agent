import asyncio

from httpx import ASGITransport, AsyncClient

from src.api.main import app


def test_health_endpoint_returns_ok() -> None:
    async def runner() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
        assert response.status_code == 200
        assert response.text == "ok"

    asyncio.run(runner())
