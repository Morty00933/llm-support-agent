"""
Tests for HTTP errors module
"""
import pytest
from src.core.errors.http import (
    HTTPError,
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    UnprocessableEntityError,
    TooManyRequestsError,
    InternalServerError,
    ServiceUnavailableError,
)


class TestHTTPError:
    """Tests for base HTTPError"""

    def test_http_error_basic(self):
        """Test basic HTTP error creation"""
        error = HTTPError(
            status_code=400,
            title="Test Error",
            detail="Test detail",
        )
        assert error.status_code == 400
        assert error.title == "Test Error"
        assert error.detail == "Test detail"

    def test_http_error_to_dict(self):
        """Test converting HTTP error to dict"""
        error = HTTPError(
            status_code=400,
            title="Test Error",
            detail="Test detail",
        )
        result = error.to_dict()
        assert result["status"] == 400
        assert result["title"] == "Test Error"
        assert result["detail"] == "Test detail"
        assert "type" in result

    def test_http_error_with_errors(self):
        """Test HTTP error with errors list"""
        error = HTTPError(
            status_code=400,
            title="Validation Error",
            errors=[{"field": "email", "message": "Invalid"}],
        )
        result = error.to_dict()
        assert "errors" in result
        assert len(result["errors"]) == 1


class TestBadRequestError:
    """Tests for BadRequestError"""

    def test_bad_request_default(self):
        """Test default BadRequestError"""
        error = BadRequestError(detail="Invalid input")
        assert error.status_code == 400
        assert error.title == "Bad Request"
        assert error.detail == "Invalid input"


class TestUnauthorizedError:
    """Tests for UnauthorizedError"""

    def test_unauthorized_default(self):
        """Test default UnauthorizedError"""
        error = UnauthorizedError(detail="Missing credentials")
        assert error.status_code == 401
        assert error.title == "Unauthorized"


class TestForbiddenError:
    """Tests for ForbiddenError"""

    def test_forbidden_default(self):
        """Test default ForbiddenError"""
        error = ForbiddenError(detail="Access denied")
        assert error.status_code == 403
        assert error.title == "Forbidden"


class TestNotFoundError:
    """Tests for NotFoundError"""

    def test_not_found_default(self):
        """Test default NotFoundError"""
        error = NotFoundError(detail="Resource not found")
        assert error.status_code == 404
        assert error.title == "Not Found"


class TestConflictError:
    """Tests for ConflictError"""

    def test_conflict_default(self):
        """Test default ConflictError"""
        error = ConflictError(detail="Resource already exists")
        assert error.status_code == 409
        assert error.title == "Conflict"


class TestUnprocessableEntityError:
    """Tests for UnprocessableEntityError"""

    def test_unprocessable_entity_default(self):
        """Test default UnprocessableEntityError"""
        error = UnprocessableEntityError(detail="Validation failed")
        assert error.status_code == 422
        assert error.title == "Unprocessable Entity"


class TestTooManyRequestsError:
    """Tests for TooManyRequestsError"""

    def test_too_many_requests_default(self):
        """Test default TooManyRequestsError"""
        error = TooManyRequestsError(detail="Rate limit exceeded")
        assert error.status_code == 429
        assert error.title == "Too Many Requests"

    def test_too_many_requests_with_retry_after(self):
        """Test TooManyRequestsError with retry_after"""
        error = TooManyRequestsError(
            detail="Rate limit exceeded",
            retry_after=60,
        )
        assert error.retry_after == 60
        assert "Retry-After" in error.headers
        assert error.headers["Retry-After"] == "60"


class TestInternalServerError:
    """Tests for InternalServerError"""

    def test_internal_server_error_default(self):
        """Test default InternalServerError"""
        error = InternalServerError(detail="Something went wrong")
        assert error.status_code == 500
        assert error.title == "Internal Server Error"


class TestServiceUnavailableError:
    """Tests for ServiceUnavailableError"""

    def test_service_unavailable_default(self):
        """Test default ServiceUnavailableError"""
        error = ServiceUnavailableError(detail="Service is down")
        assert error.status_code == 503
        assert error.title == "Service Unavailable"
