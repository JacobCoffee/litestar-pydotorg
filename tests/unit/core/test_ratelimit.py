"""Rate limiting module unit tests."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from litestar.exceptions import TooManyRequestsException
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.response import Response, Template
from litestar.status_codes import HTTP_429_TOO_MANY_REQUESTS

from pydotorg.core.ratelimit.config import RateLimitConfig as CustomRateLimitConfig
from pydotorg.core.ratelimit.config import RateLimitTier, get_ratelimit_config
from pydotorg.core.ratelimit.exceptions import (
    _create_toast_response,
    _extract_retry_after,
    _is_api_request,
    _is_htmx_request,
    rate_limit_exception_handler,
)
from pydotorg.core.ratelimit.identifier import _get_client_ip, get_rate_limit_identifier
from pydotorg.core.ratelimit.middleware import create_rate_limit_config, create_response_cache_config

if TYPE_CHECKING:
    pass


class TestRateLimitConfig:
    """Tests for RateLimitConfig class."""

    def test_default_values(self) -> None:
        """Test default rate limit values for all tiers."""
        config = CustomRateLimitConfig()

        assert config.critical_limit == 5
        assert config.high_limit == 20
        assert config.medium_limit == 60
        assert config.low_limit == 120
        assert config.authenticated_multiplier == 4.0
        assert config.staff_multiplier == 5.0
        assert config.enabled is True
        assert config.redis_key_prefix == "ratelimit:"
        assert config.window_seconds == 60

    def test_get_limit_anonymous_critical(self) -> None:
        """Test anonymous user limit for CRITICAL tier."""
        config = CustomRateLimitConfig()
        limit = config.get_limit(RateLimitTier.CRITICAL)
        assert limit == 5

    def test_get_limit_anonymous_high(self) -> None:
        """Test anonymous user limit for HIGH tier."""
        config = CustomRateLimitConfig()
        limit = config.get_limit(RateLimitTier.HIGH)
        assert limit == 20

    def test_get_limit_anonymous_medium(self) -> None:
        """Test anonymous user limit for MEDIUM tier."""
        config = CustomRateLimitConfig()
        limit = config.get_limit(RateLimitTier.MEDIUM)
        assert limit == 60

    def test_get_limit_anonymous_low(self) -> None:
        """Test anonymous user limit for LOW tier."""
        config = CustomRateLimitConfig()
        limit = config.get_limit(RateLimitTier.LOW)
        assert limit == 120

    def test_get_limit_authenticated_multiplier(self) -> None:
        """Test authenticated user gets 4x multiplier."""
        config = CustomRateLimitConfig()
        limit = config.get_limit(RateLimitTier.CRITICAL, is_authenticated=True)
        assert limit == 20

    def test_get_limit_staff_multiplier(self) -> None:
        """Test staff user gets 5x multiplier on top of authenticated."""
        config = CustomRateLimitConfig()
        limit = config.get_limit(RateLimitTier.CRITICAL, is_authenticated=True, is_staff=True)
        assert limit == 100

    def test_get_limit_staff_without_authenticated(self) -> None:
        """Test staff multiplier alone without authenticated flag."""
        config = CustomRateLimitConfig()
        limit = config.get_limit(RateLimitTier.CRITICAL, is_staff=True)
        assert limit == 25

    def test_get_tier_limits_structure(self) -> None:
        """Test get_tier_limits returns correct structure for all tiers."""
        config = CustomRateLimitConfig()
        limits = config.get_tier_limits()

        assert "critical" in limits
        assert "high" in limits
        assert "medium" in limits
        assert "low" in limits

        for tier_limits in limits.values():
            assert "anonymous" in tier_limits
            assert "authenticated" in tier_limits
            assert "staff" in tier_limits

    def test_get_tier_limits_values(self) -> None:
        """Test get_tier_limits returns correct calculated values."""
        config = CustomRateLimitConfig()
        limits = config.get_tier_limits()

        assert limits["critical"]["anonymous"] == 5
        assert limits["critical"]["authenticated"] == 20
        assert limits["critical"]["staff"] == 100

        assert limits["low"]["anonymous"] == 120
        assert limits["low"]["authenticated"] == 480
        assert limits["low"]["staff"] == 2400

    def test_environment_variable_override(self) -> None:
        """Test configuration can be overridden with environment variables."""
        with patch.dict("os.environ", {"RATELIMIT_CRITICAL_LIMIT": "10", "RATELIMIT_AUTHENTICATED_MULTIPLIER": "2.0"}):
            config = CustomRateLimitConfig()
            assert config.critical_limit == 10
            assert config.authenticated_multiplier == 2.0

    def test_custom_multipliers(self) -> None:
        """Test custom multiplier values."""
        config = CustomRateLimitConfig(
            critical_limit=10,
            authenticated_multiplier=3.0,
            staff_multiplier=2.0,
        )

        anon_limit = config.get_limit(RateLimitTier.CRITICAL)
        auth_limit = config.get_limit(RateLimitTier.CRITICAL, is_authenticated=True)
        staff_limit = config.get_limit(RateLimitTier.CRITICAL, is_authenticated=True, is_staff=True)

        assert anon_limit == 10
        assert auth_limit == 30
        assert staff_limit == 60

    def test_get_ratelimit_config_cached(self) -> None:
        """Test get_ratelimit_config returns cached instance."""
        config1 = get_ratelimit_config()
        config2 = get_ratelimit_config()
        assert config1 is config2


class TestGetRateLimitIdentifier:
    """Tests for get_rate_limit_identifier function."""

    @pytest.mark.asyncio
    async def test_anonymous_user_returns_ip(self) -> None:
        """Test anonymous user returns anon:{ip} format."""
        mock_request = Mock(spec=["scope"])
        mock_request.scope = {"user": None, "client": ("192.168.1.1", 8000)}
        mock_request.headers = {}

        identifier = await get_rate_limit_identifier(mock_request)
        assert identifier == "anon:192.168.1.1"

    @pytest.mark.asyncio
    async def test_authenticated_user_returns_user_id(self) -> None:
        """Test authenticated regular user returns user:{id} format."""
        user_id = uuid4()
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.is_staff = False
        mock_user.is_superuser = False

        mock_request = Mock(spec=["scope"])
        mock_request.scope = {"user": mock_user}

        identifier = await get_rate_limit_identifier(mock_request)
        assert identifier == f"user:{user_id}"

    @pytest.mark.asyncio
    async def test_staff_user_returns_admin_id(self) -> None:
        """Test staff user returns admin:{id} format."""
        user_id = uuid4()
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.is_staff = True
        mock_user.is_superuser = False

        mock_request = Mock(spec=["scope"])
        mock_request.scope = {"user": mock_user}

        identifier = await get_rate_limit_identifier(mock_request)
        assert identifier == f"admin:{user_id}"

    @pytest.mark.asyncio
    async def test_superuser_returns_admin_id(self) -> None:
        """Test superuser returns admin:{id} format."""
        user_id = uuid4()
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.is_staff = False
        mock_user.is_superuser = True

        mock_request = Mock(spec=["scope"])
        mock_request.scope = {"user": mock_user}

        identifier = await get_rate_limit_identifier(mock_request)
        assert identifier == f"admin:{user_id}"

    @pytest.mark.asyncio
    async def test_x_forwarded_for_header(self) -> None:
        """Test X-Forwarded-For header is parsed correctly."""
        mock_request = Mock(spec=["scope", "headers"])
        mock_request.scope = {"user": None, "client": ("10.0.0.1", 8000)}
        mock_request.headers = {"X-Forwarded-For": "203.0.113.1, 198.51.100.1"}

        identifier = await get_rate_limit_identifier(mock_request)
        assert identifier == "anon:203.0.113.1"

    @pytest.mark.asyncio
    async def test_missing_client_returns_unknown(self) -> None:
        """Test missing client info returns anon:unknown."""
        mock_request = Mock(spec=["scope", "headers"])
        mock_request.scope = {"user": None, "client": None}
        mock_request.headers = {}

        identifier = await get_rate_limit_identifier(mock_request)
        assert identifier == "anon:unknown"

    def test_get_client_ip_from_x_forwarded_for(self) -> None:
        """Test _get_client_ip extracts IP from X-Forwarded-For header."""
        mock_request = Mock(spec=["scope", "headers"])
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="203.0.113.1, 198.51.100.1, 192.0.2.1")
        mock_request.scope = {"client": ("10.0.0.1", 8000)}

        ip = _get_client_ip(mock_request)
        assert ip == "203.0.113.1"

    def test_get_client_ip_from_client(self) -> None:
        """Test _get_client_ip falls back to client when no header."""
        mock_request = Mock(spec=["scope", "headers"])
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value=None)
        mock_request.scope = {"client": ("192.168.1.100", 8000)}

        ip = _get_client_ip(mock_request)
        assert ip == "192.168.1.100"

    def test_get_client_ip_unknown(self) -> None:
        """Test _get_client_ip returns unknown when no client info."""
        mock_request = Mock(spec=["scope", "headers"])
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value=None)
        mock_request.scope = {"client": None}

        ip = _get_client_ip(mock_request)
        assert ip == "unknown"


class TestRateLimitExceptionHandler:
    """Tests for rate_limit_exception_handler and helper functions."""

    def test_is_htmx_request_true(self) -> None:
        """Test HTMX request detection when HX-Request header is true."""
        mock_request = Mock(spec=["headers"])
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="true")

        assert _is_htmx_request(mock_request) is True

    def test_is_htmx_request_false(self) -> None:
        """Test HTMX request detection when header is missing."""
        mock_request = Mock(spec=["headers"])
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value=None)

        assert _is_htmx_request(mock_request) is False

    def test_is_api_request_path_prefix(self) -> None:
        """Test API request detection by path prefix."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/api/users"
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="text/html")

        assert _is_api_request(mock_request) is True

    def test_is_api_request_accept_header(self) -> None:
        """Test API request detection by Accept header."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/some/page"
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="application/json")

        assert _is_api_request(mock_request) is True

    def test_is_api_request_false(self) -> None:
        """Test non-API request detection."""
        mock_request = Mock(spec=["url", "headers"])
        mock_request.url = Mock()
        mock_request.url.path = "/some/page"
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="text/html")

        assert _is_api_request(mock_request) is False

    def test_extract_retry_after_from_headers(self) -> None:
        """Test retry-after extraction from exception headers."""
        exc = TooManyRequestsException(detail="Rate limit exceeded")
        exc.headers = {"retry-after": "90"}

        retry_after = _extract_retry_after(exc)
        assert retry_after == "90"

    def test_extract_retry_after_from_extra(self) -> None:
        """Test retry-after extraction from exception extra dict."""
        exc = TooManyRequestsException(detail="Rate limit exceeded")
        exc.extra = {"retry_after": 45}

        retry_after = _extract_retry_after(exc)
        assert retry_after == "45"

    def test_extract_retry_after_default(self) -> None:
        """Test retry-after defaults to 60 when not found."""
        exc = TooManyRequestsException(detail="Rate limit exceeded")

        retry_after = _extract_retry_after(exc)
        assert retry_after == "60"

    def test_create_toast_response_structure(self) -> None:
        """Test toast response has correct structure."""
        response = _create_toast_response("Test message", "60")

        assert isinstance(response, Response)
        assert response.status_code == HTTP_429_TOO_MANY_REQUESTS
        assert "HX-Trigger" in response.headers
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "60"
        assert response.headers["HX-Reswap"] == "none"

    def test_create_toast_response_trigger_content(self) -> None:
        """Test toast response HX-Trigger contains correct event."""
        response = _create_toast_response("Test message", "60")

        trigger_data = json.loads(response.headers["HX-Trigger"])
        assert "showToast" in trigger_data
        assert trigger_data["showToast"]["message"] == "Test message"
        assert trigger_data["showToast"]["type"] == "warning"

    def test_rate_limit_exception_handler_htmx(self) -> None:
        """Test handler returns toast response for HTMX requests."""
        mock_request = Mock(spec=["headers", "url", "client"])
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(side_effect=lambda key, default="": {"HX-Request": "true"}.get(key, default))
        mock_request.url = Mock()
        mock_request.url.path = "/some/endpoint"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        exc = TooManyRequestsException(detail="Too many requests")

        response = rate_limit_exception_handler(mock_request, exc)

        assert isinstance(response, Response)
        assert response.status_code == HTTP_429_TOO_MANY_REQUESTS
        assert "HX-Trigger" in response.headers

    def test_rate_limit_exception_handler_api(self) -> None:
        """Test handler returns JSON response for API requests."""
        mock_request = Mock(spec=["headers", "url", "client"])
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(
            side_effect=lambda key, default="": {"Accept": "application/json"}.get(key, default)
        )
        mock_request.url = Mock()
        mock_request.url.path = "/api/endpoint"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        exc = TooManyRequestsException(detail="Rate limit exceeded")
        exc.headers = {"retry-after": "30"}

        response = rate_limit_exception_handler(mock_request, exc)

        assert isinstance(response, Response)
        assert response.status_code == HTTP_429_TOO_MANY_REQUESTS
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "30"

        content = response.content
        assert content["error"] == "Too Many Requests"
        assert content["detail"] == "Rate limit exceeded"
        assert content["retry_after"] == "30"

    def test_rate_limit_exception_handler_browser(self) -> None:
        """Test handler returns Template response for browser requests."""
        mock_request = Mock(spec=["headers", "url", "client"])
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="text/html")
        mock_request.url = Mock()
        mock_request.url.path = "/page"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        exc = TooManyRequestsException(detail="Rate limit exceeded")
        exc.headers = {"retry-after": "120"}

        response = rate_limit_exception_handler(mock_request, exc)

        assert isinstance(response, Template)
        assert response.template_name == "errors/429.html.jinja2"
        assert response.status_code == HTTP_429_TOO_MANY_REQUESTS
        assert "title" in response.context
        assert "message" in response.context
        assert "retry_after" in response.context

    def test_rate_limit_exception_handler_retry_minutes(self) -> None:
        """Test handler calculates retry minutes correctly."""
        mock_request = Mock(spec=["headers", "url", "client"])
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value="text/html")
        mock_request.url = Mock()
        mock_request.url.path = "/page"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        exc = TooManyRequestsException(detail="Rate limit exceeded")
        exc.headers = {"retry-after": "180"}

        response = rate_limit_exception_handler(mock_request, exc)

        assert isinstance(response, Template)
        assert response.context["retry_minutes"] == 3

    def test_rate_limit_exception_handler_default_detail(self) -> None:
        """Test handler uses exception's default detail message."""
        mock_request = Mock(spec=["headers", "url", "client"])
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(
            side_effect=lambda key, default="": {"Accept": "application/json"}.get(key, default)
        )
        mock_request.url = Mock()
        mock_request.url.path = "/api/endpoint"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        exc = TooManyRequestsException()

        response = rate_limit_exception_handler(mock_request, exc)

        assert isinstance(response, Response)
        assert response.content["detail"] == "Too Many Requests"
        assert response.content["error"] == "Too Many Requests"


