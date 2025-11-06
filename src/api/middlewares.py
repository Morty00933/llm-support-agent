from __future__ import annotations
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.metrics import HTTP_LATENCY, HTTP_REQUESTS


class MetricsMiddleware(BaseHTTPMiddleware):
    """Собирает гистограмму длительности запросов."""

    async def dispatch(self, request: Request, call_next: Callable):
        start = time.perf_counter()
        try:
            response = await call_next(request)
            return response
        finally:
            path = request.url.path.split("?")[0]
            HTTP_LATENCY.labels(request.method, path).observe(
                time.perf_counter() - start
            )


class CountingMiddleware(BaseHTTPMiddleware):
    """Подсчитывает количество запросов по статусам."""

    async def dispatch(self, request: Request, call_next: Callable):
        response: Response = await call_next(request)
        path = request.url.path.split("?")[0]
        HTTP_REQUESTS.labels(request.method, path, str(response.status_code)).inc()
        return response


def setup_middlewares(app):
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(CountingMiddleware)
