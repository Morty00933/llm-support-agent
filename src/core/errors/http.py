"""RFC 7807 Problem Details для HTTP errors."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HTTPError(Exception):
    """Базовый HTTP error в формате RFC 7807."""
    
    status_code: int
    title: str
    detail: str | None = None
    type: str = "about:blank"
    instance: str | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        result = {
            "type": self.type,
            "title": self.title,
            "status": self.status_code,
        }
        if self.detail:
            result["detail"] = self.detail
        if self.instance:
            result["instance"] = self.instance
        if self.errors:
            result["errors"] = self.errors
        return result


@dataclass
class BadRequestError(HTTPError):
    status_code: int = 400
    title: str = "Bad Request"
    type: str = "https://httpstatuses.com/400"


@dataclass
class UnauthorizedError(HTTPError):
    status_code: int = 401
    title: str = "Unauthorized"
    type: str = "https://httpstatuses.com/401"


@dataclass
class ForbiddenError(HTTPError):
    status_code: int = 403
    title: str = "Forbidden"
    type: str = "https://httpstatuses.com/403"


@dataclass
class NotFoundError(HTTPError):
    status_code: int = 404
    title: str = "Not Found"
    type: str = "https://httpstatuses.com/404"


@dataclass
class ConflictError(HTTPError):
    status_code: int = 409
    title: str = "Conflict"
    type: str = "https://httpstatuses.com/409"


@dataclass
class UnprocessableEntityError(HTTPError):
    status_code: int = 422
    title: str = "Unprocessable Entity"
    type: str = "https://httpstatuses.com/422"


@dataclass
class TooManyRequestsError(HTTPError):
    status_code: int = 429
    title: str = "Too Many Requests"
    type: str = "https://httpstatuses.com/429"
    retry_after: int | None = None
    
    def __post_init__(self):
        if self.retry_after:
            self.headers["Retry-After"] = str(self.retry_after)


@dataclass
class InternalServerError(HTTPError):
    status_code: int = 500
    title: str = "Internal Server Error"
    type: str = "https://httpstatuses.com/500"


@dataclass
class ServiceUnavailableError(HTTPError):
    status_code: int = 503
    title: str = "Service Unavailable"
    type: str = "https://httpstatuses.com/503"
