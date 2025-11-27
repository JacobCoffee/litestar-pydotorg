"""Tests for feature flags system."""

from __future__ import annotations

import pytest
from litestar import Litestar, get
from litestar.testing import TestClient

from pydotorg.core.features import FeatureFlags, require_feature


class TestFeatureFlags:
    """Test suite for FeatureFlags class."""

    def test_feature_flags_initialization_with_defaults(self) -> None:
        """Test that feature flags initialize with default values."""
        flags = FeatureFlags()
        assert flags.enable_oauth is True
        assert flags.enable_jobs is True
        assert flags.enable_sponsors is True
        assert flags.enable_search is True
        assert flags.maintenance_mode is False

    def test_feature_flags_initialization_with_custom_values(self) -> None:
        """Test that feature flags can be initialized with custom values."""
        flags = FeatureFlags(
            enable_oauth=False,
            enable_jobs=False,
            enable_sponsors=False,
            enable_search=False,
            maintenance_mode=True,
        )
        assert flags.enable_oauth is False
        assert flags.enable_jobs is False
        assert flags.enable_sponsors is False
        assert flags.enable_search is False
        assert flags.maintenance_mode is True

    def test_is_enabled_returns_true_for_enabled_feature(self) -> None:
        """Test is_enabled returns True for enabled features."""
        flags = FeatureFlags(enable_oauth=True)
        assert flags.is_enabled("enable_oauth") is True

    def test_is_enabled_returns_false_for_disabled_feature(self) -> None:
        """Test is_enabled returns False for disabled features."""
        flags = FeatureFlags(enable_oauth=False)
        assert flags.is_enabled("enable_oauth") is False

    def test_is_enabled_raises_attribute_error_for_unknown_feature(self) -> None:
        """Test is_enabled raises AttributeError for unknown features."""
        flags = FeatureFlags()
        with pytest.raises(AttributeError, match="Unknown feature: unknown_feature"):
            flags.is_enabled("unknown_feature")

    def test_to_dict_returns_all_flags(self) -> None:
        """Test to_dict returns dictionary of all feature flags."""
        flags = FeatureFlags(
            enable_oauth=False,
            enable_jobs=True,
            enable_sponsors=False,
            enable_search=True,
            maintenance_mode=False,
        )
        result = flags.to_dict()
        assert result == {
            "enable_oauth": False,
            "enable_jobs": True,
            "enable_sponsors": False,
            "enable_search": True,
            "maintenance_mode": False,
        }


class TestRequireFeatureGuard:
    """Test suite for require_feature guard."""

    def test_guard_allows_access_when_feature_enabled(self) -> None:
        """Test that guard allows access when feature is enabled."""
        from litestar.config.app import AppConfig
        from litestar.datastructures import State

        @get("/test", guards=[require_feature("enable_oauth")], sync_to_thread=False)
        def test_handler() -> dict:
            return {"status": "ok"}

        def init_app(app_config: AppConfig) -> AppConfig:
            if app_config.state is None:
                app_config.state = State()
            app_config.state["feature_flags"] = FeatureFlags(enable_oauth=True)
            return app_config

        app = Litestar(
            route_handlers=[test_handler],
            on_app_init=[init_app],
        )
        client = TestClient(app=app)
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_guard_blocks_access_when_feature_disabled(self) -> None:
        """Test that guard blocks access when feature is disabled."""
        from litestar.config.app import AppConfig
        from litestar.datastructures import State

        @get("/test", guards=[require_feature("enable_oauth")], sync_to_thread=False)
        def test_handler() -> dict:
            return {"status": "ok"}

        def init_app(app_config: AppConfig) -> AppConfig:
            if app_config.state is None:
                app_config.state = State()
            app_config.state["feature_flags"] = FeatureFlags(enable_oauth=False)
            return app_config

        app = Litestar(
            route_handlers=[test_handler],
            on_app_init=[init_app],
        )
        client = TestClient(app=app)
        response = client.get("/test")
        assert response.status_code == 503

    def test_guard_blocks_access_when_maintenance_mode(self) -> None:
        """Test that guard blocks all access when in maintenance mode."""
        from litestar.config.app import AppConfig
        from litestar.datastructures import State

        @get("/test", guards=[require_feature("enable_oauth")], sync_to_thread=False)
        def test_handler() -> dict:
            return {"status": "ok"}

        def init_app(app_config: AppConfig) -> AppConfig:
            if app_config.state is None:
                app_config.state = State()
            app_config.state["feature_flags"] = FeatureFlags(
                enable_oauth=True,
                maintenance_mode=True,
            )
            return app_config

        app = Litestar(
            route_handlers=[test_handler],
            on_app_init=[init_app],
        )
        client = TestClient(app=app)
        response = client.get("/test")
        assert response.status_code == 503
