"""Unit tests for API versioning middleware."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from pydotorg.lib.api_versioning import (
    APIVersion,
    APIVersionMiddleware,
    APIVersionRegistry,
    add_version,
    deprecate_version,
    registry,
)

if TYPE_CHECKING:
    pass


@pytest.mark.unit
class TestAPIVersion:
    """Test suite for APIVersion dataclass."""

    def test_creates_version_from_string_v1(self) -> None:
        """Test parsing 'v1' format."""
        version = APIVersion.from_string("v1")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0

    def test_creates_version_from_string_numeric(self) -> None:
        """Test parsing '1' format."""
        version = APIVersion.from_string("1")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0

    def test_creates_version_from_string_with_minor(self) -> None:
        """Test parsing '1.2' format."""
        version = APIVersion.from_string("1.2")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 0

    def test_creates_version_from_string_full(self) -> None:
        """Test parsing '1.2.3' format."""
        version = APIVersion.from_string("1.2.3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

    def test_raises_on_invalid_version_string(self) -> None:
        """Test that invalid version strings raise ValueError."""
        with pytest.raises(ValueError, match="Invalid version string"):
            APIVersion.from_string("invalid")

    def test_str_representation(self) -> None:
        """Test string representation of version."""
        version = APIVersion(major=1, minor=2, patch=3)
        assert str(version) == "v1.2.3"

    def test_short_string_representation(self) -> None:
        """Test short string representation of version."""
        version = APIVersion(major=2, minor=1, patch=0)
        assert version.to_short_string() == "v2"

    def test_version_comparison_less_than(self) -> None:
        """Test version comparison for less than."""
        v1 = APIVersion(major=1, minor=0, patch=0)
        v2 = APIVersion(major=2, minor=0, patch=0)
        assert v1 < v2

    def test_version_comparison_equal(self) -> None:
        """Test version comparison for equality."""
        v1 = APIVersion(major=1, minor=2, patch=3)
        v2 = APIVersion(major=1, minor=2, patch=3)
        assert v1 == v2

    def test_version_hashable(self) -> None:
        """Test that versions can be used in sets and dicts."""
        v1 = APIVersion(major=1, minor=0, patch=0)
        v2 = APIVersion(major=1, minor=0, patch=0)
        versions = {v1, v2}
        assert len(versions) == 1

    def test_deprecated_version_attributes(self) -> None:
        """Test deprecated version with sunset date."""
        sunset = date(2025, 12, 31)
        version = APIVersion(major=1, minor=0, patch=0, deprecated=True, sunset_date=sunset)
        assert version.deprecated is True
        assert version.sunset_date == sunset


@pytest.mark.unit
class TestAPIVersionRegistry:
    """Test suite for APIVersionRegistry."""

    def test_registry_has_default_v1(self) -> None:
        """Test that registry has v1 as default."""
        reg = APIVersionRegistry()
        default = reg.get_default()
        assert default.major == 1

    def test_register_new_version(self) -> None:
        """Test registering a new version."""
        reg = APIVersionRegistry()
        v2 = APIVersion(major=2, minor=0, patch=0)
        reg.register(v2)
        assert reg.get_version(2) == v2

    def test_register_as_default(self) -> None:
        """Test registering a version as default."""
        reg = APIVersionRegistry()
        v2 = APIVersion(major=2, minor=0, patch=0)
        reg.register(v2, is_default=True)
        assert reg.get_default() == v2

    def test_is_supported(self) -> None:
        """Test checking if version is supported."""
        reg = APIVersionRegistry()
        v1 = APIVersion(major=1, minor=0, patch=0)
        v99 = APIVersion(major=99, minor=0, patch=0)
        assert reg.is_supported(v1) is True
        assert reg.is_supported(v99) is False

    def test_get_version_returns_none_for_unsupported(self) -> None:
        """Test get_version returns None for unsupported version."""
        reg = APIVersionRegistry()
        assert reg.get_version(99) is None


@pytest.mark.unit
class TestAPIVersionMiddleware:
    """Test suite for APIVersionMiddleware."""

    def _create_scope(
        self,
        path: str = "/api/v1/test",
        headers: list | None = None,
        query_string: bytes = b"",
    ) -> dict:
        """Create a mock ASGI scope."""
        return {
            "type": "http",
            "path": path,
            "headers": headers or [],
            "query_string": query_string,
        }

    def test_extracts_version_from_accept_header(self) -> None:
        """Test extracting version from Accept header."""
        middleware = APIVersionMiddleware(MagicMock())
        scope = self._create_scope(headers=[(b"accept", b"application/vnd.pydotorg.v1+json")])

        version = middleware._extract_version_from_accept(scope)
        assert version is not None
        assert version.major == 1

    def test_extracts_version_from_path(self) -> None:
        """Test extracting version from URL path."""
        middleware = APIVersionMiddleware(MagicMock())
        scope = self._create_scope(path="/api/v2/users")

        version = middleware._extract_version_from_path(scope)
        assert version is not None
        assert version.major == 2

    def test_extracts_version_from_query_param(self) -> None:
        """Test extracting version from query parameter."""
        middleware = APIVersionMiddleware(MagicMock())
        scope = self._create_scope(query_string=b"api_version=1")

        version = middleware._extract_version_from_query(scope)
        assert version is not None
        assert version.major == 1

    def test_returns_none_for_no_accept_version(self) -> None:
        """Test returns None when no version in Accept header."""
        middleware = APIVersionMiddleware(MagicMock())
        scope = self._create_scope(headers=[(b"accept", b"application/json")])

        version = middleware._extract_version_from_accept(scope)
        assert version is None

    def test_returns_none_for_no_path_version(self) -> None:
        """Test returns None when no version in path."""
        middleware = APIVersionMiddleware(MagicMock())
        scope = self._create_scope(path="/users")

        version = middleware._extract_version_from_path(scope)
        assert version is None

    def test_negotiates_version_priority_accept_first(self) -> None:
        """Test that Accept header takes priority."""
        middleware = APIVersionMiddleware(MagicMock())
        scope = self._create_scope(
            path="/api/v2/users",
            headers=[(b"accept", b"application/vnd.pydotorg.v1+json")],
        )

        version = middleware._negotiate_version(scope)
        assert version.major == 1

    def test_negotiates_version_fallback_to_path(self) -> None:
        """Test fallback to path version when no Accept header."""
        middleware = APIVersionMiddleware(MagicMock())
        scope = self._create_scope(path="/api/v1/users")

        version = middleware._negotiate_version(scope)
        assert version.major == 1

    def test_negotiates_version_fallback_to_query(self) -> None:
        """Test fallback to query parameter when no Accept or path version."""
        middleware = APIVersionMiddleware(MagicMock())
        scope = self._create_scope(path="/api/users", query_string=b"api_version=1")

        version = middleware._negotiate_version(scope)
        assert version.major == 1

    def test_negotiates_version_fallback_to_default(self) -> None:
        """Test fallback to default version when no version specified."""
        middleware = APIVersionMiddleware(MagicMock())
        scope = self._create_scope(path="/api/users")

        version = middleware._negotiate_version(scope)
        assert version == registry.get_default()

    async def test_passes_through_non_http_requests(self) -> None:
        """Test that non-HTTP requests pass through unchanged."""
        mock_app = AsyncMock()
        middleware = APIVersionMiddleware(mock_app)

        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        mock_app.assert_called_once_with(scope, receive, send)

    async def test_passes_through_non_api_paths(self) -> None:
        """Test that non-API paths pass through unchanged."""
        mock_app = AsyncMock()
        middleware = APIVersionMiddleware(mock_app)

        scope = {"type": "http", "path": "/docs"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        mock_app.assert_called_once_with(scope, receive, send)


@pytest.mark.unit
class TestHelperFunctions:
    """Test suite for helper functions."""

    def test_deprecate_version(self) -> None:
        """Test deprecating a version."""
        test_registry = APIVersionRegistry()
        test_registry.register(APIVersion(major=1, minor=0, patch=0))

        sunset = date(2025, 12, 31)

        original_get_version = registry.get_version
        original_register = registry.register

        try:
            registry.get_version = test_registry.get_version
            registry.register = test_registry.register
            registry.get_default = test_registry.get_default

            deprecate_version(1, sunset_date=sunset)
            version = test_registry.get_version(1)
            assert version is not None
            assert version.deprecated is True
            assert version.sunset_date == sunset
        finally:
            registry.get_version = original_get_version
            registry.register = original_register

    def test_add_version(self) -> None:
        """Test adding a new version."""
        test_registry = APIVersionRegistry()

        original_register = registry.register

        try:
            registry.register = test_registry.register

            version = add_version(3, 1, 0)
            assert version.major == 3
            assert version.minor == 1
            assert version.patch == 0
        finally:
            registry.register = original_register
