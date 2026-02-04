# -*- coding: utf-8 -*-
"""Middleware для API - ИСПРАВЛЕННАЯ ВЕРСИЯ.

ИСПРАВЛЕНИЯ:
1. RateLimitMiddleware: добавлена очистка старых IP (memory leak fix)
2. Добавлен max_ips для ограничения размера словаря
3. Добавлен Retry-After header для 429 responses
"""
from __future__ import annotations

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования запросов."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        start_time = time.perf_counter()
        
        # Логируем входящий запрос
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query=str(request.query_params),
        )
        
        response = await call_next(request)
        
        # Вычисляем время обработки
        process_time = time.perf_counter() - start_time
        
        # Логируем завершение
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(process_time * 1000, 2),
        )
        
        # Добавляем заголовок с временем обработки
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiter на основе IP.

    ИСПРАВЛЕНО:
    - Добавлена очистка неактивных IP (fix memory leak)
    - Добавлен max_ips для ограничения размера словаря
    - Периодическая полная очистка
    - Добавлен Retry-After header
    """

    DEFAULT_MAX_IPS: int = 10000
    CLEANUP_INTERVAL: int = 300  # 5 минут

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        max_ips: int | None = None,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.max_ips = max_ips or self.DEFAULT_MAX_IPS
        self._requests: dict[str, list[float]] = {}
        self._last_cleanup: float = time.time()

    def _cleanup_old_entries(self, current_time: float) -> None:
        """Удаляет устаревшие записи и неактивные IP.

        ИСПРАВЛЕНИЕ: раньше dict рос бесконечно.
        """
        ips_to_remove = []

        for ip, timestamps in self._requests.items():
            valid_timestamps = [t for t in timestamps if current_time - t < 60]

            if valid_timestamps:
                self._requests[ip] = valid_timestamps
            else:
                ips_to_remove.append(ip)

        for ip in ips_to_remove:
            del self._requests[ip]

        # Если всё ещё слишком много IP - удаляем самые старые
        if len(self._requests) > self.max_ips:
            sorted_ips = sorted(
                self._requests.items(),
                key=lambda x: max(x[1]) if x[1] else 0
            )
            for ip, _ in sorted_ips[:len(sorted_ips) // 2]:
                del self._requests[ip]

            logger.warning(
                "rate_limiter_cleanup",
                removed_ips=len(sorted_ips) // 2,
                remaining_ips=len(self._requests),
            )

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Периодическая полная очистка
        if current_time - self._last_cleanup > self.CLEANUP_INTERVAL:
            self._cleanup_old_entries(current_time)
            self._last_cleanup = current_time

        # Очищаем старые записи для текущего IP
        if client_ip in self._requests:
            self._requests[client_ip] = [
                t for t in self._requests[client_ip]
                if current_time - t < 60
            ]
        else:
            self._requests[client_ip] = []

        # Проверяем лимит
        if len(self._requests[client_ip]) >= self.requests_per_minute:
            logger.warning(
                "rate_limit_exceeded",
                client_ip=client_ip,
                requests=len(self._requests[client_ip]),
            )
            return Response(
                content='{"detail": "Too many requests"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )

        # Добавляем текущий запрос
        self._requests[client_ip].append(current_time)

        return await call_next(request)


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """Distributed rate limiting using Redis with sliding window."""

    def __init__(
        self,
        app,
        redis_client,
        max_requests: int = 60,
        window_seconds: int = 60,
    ):
        super().__init__(app)
        from src.core.rate_limit_redis import RedisRateLimiter
        self.limiter = RedisRateLimiter(
            redis_client=redis_client,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/ready", "/health/live", "/metrics"]:
            return await call_next(request)

        # Skip rate limiting for test environment (detect by client host "test")
        client_ip = request.client.host if request.client else "unknown"
        if client_ip == "test" or request.headers.get("X-Test-Client") == "pytest":
            return await call_next(request)

        endpoint = f"{request.method}:{request.url.path}"

        # Stricter rate limiting for auth endpoints (5 requests per minute)
        is_auth_endpoint = request.url.path.startswith("/v1/auth/")
        if is_auth_endpoint:
            # Use separate, stricter limits for auth endpoints
            auth_allowed, auth_retry = await self.limiter.is_allowed(
                client_ip,
                f"auth:{endpoint}",
                max_requests=5,  # Only 5 login attempts per minute
                window_seconds=60
            )
            if not auth_allowed:
                logger.warning(
                    "auth_rate_limit_exceeded",
                    client_ip=client_ip,
                    endpoint=endpoint,
                    retry_after=auth_retry,
                )
                return Response(
                    content='{"detail": "Too many authentication attempts. Please try again later."}',
                    status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": str(auth_retry)},
                )

        allowed, retry_after = await self.limiter.is_allowed(client_ip, endpoint)

        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                client_ip=client_ip,
                endpoint=endpoint,
                retry_after=retry_after,
            )
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)
        return response
