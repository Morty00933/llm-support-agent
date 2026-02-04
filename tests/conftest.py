# -*- coding: utf-8 -*-
"""Pytest configuration and fixtures."""
from __future__ import annotations

import pytest
import pytest_asyncio
import uuid
from typing import AsyncGenerator, List
from unittest.mock import MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import event

from src.main import app
from src.core.db import get_db
from src.core.security import get_password_hash
from src.domain.models import Base, Tenant, User, Ticket, KBChunk

# ===================================================================
# ВАЖНО: URL для Docker-окружения
# Тесты запускаются ВНУТРИ контейнера backend, поэтому:
# - hostname: postgres (имя сервиса в docker-compose)
# - port: 5432 (внутренний порт)
# - database: llm_agent (используем ту же БД, что и для dev)
# ===================================================================
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@postgres:5432/llm_agent"


# ===================================================================
# DATABASE ENGINE & FIXTURES
# ===================================================================



@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Создаёт test engine один раз на всю сессию.
    Таблицы создаются один раз в начале и удаляются в конце.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,  # Отключаем пулинг для тестов
        echo=False,
    )

    # Создаём таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Удаляем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Создаёт новую сессию для каждого теста с автоматическим rollback.
    Все изменения в БД откатываются после каждого теста.

    Uses a shared connection with nested transaction to ensure all changes
    are visible within the test but rolled back after.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()

    async_session_maker = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        # Start a nested transaction (savepoint)
        await connection.begin_nested()

        # Intercept commits to use savepoints instead
        @event.listens_for(session.sync_session, "after_transaction_end")
        def restart_savepoint(session, transaction):
            if transaction.nested and not transaction._parent.nested:
                session.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()
            await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP-клиент с переопределённой зависимостью get_db."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    # Add X-Test-Client header to bypass rate limiting
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Test-Client": "pytest"}
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ===================================================================
# DATA FIXTURES - scope="function"
# Каждый тест получает свежие данные
# ===================================================================

