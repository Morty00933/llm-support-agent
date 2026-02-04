# -*- coding: utf-8 -*-
"""Exception handlers for FastAPI - FIXED VERSION.

Централизованная обработка всех исключений.
"""
from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.domain.exceptions import DomainError

logger = logging.getLogger(__name__)

# Correlation ID for request tracing
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Get current correlation ID."""
    cid = _correlation_id.get()
    if not cid:
        cid = str(uuid.uuid4())[:8]
        _correlation_id.set(cid)
    return cid


def set_correlation_id(cid: str) -> None:
    """Set correlation ID."""
    _correlation_id.set(cid)


# ============================================================
# EXCEPTION HANDLERS
# ============================================================

async def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Handle domain exceptions."""
    status_code = 400
    
    # Map error codes to status codes
    code_mapping = {
        "ENTITY_NOT_FOUND": 404,
        "ENTITY_ALREADY_EXISTS": 409,
        "VALIDATION_ERROR": 422,
        "AUTHENTICATION_ERROR": 401,
        "INVALID_CREDENTIALS": 401,
        "TENANT_MISMATCH": 403,
        "INVALID_STATE_TRANSITION": 400,
    }
    
    status_code = code_mapping.get(exc.code, 400)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "type": f"https://errors.llm-agent.local/{exc.code.lower()}",
            "title": exc.code.replace("_", " ").title(),
            "status": status_code,
            "detail": exc.message,
            "instance": str(request.url.path),
            "correlation_id": get_correlation_id(),
            **exc.details,
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://httpstatuses.com/{exc.status_code}",
            "title": exc.detail if isinstance(exc.detail, str) else "Error",
            "status": exc.status_code,
            "instance": str(request.url.path),
            "correlation_id": get_correlation_id(),
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "type": "https://httpstatuses.com/422",
            "title": "Validation Error",
            "status": 422,
            "detail": "Request validation failed",
            "instance": str(request.url.path),
            "correlation_id": get_correlation_id(),
            "errors": errors,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    logger.exception(
        "unhandled_exception",
        extra={
            "error": str(exc),
            "path": str(request.url.path),
            "correlation_id": get_correlation_id(),
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "type": "https://httpstatuses.com/500",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred",
            "instance": str(request.url.path),
            "correlation_id": get_correlation_id(),
        },
    )


# ============================================================
# SETUP
# ============================================================

def setup_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers."""
    app.add_exception_handler(DomainError, domain_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)


__all__ = [
    "setup_exception_handlers",
    "get_correlation_id",
    "set_correlation_id",
]
