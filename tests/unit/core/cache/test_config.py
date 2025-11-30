"""Unit tests for cache configuration."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pydotorg.core.cache.config import (
    CACHE_STORE_NAME,
    CACHE_TTL_DEFAULT,
    CACHE_TTL_PAGES,
    CACHE_TTL_STATIC,
    create_response_cache_config,
    page_cache_key_builder,
)


class TestCacheConstants:
    """Tests for cache configuration constants."""

    def test_cache_ttl_default(self) -> None:
        """Default TTL should be 60 seconds."""
        assert CACHE_TTL_DEFAULT == 60

    def test_cache_ttl_pages(self) -> None:
        """Pages TTL should be 300 seconds (5 minutes)."""
        assert CACHE_TTL_PAGES == 300

    def test_cache_ttl_static(self) -> None:
        """Static content TTL should be 3600 seconds (1 hour)."""
        assert CACHE_TTL_STATIC == 3600

    def test_cache_store_name(self) -> None:
        """Store name should be 'response_cache'."""
        assert CACHE_STORE_NAME == "response_cache"


class TestPageCacheKeyBuilder:
    """Tests for the page cache key builder function."""

    @pytest.fixture
    def mock_request(self) -> MagicMock:
        """Create a mock Litestar request."""
        request = MagicMock()
        request.url.path = "/about/history"
        request.query_params = {}
        return request

    def test_basic_path_key(self, mock_request: MagicMock) -> None:
        """Should create cache key from path only."""
        key = page_cache_key_builder(mock_request)
        assert key.startswith("page:")
        assert len(key) == len("page:") + 32

    def test_different_paths_different_keys(self, mock_request: MagicMock) -> None:
        """Different paths should produce different cache keys."""
        mock_request.url.path = "/about/history"
        key1 = page_cache_key_builder(mock_request)

        mock_request.url.path = "/about/mission"
        key2 = page_cache_key_builder(mock_request)

        assert key1 != key2

    def test_query_params_affect_key(self, mock_request: MagicMock) -> None:
        """Query parameters should be included in cache key."""
        mock_request.url.path = "/search"
        mock_request.query_params = {}
        key_without_params = page_cache_key_builder(mock_request)

        mock_request.query_params = {"q": "python"}
        key_with_params = page_cache_key_builder(mock_request)

        assert key_without_params != key_with_params

    def test_query_param_order_independent(self, mock_request: MagicMock) -> None:
        """Query parameters should produce same key regardless of order."""
        mock_request.url.path = "/search"
        mock_request.query_params = {"a": "1", "b": "2"}
        key1 = page_cache_key_builder(mock_request)

        mock_request.query_params = {"b": "2", "a": "1"}
        key2 = page_cache_key_builder(mock_request)

        assert key1 == key2

    def test_root_path(self, mock_request: MagicMock) -> None:
        """Should handle root path correctly."""
        mock_request.url.path = "/"
        mock_request.query_params = {}
        key = page_cache_key_builder(mock_request)
        assert key.startswith("page:")

    def test_key_is_consistent(self, mock_request: MagicMock) -> None:
        """Same request should always produce same key."""
        mock_request.url.path = "/test"
        mock_request.query_params = {}

        keys = [page_cache_key_builder(mock_request) for _ in range(10)]
        assert len(set(keys)) == 1


class TestCreateResponseCacheConfig:
    """Tests for the response cache configuration factory."""

    def test_returns_response_cache_config(self) -> None:
        """Should return a ResponseCacheConfig instance."""
        from litestar.config.response_cache import ResponseCacheConfig

        config = create_response_cache_config()
        assert isinstance(config, ResponseCacheConfig)

    def test_default_expiration(self) -> None:
        """Should use default expiration of 60 seconds."""
        config = create_response_cache_config()
        assert config.default_expiration == CACHE_TTL_DEFAULT

    def test_store_name(self) -> None:
        """Should use 'response_cache' store name."""
        config = create_response_cache_config()
        assert config.store == CACHE_STORE_NAME
