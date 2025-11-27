"""Structured logging configuration using structlog."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import structlog
from litestar.logging.config import LoggingConfig, StructlogEventFilter, StructLoggingConfig
from litestar.middleware.logging import LoggingMiddlewareConfig
from litestar.plugins.structlog import StructlogConfig, StructlogPlugin
from structlog.dev import RichTracebackFormatter

if TYPE_CHECKING:
    from structlog.typing import Processor


def _get_console_processors() -> list[Processor]:
    """Get processors for pretty console output with Rich."""
    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=RichTracebackFormatter(
                width=120,
                show_locals=True,
                max_frames=20,
            ),
        ),
    ]


def _get_json_processors() -> list[Processor]:
    """Get processors for JSON output in production."""
    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]


def _get_stdlib_processors(*, use_json: bool) -> list[Processor]:
    """Get processors for stdlib logging integration."""
    if use_json:
        return [
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.stdlib.ExtraAdder(),
            StructlogEventFilter(["color_message"]),
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ]
    return [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.stdlib.ExtraAdder(),
        StructlogEventFilter(["color_message"]),
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=RichTracebackFormatter(
                width=120,
                show_locals=True,
                max_frames=20,
            ),
        ),
    ]


def configure_structlog(
    log_level: str = "INFO",
    *,
    use_json: bool = False,
) -> StructlogPlugin:
    """Configure structlog for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: If True, use JSON formatter for production. If False, use rich console for development.

    Returns:
        StructlogPlugin: Configured structlog plugin
    """
    if use_json:
        processors = _get_json_processors()
        logger_factory = structlog.BytesLoggerFactory()
    else:
        processors = _get_console_processors()
        logger_factory = structlog.WriteLoggerFactory()

    stdlib_logging_config = LoggingConfig(
        root={"level": log_level, "handlers": ["queue_listener"]},
        loggers={
            "litestar": {"level": log_level, "handlers": ["queue_listener"], "propagate": False},
            "sqlalchemy": {"level": "WARNING", "handlers": ["queue_listener"], "propagate": False},
            "granian": {"level": "INFO", "handlers": ["queue_listener"], "propagate": False},
        },
        formatters={
            "standard": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": _get_stdlib_processors(use_json=use_json),
            }
        },
    )

    structlog_config = StructLoggingConfig(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(log_level.upper())),
        logger_factory=logger_factory,
        standard_lib_logging_config=stdlib_logging_config,
        pretty_print_tty=not use_json,
    )

    middleware_config = LoggingMiddlewareConfig(
        request_log_fields=(
            "method",
            "path",
            "path_params",
            "query",
            "content_type",
        ),
        response_log_fields=(
            "status_code",
            "content_type",
        ),
        logger_name="litestar",
    )

    config = StructlogConfig(
        structlog_logging_config=structlog_config,
        middleware_logging_config=middleware_config,
        enable_middleware_logging=True,
    )
    return StructlogPlugin(config=config)


def get_logger(name: str | None = None) -> Any:
    """Get a structlog logger instance.

    Args:
        name: Logger name. If None, uses the root logger.

    Returns:
        A structlog logger instance
    """
    return structlog.get_logger(name)


def bind_correlation_id(correlation_id: str) -> None:
    """Bind a correlation ID to the current context.

    Args:
        correlation_id: Unique identifier to correlate related log entries
    """
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def unbind_correlation_id() -> None:
    """Remove the correlation ID from the current context."""
    structlog.contextvars.unbind_contextvars("correlation_id")


def bind_user_context(user_id: int | str, username: str | None = None) -> None:
    """Bind user context to the current logging context.

    Args:
        user_id: User identifier
        username: Username (optional)
    """
    context = {"user_id": user_id}
    if username:
        context["username"] = username
    structlog.contextvars.bind_contextvars(**context)


def unbind_user_context() -> None:
    """Remove user context from the current logging context."""
    structlog.contextvars.unbind_contextvars("user_id", "username")
