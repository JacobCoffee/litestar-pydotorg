"""Unit tests for core exception handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

from litestar.exceptions import (
    HTTPException,
    InternalServerException,
    NotFoundException,
    PermissionDeniedException,
)
from litestar.response import Response, Template
from litestar.status_codes import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from pydotorg.core.exceptions import (
    _create_json_error_response,
    _is_api_request,
    _is_htmx_request,
    http_exception_handler,
    internal_server_error_handler,
    not_found_exception_handler,
    permission_denied_handler,
)

if TYPE_CHECKING:
    pass


class TestIsApiRequest:
    """Tests for _is_api_request helper."""

    def test_api_path_prefix(self) -> None:
        """Test API request detection by /api/ path prefix."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/users"
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="text/html")

        assert _is_api_request(mock_request) is True

    def test_accept_header_json(self) -> None:
        """Test API request detection by Accept: application/json header."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/some/page"
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="application/json")

        assert _is_api_request(mock_request) is True

    def test_browser_request(self) -> None:
        """Test non-API browser request detection."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/about"
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="text/html")

        assert _is_api_request(mock_request) is False


class TestIsHtmxRequest:
    """Tests for _is_htmx_request helper."""

    def test_htmx_request_true(self) -> None:
        """Test HTMX request detection when HX-Request header is present."""
        mock_request = Mock(spec=["headers"])
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="true")

        assert _is_htmx_request(mock_request) is True

    def test_htmx_request_false(self) -> None:
        """Test HTMX request detection when header is absent."""
        mock_request = Mock(spec=["headers"])
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value=None)

        assert _is_htmx_request(mock_request) is False


class TestCreateJsonErrorResponse:
    """Tests for _create_json_error_response helper."""

    def test_basic_response(self) -> None:
        """Test basic JSON error response structure."""
        response = _create_json_error_response(
            detail="Resource not found",
            status_code=HTTP_404_NOT_FOUND,
        )

        assert isinstance(response, Response)
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.media_type == "application/json"

    def test_response_with_extra(self) -> None:
        """Test JSON error response with extra details."""
        extra = {"field": "email", "error": "invalid format"}
        response = _create_json_error_response(
            detail="Validation error",
            status_code=HTTP_400_BAD_REQUEST,
            extra=extra,
        )

        assert isinstance(response, Response)
        assert response.status_code == HTTP_400_BAD_REQUEST