class TestCreateRateLimitConfig:
    """Tests for create_rate_limit_config function."""

    def test_returns_rate_limit_config_instance(self) -> None:
        """Test function returns RateLimitConfig instance."""
        mock_settings = Mock()
        mock_settings.redis_url = "redis://localhost:6379"

        config = create_rate_limit_config(mock_settings)

        assert isinstance(config, RateLimitConfig)

    def test_rate_limit_tuple(self) -> None:
        """Test rate limit is set to (minute, 100)."""
        mock_settings = Mock()
        mock_settings.redis_url = "redis://localhost:6379"

        config = create_rate_limit_config(mock_settings)

        assert config.rate_limit == ("minute", 100)

    def test_store_name(self) -> None:
        """Test store is set to rate_limit."""
        mock_settings = Mock()
        mock_settings.redis_url = "redis://localhost:6379"

        config = create_rate_limit_config(mock_settings)

        assert config.store == "rate_limit"

    def test_exclusions_include_health(self) -> None:
        """Test exclusions include /health endpoint."""
        mock_settings = Mock()
        mock_settings.redis_url = "redis://localhost:6379"

        config = create_rate_limit_config(mock_settings)

        assert config.exclude is not None
        assert "/health" in config.exclude

    def test_exclusions_include_static(self) -> None:
        """Test exclusions include /static/* paths."""
        mock_settings = Mock()
        mock_settings.redis_url = "redis://localhost:6379"

        config = create_rate_limit_config(mock_settings)

        assert config.exclude is not None
        assert "/static/*" in config.exclude

    def test_exclusions_include_schema(self) -> None:
        """Test exclusions include /schema endpoint."""
        mock_settings = Mock()
        mock_settings.redis_url = "redis://localhost:6379"

        config = create_rate_limit_config(mock_settings)

        assert config.exclude is not None
        assert "/schema" in config.exclude

    def test_exclusions_include_docs(self) -> None:
        """Test exclusions include /docs endpoint."""
        mock_settings = Mock()
        mock_settings.redis_url = "redis://localhost:6379"

        config = create_rate_limit_config(mock_settings)

        assert config.exclude is not None
        assert "/docs" in config.exclude

    def test_exclusions_include_api(self) -> None:
        """Test exclusions include /api endpoint."""
        mock_settings = Mock()
        mock_settings.redis_url = "redis://localhost:6379"

        config = create_rate_limit_config(mock_settings)

        assert config.exclude is not None
        assert "/api" in config.exclude


class TestCreateResponseCacheConfig:
    """Tests for create_response_cache_config function."""

    def test_returns_response_cache_config(self) -> None:
        """Test function returns ResponseCacheConfig instance."""
        from litestar.config.response_cache import ResponseCacheConfig

        mock_settings = Mock()
        mock_settings.redis_url = "redis://localhost:6379"

        config = create_response_cache_config(mock_settings)

        assert isinstance(config, ResponseCacheConfig)

    def test_default_expiration(self) -> None:
        """Test default expiration is set to 60 seconds."""
        mock_settings = Mock()
        mock_settings.redis_url = "redis://localhost:6379"

        config = create_response_cache_config(mock_settings)

        assert config.default_expiration == 60

    def test_store_name(self) -> None:
        """Test store is set to response_cache."""
        mock_settings = Mock()
        mock_settings.redis_url = "redis://localhost:6379"

        config = create_response_cache_config(mock_settings)

        assert config.store == "response_cache"
