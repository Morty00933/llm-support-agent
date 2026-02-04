"""Correlation ID middleware для трейсинга запросов."""
from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable для хранения correlation ID
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)

CORRELATION_ID_HEADER = "X-Correlation-ID"


def get_correlation_id() -> str | None:
    """Получение текущего correlation ID."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Установка correlation ID."""
    correlation_id_var.set(correlation_id)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления correlation ID к каждому запросу."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Получаем correlation ID из заголовка или генерируем новый
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Устанавливаем в context variable
        set_correlation_id(correlation_id)
        
        # Выполняем запрос
        response = await call_next(request)
        
        # Добавляем заголовок в ответ
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        
        return response
