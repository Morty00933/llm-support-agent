# -*- coding: utf-8 -*-
"""FastAPI Application Entry Point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.core.config import settings
from src.core.db import get_db, close_db
from src.core.errors.handlers import setup_exception_handlers
from src.api.middlewares import RequestLoggingMiddleware, RedisRateLimitMiddleware

from src.api.routers.auth import router as auth_router
from src.api.routers.tickets import router as tickets_router
from src.api.routers.kb import router as kb_router
from src.api.routers.integrations import router as integrations_router
from src.api.routers.tenants import router as tenants_router
from src.api.routers.agent import router as agent_router
from src.api.routers.websockets import router as websockets_router
from src.api.routers.demo import router as demo_router
from src.api.routers.users import router as users_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.env}")
    logger.info(f"Debug: {settings.debug}")

    db = settings.database
    logger.info(f"Database: {db.host}:{db.port}/{db.name}")

    ollama = settings.ollama
    logger.info(f"Ollama: {ollama.base_url} (chat: {ollama.model_chat}, embed: {ollama.model_embed})")

    redis_cfg = settings.redis
    logger.info(f"Redis: {redis_cfg.host}:{redis_cfg.port}/{redis_cfg.db}")

    yield

    logger.info("Shutting down...")
    await close_db()

    try:
        from src.services.ollama import close_ollama_client
        await close_ollama_client()
    except Exception as e:
        logger.warning(f"Error closing Ollama client: {e}")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="LLM-powered Support Agent API",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

redis_client = Redis.from_url(settings.redis.dsn, decode_responses=False)
app.add_middleware(
    RedisRateLimitMiddleware,
    redis_client=redis_client,
    max_requests=100,
    window_seconds=60,
)


setup_exception_handlers(app)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/health/ready", tags=["health"])
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Readiness check with database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ready" if db_status == "connected" else "not_ready",
        "database": db_status,
    }


@app.get("/health/live", tags=["health"])
async def liveness_check() -> dict:
    """Liveness check."""
    return {"status": "alive"}


if settings.prometheus_enabled:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from starlette.responses import Response

    @app.get("/metrics", tags=["metrics"], include_in_schema=False)
    async def metrics() -> Response:
        """Prometheus metrics endpoint."""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )


app.include_router(auth_router, prefix="/v1/auth")
app.include_router(users_router, prefix="/v1/users")
app.include_router(tickets_router, prefix="/v1/tickets")
app.include_router(kb_router, prefix="/v1/kb")
app.include_router(integrations_router, prefix="/v1/integrations")
app.include_router(tenants_router, prefix="/v1/tenants")
app.include_router(agent_router, prefix="/v1/agent")
app.include_router(websockets_router, prefix="/v1", tags=["WebSocket"])

if settings.demo_mode_enabled:
    app.include_router(demo_router, prefix="/v1/demo")


@app.get("/", tags=["root"])
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "disabled",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers,
        log_level=settings.log_level.lower(),
    )