class TestNotFoundExceptionHandler:
    """Tests for not_found_exception_handler."""

    def test_api_request_returns_json(self) -> None:
        """Test that API requests get JSON response."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/users/123"
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="application/json")

        exc = NotFoundException(detail="User not found")

        response = not_found_exception_handler(mock_request, exc)

        assert isinstance(response, Response)
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.media_type == "application/json"

    def test_htmx_request_returns_toast(self) -> None:
        """Test that HTMX requests get toast response."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/about"
        mock_request.headers = Mock()

        def header_get(key: str, default: str = "") -> str:
            if key == "HX-Request":
                return "true"
            return default

        mock_request.headers.get = Mock(side_effect=header_get)

        exc = NotFoundException(detail="Page not found")

        response = not_found_exception_handler(mock_request, exc)

        assert isinstance(response, Response)
        assert response.status_code == HTTP_404_NOT_FOUND
        assert "HX-Trigger" in response.headers

    def test_browser_request_returns_template(self) -> None:
        """Test that browser requests get HTML template."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/about"
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="text/html")

        exc = NotFoundException(detail="Page not found")

        response = not_found_exception_handler(mock_request, exc)

        assert isinstance(response, Template)
        assert response.status_code == HTTP_404_NOT_FOUND


class TestHttpExceptionHandler:
    """Tests for http_exception_handler."""

    def test_api_request_returns_json(self) -> None:
        """Test that API requests get JSON response for generic HTTP errors."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/pages"
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="application/json")

        exc = HTTPException(detail="Validation failed", status_code=HTTP_400_BAD_REQUEST)

        response = http_exception_handler(mock_request, exc)

        assert isinstance(response, Response)
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response.media_type == "application/json"

    def test_api_request_includes_extra(self) -> None:
        """Test that API responses include extra error details."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/pages"
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="application/json")

        exc = HTTPException(detail="Validation failed", status_code=HTTP_400_BAD_REQUEST)
        exc.extra = [{"key": "limit_offset", "source": "query"}]

        response = http_exception_handler(mock_request, exc)

        assert isinstance(response, Response)
        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_htmx_request_returns_toast(self) -> None:
        """Test that HTMX requests get toast response."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/dashboard"
        mock_request.headers = Mock()

        def header_get(key: str, default: str = "") -> str:
            if key == "HX-Request":
                return "true"
            return default

        mock_request.headers.get = Mock(side_effect=header_get)

        exc = HTTPException(detail="Something went wrong", status_code=HTTP_400_BAD_REQUEST)

        response = http_exception_handler(mock_request, exc)

        assert isinstance(response, Response)
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert "HX-Trigger" in response.headers

    def test_browser_request_returns_template(self) -> None:
        """Test that browser requests get HTML template."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/dashboard"
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="text/html")

        exc = HTTPException(detail="Something went wrong", status_code=HTTP_400_BAD_REQUEST)

        response = http_exception_handler(mock_request, exc)

        assert isinstance(response, Template)
        assert response.status_code == HTTP_400_BAD_REQUEST


class TestPermissionDeniedHandler:
    """Tests for permission_denied_handler."""

    def test_api_request_returns_json(self) -> None:
        """Test that API requests get JSON response for 403."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/admin/users"
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="application/json")

        exc = PermissionDeniedException(detail="Admin access required")

        response = permission_denied_handler(mock_request, exc)

        assert isinstance(response, Response)
        assert response.status_code == HTTP_403_FORBIDDEN
        assert response.media_type == "application/json"

    def test_htmx_request_returns_toast(self) -> None:
        """Test that HTMX requests get toast response."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/admin"
        mock_request.headers = Mock()

        def header_get(key: str, default: str = "") -> str:
            if key == "HX-Request":
                return "true"
            return default

        mock_request.headers.get = Mock(side_effect=header_get)

        exc = PermissionDeniedException(detail="Admin access required")

        response = permission_denied_handler(mock_request, exc)

        assert isinstance(response, Response)
        assert response.status_code == HTTP_403_FORBIDDEN
        assert "HX-Trigger" in response.headers

    def test_browser_request_returns_template(self) -> None:
        """Test that browser requests get 403 template."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/admin"
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="text/html")

        exc = PermissionDeniedException(detail="Admin access required")

        response = permission_denied_handler(mock_request, exc)

        assert isinstance(response, Template)
        assert response.status_code == HTTP_403_FORBIDDEN


class TestInternalServerErrorHandler:
    """Tests for internal_server_error_handler."""

    def test_api_request_returns_json(self) -> None:
        """Test that API requests get JSON response for 500."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/data"
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="application/json")

        exc = InternalServerException(detail="Database error")

        response = internal_server_error_handler(mock_request, exc)

        assert isinstance(response, Response)
        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        assert response.media_type == "application/json"

    def test_htmx_request_returns_toast(self) -> None:
        """Test that HTMX requests get toast response."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/dashboard"
        mock_request.headers = Mock()

        def header_get(key: str, default: str = "") -> str:
            if key == "HX-Request":
                return "true"
            return default

        mock_request.headers.get = Mock(side_effect=header_get)

        exc = InternalServerException(detail="Database error")

        response = internal_server_error_handler(mock_request, exc)

        assert isinstance(response, Response)
        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        assert "HX-Trigger" in response.headers

    def test_browser_request_returns_template(self) -> None:
        """Test that browser requests get 500 template."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/dashboard"
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="text/html")

        exc = InternalServerException(detail="Database error")

        response = internal_server_error_handler(mock_request, exc)

        assert isinstance(response, Template)
        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
