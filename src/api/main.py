from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response, PlainTextResponse
from .middlewares import setup_middlewares
from ..core.config import settings
from . import routers as r

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


@app.get("/health", response_class=PlainTextResponse)
async def health():
    return "ok"


@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# Подключение роутеров
app.include_router(r.admin.router)
app.include_router(r.auth.router)
app.include_router(r.kb.router)
app.include_router(r.tickets.router)
app.include_router(r.support.router)
