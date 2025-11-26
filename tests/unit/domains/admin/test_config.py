"""Unit tests for admin configuration and schemas."""

from __future__ import annotations

from pydotorg.config import get_config_summary


class TestConfigSummary:
    """Tests for get_config_summary function."""

    def test_config_summary_structure(self) -> None:
        """Config summary should have expected structure."""
        config = get_config_summary()

        required_keys = [
            "environment",
            "debug",
            "log_level",
            "database_host",
            "database_port",
            "database_name",
            "redis_configured",
            "cdn_enabled",
            "email_enabled",
            "github_oauth_enabled",
            "google_oauth_enabled",
            "create_tables_on_startup",
            "cors_allow_all",
            "show_error_details",
            "jwt_algorithm",
            "session_expire_minutes",
            "features",
        ]

        for key in required_keys:
            assert key in config, f"Missing key '{key}' in config summary"

    def test_config_summary_no_sensitive_data(self) -> None:
        """Config summary should not contain sensitive information."""
        config = get_config_summary()

        config_str = str(config).lower()

        sensitive_patterns = [
            "password",
            "secret_key",
            "jwt_secret",
            "session_secret",
            "csrf_secret",
            "api_key",
            "client_secret",
            "smtp_password",
        ]

        for pattern in sensitive_patterns:
            assert pattern not in config_str, f"Sensitive data pattern '{pattern}' found in config summary"

    def test_config_summary_features_structure(self) -> None:
        """Config summary features should have expected structure."""
        config = get_config_summary()

        assert "features" in config
        features = config["features"]

        required_feature_keys = [
            "enable_oauth",
            "enable_jobs",
            "enable_sponsors",
            "enable_search",
            "maintenance_mode",
        ]

        for key in required_feature_keys:
            assert key in features, f"Missing feature flag '{key}'"

    def test_config_summary_types(self) -> None:
        """Config summary values should have correct types."""
        config = get_config_summary()

        assert isinstance(config["environment"], str)
        assert isinstance(config["debug"], bool)
        assert isinstance(config["log_level"], str)
        assert isinstance(config["database_host"], str)
        assert isinstance(config["database_port"], int)
        assert isinstance(config["database_name"], str)
        assert isinstance(config["redis_configured"], bool)
        assert isinstance(config["cdn_enabled"], bool)
        assert isinstance(config["email_enabled"], bool)
        assert isinstance(config["github_oauth_enabled"], bool)
        assert isinstance(config["google_oauth_enabled"], bool)
        assert isinstance(config["create_tables_on_startup"], bool)
        assert isinstance(config["cors_allow_all"], bool)
        assert isinstance(config["show_error_details"], bool)
        assert isinstance(config["jwt_algorithm"], str)
        assert isinstance(config["session_expire_minutes"], int)
        assert isinstance(config["features"], dict)

    def test_config_summary_feature_flags_are_bools(self) -> None:
        """All feature flags should be boolean values."""
        config = get_config_summary()
        features = config["features"]

        for key, value in features.items():
            assert isinstance(value, bool), f"Feature flag '{key}' is not a boolean"

    def test_config_summary_environment_values(self) -> None:
        """Environment should be one of the valid values."""
        config = get_config_summary()

        valid_environments = ["dev", "staging", "prod"]
        assert config["environment"] in valid_environments

    def test_config_summary_log_level_values(self) -> None:
        """Log level should be one of the valid values."""
        config = get_config_summary()

        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert config["log_level"] in valid_log_levels

    def test_config_summary_jwt_algorithm(self) -> None:
        """JWT algorithm should be a valid value."""
        config = get_config_summary()

        valid_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
        assert config["jwt_algorithm"] in valid_algorithms

    def test_config_summary_session_expire_reasonable(self) -> None:
        """Session expiration should be a reasonable value."""
        config = get_config_summary()

        session_expire = config["session_expire_minutes"]
        assert session_expire > 0, "Session expiration must be positive"
        assert session_expire <= 60 * 24 * 365, "Session expiration seems unreasonably long"
