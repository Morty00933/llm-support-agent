from __future__ import annotations

import asyncio
import logging

import httpx
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from . import routers as r
from .middlewares import setup_middlewares
from ..core.config import settings
from ..core.db import get_session

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

# CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Метрики/счётчики
setup_middlewares(app)


@app.on_event("startup")
async def startup_checks() -> None:
    if settings.EMBEDDING_DIM <= 0:
        raise RuntimeError("EMBEDDING_DIM must be greater than zero")
    if not settings.OLLAMA_MODEL_EMBED.strip():
        raise RuntimeError("OLLAMA_MODEL_EMBED must be configured")

    base_url = settings.OLLAMA_BASE_URL.strip()
    if not base_url:
        raise RuntimeError("OLLAMA_BASE_URL must be configured")

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(3.0, connect=2.0)) as client:
            await client.get(f"{base_url.rstrip('/')}/api/version")
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("Ollama base URL %s is not reachable: %s", base_url, exc)


@app.get("/health", response_class=PlainTextResponse)
async def health() -> str:
    return "ok"


@app.get("/health/deps")
async def health_deps() -> JSONResponse:
    payload: dict[str, object] = {"database": False, "ollama": False}
    status_code = status.HTTP_200_OK

    try:
        async with get_session() as session:
            await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=3.0)
        payload["database"] = True
    except Exception as exc:  # pragma: no cover - requires external services
        payload["database_error"] = str(exc)
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(3.0, connect=2.0)) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/version")
        if response.is_success:
            payload["ollama"] = True
        else:  # pragma: no cover - depends on external service
            payload["ollama_error"] = f"HTTP {response.status_code}"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    except Exception as exc:  # pragma: no cover - network dependent
        payload["ollama_error"] = str(exc)
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(status_code=status_code, content=payload)


@app.get("/metrics")
def metrics() -> Response:
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# Подключение роутеров
app.include_router(r.admin.router)
app.include_router(r.auth.router)
app.include_router(r.kb.router)
app.include_router(r.tickets.router)
app.include_router(r.support.router)
