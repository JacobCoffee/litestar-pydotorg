"""Tests for structlog configuration."""

from __future__ import annotations

import structlog
from litestar.plugins.structlog import StructlogPlugin
from structlog.dev import ConsoleRenderer, RichTracebackFormatter
from structlog.processors import JSONRenderer

from pydotorg.core.logging import (
    bind_correlation_id,
    bind_user_context,
    configure_structlog,
    get_logger,
    unbind_correlation_id,
    unbind_user_context,
)


class TestConfigureStructlog:
    def test_returns_structlog_plugin(self) -> None:
        plugin = configure_structlog()
        assert isinstance(plugin, StructlogPlugin)

    def test_plugin_has_on_app_init(self) -> None:
        plugin = configure_structlog()
        assert hasattr(plugin, "on_app_init")
        assert callable(plugin.on_app_init)


class TestRichTracebackFormatter:
    def test_formatter_instantiation(self) -> None:
        formatter = RichTracebackFormatter(
            width=120,
            show_locals=True,
            max_frames=20,
        )
        assert formatter.width == 120
        assert formatter.show_locals is True
        assert formatter.max_frames == 20

    def test_formatter_default_values(self) -> None:
        formatter = RichTracebackFormatter()
        assert formatter.show_locals is True
        assert formatter.max_frames == 100


class TestConsoleRendererWithRich:
    def test_console_renderer_accepts_rich_formatter(self) -> None:
        formatter = RichTracebackFormatter(width=120, show_locals=True)
        renderer = ConsoleRenderer(colors=True, exception_formatter=formatter)
        assert renderer._colors is True
        assert isinstance(renderer._exception_formatter, RichTracebackFormatter)

    def test_console_renderer_colors_enabled(self) -> None:
        renderer = ConsoleRenderer(colors=True)
        assert renderer._colors is True

    def test_console_renderer_colors_disabled(self) -> None:
        renderer = ConsoleRenderer(colors=False)
        assert renderer._colors is False


class TestJSONRenderer:
    def test_json_renderer_instantiation(self) -> None:
        renderer = JSONRenderer()
        assert isinstance(renderer, JSONRenderer)


class TestGetLogger:
    def test_returns_logger(self) -> None:
        logger = get_logger("test")
        assert logger is not None

    def test_returns_logger_without_name(self) -> None:
        logger = get_logger()
        assert logger is not None

    def test_logger_has_expected_methods(self) -> None:
        logger = get_logger("test")
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")


class TestContextBindings:
    def setup_method(self) -> None:
        structlog.contextvars.clear_contextvars()

    def teardown_method(self) -> None:
        structlog.contextvars.clear_contextvars()

    def test_bind_correlation_id(self) -> None:
        bind_correlation_id("test-123")
        ctx = structlog.contextvars.get_contextvars()
        assert ctx.get("correlation_id") == "test-123"

    def test_unbind_correlation_id(self) -> None:
        bind_correlation_id("test-123")
        unbind_correlation_id()
        ctx = structlog.contextvars.get_contextvars()
        assert "correlation_id" not in ctx

    def test_bind_user_context_with_id_only(self) -> None:
        bind_user_context(user_id=42)
        ctx = structlog.contextvars.get_contextvars()
        assert ctx.get("user_id") == 42
        assert "username" not in ctx

    def test_bind_user_context_with_username(self) -> None:
        bind_user_context(user_id=42, username="testuser")
        ctx = structlog.contextvars.get_contextvars()
        assert ctx.get("user_id") == 42
        assert ctx.get("username") == "testuser"

    def test_unbind_user_context(self) -> None:
        bind_user_context(user_id=42, username="testuser")
        unbind_user_context()
        ctx = structlog.contextvars.get_contextvars()
        assert "user_id" not in ctx
        assert "username" not in ctx

    def test_bind_user_context_string_id(self) -> None:
        bind_user_context(user_id="user-uuid-123")
        ctx = structlog.contextvars.get_contextvars()
        assert ctx.get("user_id") == "user-uuid-123"