@pytest_asyncio.fixture(scope="function")
async def test_tenant(db_session: AsyncSession) -> Tenant:
    """Создаёт тестового tenant с уникальным ID."""
    unique_id = str(uuid.uuid4())[:8]
    tenant = Tenant(
        name=f"Test Tenant {unique_id}",
        slug=f"test-tenant-{unique_id}",
        is_active=True,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession, test_tenant: Tenant) -> User:
    """Создаёт тестового пользователя с уникальным email."""
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        tenant_id=test_tenant.id,
        email=f"test-{unique_id}@example.com",
        hashed_password=get_password_hash("Testpass123"),
        full_name="Test User",
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_admin(db_session: AsyncSession, test_tenant: Tenant) -> User:
    """Создаёт тестового админа."""
    unique_id = str(uuid.uuid4())[:8]
    admin = User(
        tenant_id=test_tenant.id,
        email=f"admin-{unique_id}@example.com",
        hashed_password=get_password_hash("Adminpass123"),
        full_name="Admin User",
        role="admin",
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture(scope="function")
async def test_ticket(db_session: AsyncSession, test_tenant: Tenant, test_user: User) -> Ticket:
    """Создаёт тестовый тикет."""
    ticket = Ticket(
        tenant_id=test_tenant.id,
        title="Test Ticket",
        description="Test description",
        status="open",
        priority="medium",
        created_by_id=test_user.id,
    )
    db_session.add(ticket)
    await db_session.commit()
    await db_session.refresh(ticket)
    return ticket


@pytest_asyncio.fixture(scope="function")
async def test_kb_chunks(db_session: AsyncSession, test_tenant: Tenant) -> List[KBChunk]:
    """Создаёт тестовые KB chunks."""
    chunks = [
        KBChunk(
            tenant_id=test_tenant.id,
            source="test.md",
            chunk="This is test content about password recovery",
            chunk_hash="hash1",
            is_current=True,
        ),
        KBChunk(
            tenant_id=test_tenant.id,
            source="test.md",
            chunk="Support hours are 9AM to 6PM",
            chunk_hash="hash2",
            is_current=True,
        ),
    ]
    db_session.add_all(chunks)
    await db_session.flush()
    for chunk in chunks:
        await db_session.refresh(chunk)
    return chunks


@pytest_asyncio.fixture(scope="function")
async def second_tenant(db_session: AsyncSession) -> Tenant:
    """Создаёт второго tenant для тестов изоляции."""
    unique_id = str(uuid.uuid4())[:8]
    tenant = Tenant(
        name=f"Second Tenant {unique_id}",
        slug=f"second-tenant-{unique_id}",
        is_active=True,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture(scope="function")
async def second_tenant_user(db_session: AsyncSession, second_tenant: Tenant) -> User:
    """Создаёт пользователя для второго tenant."""
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        tenant_id=second_tenant.id,
        email=f"user-{unique_id}@example.com",
        hashed_password=get_password_hash("Pass1234"),
        full_name="Second User",
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ===================================================================
# AUTHENTICATION FIXTURES
# ===================================================================

@pytest_asyncio.fixture(scope="function")
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Получает JWT токен для test_user."""
    response = await client.post(
        "/v1/auth/login/json",
        json={
            "email": test_user.email,
            "password": "Testpass123",
            "tenant_id": test_user.tenant_id,
        },
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def admin_headers(client: AsyncClient, test_admin: User) -> dict:
    """Получает JWT токен для test_admin."""
    response = await client.post(
        "/v1/auth/login/json",
        json={
            "email": test_admin.email,
            "password": "Adminpass123",
            "tenant_id": test_admin.tenant_id,
        },
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def second_tenant_headers(client: AsyncClient, second_tenant_user: User) -> dict:
    """Получает JWT токен для second_tenant_user."""
    response = await client.post(
        "/v1/auth/login/json",
        json={
            "email": second_tenant_user.email,
            "password": "Pass1234",
            "tenant_id": second_tenant_user.tenant_id,
        },
    )
    assert response.status_code == 200, f"Second tenant login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ===================================================================
# MOCKS FOR UNIT TESTS
# ===================================================================

@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """
    Мокает Settings для unit-тестов.
    ВАЖНО: Правильная структура с вложенными конфигами.
    """
    class MockOllama:
        base_url = "http://ollama:11434"
        model_chat = "qwen2.5:3b"
        model_embed = "nomic-embed-text"
        timeout = 120
        temperature = 0.2
        embedding_dim = 768
    
    class MockJWT:
        secret = "test-secret-key-minimum-32-chars-long"
        algorithm = "HS256"
        expire_minutes = 60
        refresh_expire_days = 7
        access_token_expire_minutes = 60
        audience = "llm-support-agent"
        issuer = "llm-support-agent"
    
    class MockDatabase:
        host = "postgres"
        port = 5432
        user = "postgres"
        password = "postgres"
        name = "llm_agent"
        
        @property
        def async_url(self):
            return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    class MockSettings:
        # Плоские атрибуты для обратной совместимости
        ollama_base_url = "http://ollama:11434"
        ollama_model_chat = "qwen2.5:3b"
        ollama_model_embed = "nomic-embed-text"
        jwt_secret = "test-secret-key-minimum-32-chars-long"
        jwt_algorithm = "HS256"
        jwt_expire_minutes = 60
        jwt_refresh_expire_days = 7
        debug = False
        env = "test"
        
        # Вложенные конфиги
        ollama = MockOllama()
        jwt = MockJWT()
        database = MockDatabase()

    mock_obj = MockSettings()

    # Заменяем settings во всех модулях, включая security для JWT
    monkeypatch.setattr("src.services.agent.settings", mock_obj, raising=False)
    monkeypatch.setattr("src.services.ollama.settings", mock_obj, raising=False)
    monkeypatch.setattr("src.core.config.settings", mock_obj, raising=False)
    monkeypatch.setattr("src.api.routers.auth.settings", mock_obj, raising=False)
    monkeypatch.setattr("src.core.db.settings", mock_obj, raising=False)
    monkeypatch.setattr("src.core.security.settings", mock_obj, raising=False)


@pytest.fixture
def mock_ollama_client():
    """Мок OllamaClient для интеграционных тестов."""
    mock = MagicMock()
    mock.generate.return_value = "Mocked LLM response"
    mock.embed.return_value = [0.1] * 768
    mock.embed_batch.return_value = [[0.1] * 768, [0.2] * 768]
    mock.chat_model = "qwen2.5:3b"
    mock.embed_model = "nomic-embed-text"
    return mock