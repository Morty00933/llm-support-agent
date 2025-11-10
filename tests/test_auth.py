import asyncio

from httpx import ASGITransport, AsyncClient

from src.api.main import app


def test_login_returns_access_token() -> None:
    async def runner() -> None:
        payload = {"email": "user@example.com", "password": "secret", "tenant": 7}
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/v1/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"access_token", "token_type"}
        assert isinstance(data["access_token"], str) and data["access_token"]
        assert data["token_type"] == "bearer"

    asyncio.run(runner())
