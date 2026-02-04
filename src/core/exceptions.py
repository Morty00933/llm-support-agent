"""Custom exception classes for standardized error handling.

This module provides custom exception classes that inherit from HTTPException
to ensure consistent error responses across the API.

Benefits:
- DRY: Avoid repeating status codes and error formats
- Consistency: All errors follow same structure
- Maintainability: Easy to update error messages in one place
- Type safety: Better IDE support and type checking
"""
from __future__ import annotations


from fastapi import HTTPException, status


# ============================================================
# BASE EXCEPTION CLASSES
# ============================================================

class APIException(HTTPException):
    """Base class for all API exceptions.

    Provides consistent error structure with optional details.
    """

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


# ============================================================
# 4XX CLIENT ERROR EXCEPTIONS
# ============================================================

class BadRequestException(APIException):
    """400 Bad Request - Client sent invalid data."""

    def __init__(self, message: str = "Bad request", headers: dict[str, str] | None = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            headers=headers,
        )


class UnauthorizedException(APIException):
    """401 Unauthorized - Authentication required or failed."""

    def __init__(
        self,
        message: str = "Authentication required",
        headers: dict[str, str] | None = None,
    ):
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers=headers,
        )


class ForbiddenException(APIException):
    """403 Forbidden - User authenticated but lacks permission."""

    def __init__(self, message: str = "Access denied", headers: dict[str, str] | None = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
            headers=headers,
        )


class NotFoundException(APIException):
    """404 Not Found - Resource does not exist."""

    def __init__(self, resource: str = "Resource", headers: dict[str, str] | None = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} not found",
            headers=headers,
        )


class ConflictException(APIException):
    """409 Conflict - Resource already exists or conflict with current state."""

    def __init__(self, message: str = "Resource conflict", headers: dict[str, str] | None = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
            headers=headers,
        )


class UnprocessableEntityException(APIException):
    """422 Unprocessable Entity - Validation error."""

    def __init__(
        self,
        message: str = "Validation error",
        headers: dict[str, str] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message,
            headers=headers,
        )


class TooManyRequestsException(APIException):
    """429 Too Many Requests - Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        headers: dict[str, str] | None = None,
    ):
        if retry_after and headers is None:
            headers = {"Retry-After": str(retry_after)}
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message,
            headers=headers,
        )


# ============================================================
# 5XX SERVER ERROR EXCEPTIONS
# ============================================================

class InternalServerErrorException(APIException):
    """500 Internal Server Error - Unexpected server error."""

    def __init__(
        self,
        message: str = "Internal server error",
        headers: dict[str, str] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
            headers=headers,
        )


class ServiceUnavailableException(APIException):
    """503 Service Unavailable - Service temporarily unavailable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        retry_after: int | None = None,
        headers: dict[str, str] | None = None,
    ):
        if retry_after and headers is None:
            headers = {"Retry-After": str(retry_after)}
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=message,
            headers=headers,
        )


# ============================================================
# DOMAIN-SPECIFIC EXCEPTIONS
# ============================================================

class TicketNotFoundException(NotFoundException):
    """Ticket not found exception."""

    def __init__(self, ticket_id: int | None = None):
        if ticket_id:
            super().__init__(f"Ticket #{ticket_id}")
        else:
            super().__init__("Ticket")


class UserNotFoundException(NotFoundException):
    """User not found exception."""

    def __init__(self, user_id: int | None = None, email: str | None = None):
        if user_id:
            super().__init__(f"User #{user_id}")
        elif email:
            super().__init__(f"User with email '{email}'")
        else:
            super().__init__("User")


class TenantNotFoundException(NotFoundException):
    """Tenant not found exception."""

    def __init__(self, tenant_id: int | None = None):
        if tenant_id:
            super().__init__(f"Tenant #{tenant_id}")
        else:
            super().__init__("Tenant")


class KBChunkNotFoundException(NotFoundException):
    """Knowledge base chunk not found exception."""

    def __init__(self, chunk_id: int | None = None):
        if chunk_id:
            super().__init__(f"KB Chunk #{chunk_id}")
        else:
            super().__init__("KB Chunk")


class EmailAlreadyExistsException(ConflictException):
    """Email already registered exception."""

    def __init__(self, email: str | None = None):
        if email:
            super().__init__(f"Email '{email}' is already registered")
        else:
            super().__init__("Email already registered")


class InvalidCredentialsException(UnauthorizedException):
    """Invalid email or password exception."""

    def __init__(self):
        super().__init__("Incorrect email or password")


class InactiveUserException(ForbiddenException):
    """User account is disabled exception."""

    def __init__(self):
        super().__init__("User account is disabled")


class PermissionDeniedException(ForbiddenException):
    """Permission denied for specific operation."""

    def __init__(self, operation: str | None = None):
        if operation:
            super().__init__(f"Permission denied: {operation}")
        else:
            super().__init__("Permission denied")


class InvalidTokenException(UnauthorizedException):
    """Invalid or expired token exception."""

    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message)


class OllamaNotAvailableException(ServiceUnavailableException):
    """Ollama service not available exception."""

    def __init__(self):
        super().__init__(
            "AI service (Ollama) is currently unavailable. Please try again later.",
            retry_after=60,
        )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Base
    "APIException",
    # 4XX
    "BadRequestException",
    "UnauthorizedException",
    "ForbiddenException",
    "NotFoundException",
    "ConflictException",
    "UnprocessableEntityException",
    "TooManyRequestsException",
    # 5XX
    "InternalServerErrorException",
    "ServiceUnavailableException",
    # Domain-specific
    "TicketNotFoundException",
    "UserNotFoundException",
    "TenantNotFoundException",
    "KBChunkNotFoundException",
    "EmailAlreadyExistsException",
    "InvalidCredentialsException",
    "InactiveUserException",
    "PermissionDeniedException",
    "InvalidTokenException",
    "OllamaNotAvailableException",
]
