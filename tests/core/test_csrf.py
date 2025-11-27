"""Tests for CSRF protection configuration."""

from __future__ import annotations

import pytest
from litestar.config.csrf import CSRFConfig

from pydotorg.config import settings
from pydotorg.core.security.csrf import create_csrf_config


class TestCreateCSRFConfig:
    """Test suite for create_csrf_config function."""

    def test_returns_csrf_config_instance(self) -> None:
        """Test that create_csrf_config returns a CSRFConfig instance."""
        config = create_csrf_config()
        assert isinstance(config, CSRFConfig)

    def test_uses_settings_secret(self) -> None:
        """Test that CSRF config uses the secret from settings."""
        config = create_csrf_config()
        assert config.secret == settings.csrf_secret

    def test_uses_settings_cookie_name(self) -> None:
        """Test that CSRF config uses the cookie name from settings."""
        config = create_csrf_config()
        assert config.cookie_name == settings.csrf_cookie_name

    def test_uses_settings_header_name(self) -> None:
        """Test that CSRF config uses the header name from settings."""
        config = create_csrf_config()
        assert config.header_name == settings.csrf_header_name

    def test_cookie_httponly_enabled(self) -> None:
        """Test that CSRF cookie is httponly."""
        config = create_csrf_config()
        assert config.cookie_httponly is True

    def test_cookie_samesite_is_lax(self) -> None:
        """Test that CSRF cookie has samesite=lax."""
        config = create_csrf_config()
        assert config.cookie_samesite == "lax"

    def test_cookie_path_is_root(self) -> None:
        """Test that CSRF cookie path is root."""
        config = create_csrf_config()
        assert config.cookie_path == "/"


class TestCSRFExclusions:
    """Test suite for CSRF route exclusions."""

    def test_excludes_api_auth_routes(self) -> None:
        """Test that /api/auth/* routes are excluded from CSRF."""
        config = create_csrf_config()
        assert "/api/auth/*" in config.exclude

    def test_excludes_api_v1_routes(self) -> None:
        """Test that /api/v1/* routes are excluded from CSRF."""
        config = create_csrf_config()
        assert "/api/v1/*" in config.exclude

    def test_excludes_health_endpoint(self) -> None:
        """Test that /health endpoint is excluded from CSRF."""
        config = create_csrf_config()
        assert "/health" in config.exclude

    def test_excludes_static_files(self) -> None:
        """Test that /static/* routes are excluded from CSRF."""
        config = create_csrf_config()
        assert "/static/*" in config.exclude

    def test_exclusion_list_has_expected_length(self) -> None:
        """Test that exclusion list has expected number of entries."""
        config = create_csrf_config()
        assert len(config.exclude) == 4


class TestCSRFSecuritySettings:
    """Test suite for CSRF security settings based on debug mode."""

    def test_cookie_secure_based_on_debug(self) -> None:
        """Test that cookie_secure is opposite of debug setting."""
        config = create_csrf_config()
        assert config.cookie_secure == (not settings.debug if settings.debug is not None else not settings.is_debug)
