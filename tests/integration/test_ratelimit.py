"""Integration tests for API rate limiting.

These tests verify that rate limiting works correctly in the full application
context with MemoryStore as the backend store. Tests cover:
- Rate limit enforcement (429 after limit exceeded)
- Rate limit headers in responses
- Rate limit exclusions (health, static)
- HTMX-aware 429 responses
- API-aware 429 responses
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from litestar import Litestar, Request, get
from litestar.exceptions import TooManyRequestsException
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.response import Response
from litestar.status_codes import HTTP_429_TOO_MANY_REQUESTS
from litestar.stores.memory import MemoryStore
from litestar.testing import AsyncTestClient

from pydotorg.core.ratelimit import create_rate_limit_config
from pydotorg.core.ratelimit.identifier import get_rate_limit_identifier

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

pytestmark = [pytest.mark.integration, pytest.mark.slow]


@get("/test-endpoint", exclude_from_auth=True, sync_to_thread=False)
def _rate_test_endpoint() -> dict:
    """Simple test endpoint for rate limiting."""
    return {"status": "ok"}


@get("/api/v1/test", exclude_from_auth=True, sync_to_thread=False)
def _rate_api_test_endpoint() -> dict:
    """API test endpoint for rate limiting."""
    return {"data": "test"}


@get("/health", exclude_from_auth=True, sync_to_thread=False)
def _rate_health_endpoint() -> dict:
    """Health check endpoint (should be excluded from rate limiting)."""
    return {"status": "healthy"}


def _test_rate_limit_exception_handler(
    request: Request,
    exc: TooManyRequestsException,
) -> Response:
    """Simple 429 handler for integration tests that returns JSON.

    This avoids the need for template engine configuration in tests.
    """
    retry_after = "60"
    if hasattr(exc, "headers") and exc.headers and "retry-after" in exc.headers:
        retry_after = str(exc.headers["retry-after"])

    is_htmx = request.headers.get("HX-Request") == "true"
    is_api = request.url.path.startswith("/api/") or "application/json" in request.headers.get("Accept", "")

    if is_htmx:
        toast_event = json.dumps(
            {
                "showToast": {
                    "message": "Too many requests. Please slow down.",
                    "type": "warning",
                }
            }
        )
        return Response(
            content=None,
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            headers={
                "HX-Trigger": toast_event,
                "HX-Reswap": "none",
                "Retry-After": retry_after,
            },
        )

    if is_api:
        return Response(
            content={
                "error": "Too Many Requests",
                "detail": "Rate limit exceeded",
                "retry_after": retry_after,
                "status_code": HTTP_429_TOO_MANY_REQUESTS,
            },
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": retry_after},
        )

    return Response(
        content={"error": "Too Many Requests", "retry_after": retry_after},
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        headers={"Retry-After": retry_after},
    )


@pytest.fixture
async def rate_limited_client() -> AsyncIterator[AsyncTestClient]:
    """Create a test client with rate limiting configured.

    Uses MemoryStore for testing to avoid Redis dependency.
    Configured with very low limits (3 requests/minute) for testing.
    """
    rate_limit_config = RateLimitConfig(
        rate_limit=("minute", 3),
        store="rate_limit",
        exclude=["/health", "/static/*"],
    )

    test_app = Litestar(
        route_handlers=[_rate_test_endpoint, _rate_api_test_endpoint, _rate_health_endpoint],
        middleware=[rate_limit_config.middleware],
        stores={"rate_limit": MemoryStore()},
        exception_handlers={TooManyRequestsException: _test_rate_limit_exception_handler},
        debug=True,
    )

    async with AsyncTestClient(
        app=test_app,
        base_url="http://testserver.local",
    ) as client:
        yield client


@pytest.mark.asyncio
class TestRateLimitEnforcement:
    """Test that rate limits are enforced correctly."""

    async def test_requests_under_limit_succeed(self, rate_limited_client: AsyncTestClient) -> None:
        """Test that requests under the rate limit succeed."""
        for _ in range(3):
            response = await rate_limited_client.get("/test-endpoint")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

    async def test_requests_over_limit_return_429(self, rate_limited_client: AsyncTestClient) -> None:
        """Test that requests over the rate limit return 429."""
        for _ in range(3):
            response = await rate_limited_client.get("/test-endpoint")
            assert response.status_code == 200

        response = await rate_limited_client.get("/test-endpoint")
        assert response.status_code == 429

    async def test_rate_limit_shared_across_requests(self, rate_limited_client: AsyncTestClient) -> None:
        """Test that rate limits are enforced per client connection.

        Note: Without a custom key function, Litestar's default rate limiter
        uses the client connection info, not X-Forwarded-For headers.
        """
        for _ in range(3):
            response = await rate_limited_client.get("/test-endpoint")
            assert response.status_code == 200

        response = await rate_limited_client.get("/test-endpoint")
        assert response.status_code == 429


@pytest.mark.asyncio
class TestRateLimitHeaders:
    """Test that rate limit headers are included in responses."""

    async def test_rate_limit_headers_present(self, rate_limited_client: AsyncTestClient) -> None:
        """Test that rate limit headers are present in responses."""
        response = await rate_limited_client.get("/test-endpoint")
        assert response.status_code == 200

        assert "x-ratelimit-limit" in response.headers or "ratelimit-limit" in response.headers

    async def test_rate_limit_remaining_decreases(self, rate_limited_client: AsyncTestClient) -> None:
        """Test that rate limit remaining decreases with each request."""
        response1 = await rate_limited_client.get("/test-endpoint")
        remaining1_key = (
            "x-ratelimit-remaining" if "x-ratelimit-remaining" in response1.headers else "ratelimit-remaining"
        )
        remaining1 = int(response1.headers.get(remaining1_key, response1.headers.get("ratelimit-remaining", "0")))

        response2 = await rate_limited_client.get("/test-endpoint")
        remaining2_key = (
            "x-ratelimit-remaining" if "x-ratelimit-remaining" in response2.headers else "ratelimit-remaining"
        )
        remaining2 = int(response2.headers.get(remaining2_key, response2.headers.get("ratelimit-remaining", "0")))

        assert remaining2 < remaining1

    async def test_429_response_has_retry_after(self, rate_limited_client: AsyncTestClient) -> None:
        """Test that 429 responses include Retry-After header."""
        for _ in range(3):
            await rate_limited_client.get("/test-endpoint")

        response = await rate_limited_client.get("/test-endpoint")
        assert response.status_code == 429
        assert "retry-after" in response.headers


@pytest.mark.asyncio
class TestRateLimitExclusions:
    """Test that certain endpoints are excluded from rate limiting."""

    async def test_health_endpoint_excluded(self, rate_limited_client: AsyncTestClient) -> None:
        """Test that health endpoint is excluded from rate limiting."""
        for _ in range(10):
            response = await rate_limited_client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}

    async def test_non_excluded_endpoint_rate_limited(self, rate_limited_client: AsyncTestClient) -> None:
        """Test that non-excluded endpoints are still rate limited."""
        for _ in range(10):
            await rate_limited_client.get("/health")

        for _ in range(3):
            response = await rate_limited_client.get("/test-endpoint")
            assert response.status_code == 200

        response = await rate_limited_client.get("/test-endpoint")
        assert response.status_code == 429


@pytest.mark.asyncio
class TestRateLimitResponseFormats:
    """Test that 429 responses are formatted correctly for different request types."""

    async def test_htmx_request_returns_toast(self, rate_limited_client: AsyncTestClient) -> None:
        """Test that HTMX requests get toast notification response."""
        for _ in range(3):
            await rate_limited_client.get("/test-endpoint")

        response = await rate_limited_client.get(
            "/test-endpoint",
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 429
        assert "HX-Trigger" in response.headers
        assert "showToast" in response.headers["HX-Trigger"]
        assert "HX-Reswap" in response.headers
        assert response.headers["HX-Reswap"] == "none"

    async def test_api_request_returns_json(self, rate_limited_client: AsyncTestClient) -> None:
        """Test that API requests get JSON error response."""
        for _ in range(3):
            await rate_limited_client.get("/test-endpoint")

        response = await rate_limited_client.get(
            "/api/v1/test",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 429
        data = response.json()
        assert "error" in data
        assert data["error"] == "Too Many Requests"
        assert "retry_after" in data

    async def test_browser_request_returns_json_fallback(self, rate_limited_client: AsyncTestClient) -> None:
        """Test that browser requests get JSON fallback (no template in test)."""
        for _ in range(3):
            await rate_limited_client.get("/test-endpoint")

        response = await rate_limited_client.get(
            "/test-endpoint",
            headers={"Accept": "text/html"},
        )
        assert response.status_code == 429
        data = response.json()
        assert "error" in data
        assert "retry_after" in data


@pytest.mark.asyncio
class TestRateLimitIdentifier:
    """Test the rate limit identifier function."""

    async def test_identifier_anonymous_user(self) -> None:
        """Test identifier for anonymous users."""
        mock_request = MagicMock()
        mock_request.scope = {"user": None, "client": ("192.168.1.100", 12345)}
        mock_request.headers = {}

        identifier = await get_rate_limit_identifier(mock_request)
        assert identifier == "anon:192.168.1.100"

    async def test_identifier_authenticated_user(self) -> None:
        """Test identifier for authenticated users."""
        mock_user = MagicMock()
        mock_user.id = "user-uuid-123"
        mock_user.is_staff = False
        mock_user.is_superuser = False

        mock_request = MagicMock()
        mock_request.scope = {"user": mock_user}
        mock_request.headers = {}

        identifier = await get_rate_limit_identifier(mock_request)
        assert identifier == "user:user-uuid-123"

    async def test_identifier_staff_user(self) -> None:
        """Test identifier for staff users."""
        mock_user = MagicMock()
        mock_user.id = "staff-uuid-456"
        mock_user.is_staff = True
        mock_user.is_superuser = False

        mock_request = MagicMock()
        mock_request.scope = {"user": mock_user}
        mock_request.headers = {}

        identifier = await get_rate_limit_identifier(mock_request)
        assert identifier == "admin:staff-uuid-456"

    async def test_identifier_superuser(self) -> None:
        """Test identifier for superusers."""
        mock_user = MagicMock()
        mock_user.id = "super-uuid-789"
        mock_user.is_staff = False
        mock_user.is_superuser = True

        mock_request = MagicMock()
        mock_request.scope = {"user": mock_user}
        mock_request.headers = {}

        identifier = await get_rate_limit_identifier(mock_request)
        assert identifier == "admin:super-uuid-789"

    async def test_identifier_x_forwarded_for(self) -> None:
        """Test identifier uses X-Forwarded-For header."""
        mock_request = MagicMock()
        mock_request.scope = {"user": None, "client": ("10.0.0.1", 12345)}
        mock_request.headers = {"X-Forwarded-For": "203.0.113.195, 70.41.3.18"}

        identifier = await get_rate_limit_identifier(mock_request)
        assert identifier == "anon:203.0.113.195"

    async def test_identifier_missing_client(self) -> None:
        """Test identifier handles missing client info."""
        mock_request = MagicMock()
        mock_request.scope = {"user": None, "client": None}
        mock_request.headers = {}

        identifier = await get_rate_limit_identifier(mock_request)
        assert identifier == "anon:unknown"


@pytest.mark.asyncio
class TestRateLimitConfig:
    """Test rate limit configuration integration."""

    async def test_create_rate_limit_config_integration(self) -> None:
        """Test that rate limit config is created correctly."""
        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"

        config = create_rate_limit_config(mock_settings)

        assert config.rate_limit == ("minute", 100)
        assert config.store == "rate_limit"
        assert "/health" in config.exclude
        assert "/static/*" in config.exclude

    async def test_rate_limit_config_middleware_property(self) -> None:
        """Test that rate limit config has middleware property."""
        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"

        config = create_rate_limit_config(mock_settings)

        assert hasattr(config, "middleware")
        assert config.middleware is not None


@pytest.mark.asyncio
class TestRateLimitConcurrency:
    """Test rate limiting under concurrent requests."""

    async def test_concurrent_requests_respect_limit(self, rate_limited_client: AsyncTestClient) -> None:
        """Test that concurrent requests are still rate limited correctly."""

        async def make_request() -> int:
            response = await rate_limited_client.get("/test-endpoint")
            return response.status_code

        results = await asyncio.gather(*[make_request() for _ in range(5)])

        success_count = sum(1 for r in results if r == 200)
        rate_limited_count = sum(1 for r in results if r == 429)

        assert success_count == 3
        assert rate_limited_count == 2
