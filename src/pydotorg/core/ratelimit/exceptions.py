"""Rate limit exception handler with HTMX-aware responses.

This module provides a custom exception handler for 429 Too Many Requests errors
that adapts responses based on the request type (HTMX, API, or browser). It
automatically includes Retry-After headers to inform clients when they can retry.

Features:
    - HTMX requests: Returns toast notification with rate limit message
    - API requests: Returns JSON with Retry-After header
    - Browser requests: Renders full 429 error template
    - Automatic Retry-After header extraction from exception

Usage::

    from pydotorg.core.ratelimit.exceptions import rate_limit_exception_handler
    from litestar.exceptions import TooManyRequestsException

    app = Litestar(
        exception_handlers={
            TooManyRequestsException: rate_limit_exception_handler,
        }
    )
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from litestar.response import Response, Template
from litestar.status_codes import HTTP_429_TOO_MANY_REQUESTS

if TYPE_CHECKING:
    from litestar import Request
    from litestar.exceptions import TooManyRequestsException

logger = logging.getLogger(__name__)


def _is_htmx_request(request: Request) -> bool:
    """Check if the request is an HTMX request.

    Args:
        request: The incoming request

    Returns:
        bool: True if HX-Request header is present and set to "true"
    """
    return request.headers.get("HX-Request") == "true"


def _is_api_request(request: Request) -> bool:
    """Check if the request is an API request.

    Args:
        request: The incoming request

    Returns:
        bool: True if path starts with /api/ or Accept header is application/json
    """
    return request.url.path.startswith("/api/") or "application/json" in request.headers.get("Accept", "")


def _extract_retry_after(exc: TooManyRequestsException) -> str:
    """Extract Retry-After value from exception headers or detail.

    The exception may contain retry information in its headers dict or
    as part of the detail message. Default to "60" (60 seconds) if not found.

    Args:
        exc: The TooManyRequestsException that was raised

    Returns:
        str: Retry-After value in seconds (e.g., "60")
    """
    if hasattr(exc, "headers") and exc.headers and "retry-after" in exc.headers:
        return str(exc.headers["retry-after"])

    if hasattr(exc, "extra") and isinstance(exc.extra, dict):
        retry_after = exc.extra.get("retry_after")
        if retry_after:
            return str(retry_after)

    return "60"


def _create_toast_response(
    message: str,
    retry_after: str,
) -> Response:
    """Create an HTMX-compatible response that triggers a toast notification.

    Args:
        message: The message to display in the toast
        retry_after: Retry-After value in seconds

    Returns:
        Response with HX-Trigger header for toast display and Retry-After header
    """
    toast_event = json.dumps(
        {
            "showToast": {
                "message": message,
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


def rate_limit_exception_handler(
    request: Request,
    exc: TooManyRequestsException,
) -> Response | Template:
    """Handle 429 Too Many Requests exceptions with adaptive responses.

    Provides different response formats based on the request type:
    - HTMX requests: Empty response with toast notification trigger
    - API requests: JSON response with error details
    - Browser requests: Full HTML error page with friendly message

    All responses include the Retry-After header to inform clients when
    they can retry their request.

    Args:
        request: The incoming request
        exc: The TooManyRequestsException that was raised

    Returns:
        Response | Template: Appropriate response based on request type

    Example:
        >>> @get("/resource")
        >>> async def resource():
        >>> # This will trigger rate limit exception if limit exceeded
        >>>     return {"data": "resource"}
    """
    retry_after = _extract_retry_after(exc)
    detail = exc.detail if exc.detail else "Too many requests. Please try again later."

    retry_minutes = int(retry_after) // 60 if retry_after.isdigit() else 1
    retry_seconds = int(retry_after) if retry_after.isdigit() else 60

    logger.warning(
        "Rate limit exceeded on %s from IP %s - retry in %s seconds",
        request.url.path,
        request.client.host if request.client else "unknown",
        retry_after,
    )

    if _is_htmx_request(request):
        friendly_message = (
            f"{detail} You can try again in {retry_minutes} minute{'s' if retry_minutes != 1 else ''}."
            if retry_minutes > 0
            else f"{detail} Please wait {retry_seconds} seconds before trying again."
        )
        return _create_toast_response(
            message=friendly_message,
            retry_after=retry_after,
        )

    if _is_api_request(request):
        return Response(
            content={
                "error": "Too Many Requests",
                "detail": detail,
                "retry_after": retry_after,
                "status_code": HTTP_429_TOO_MANY_REQUESTS,
            },
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": retry_after},
        )

    friendly_message = (
        f"You've made too many requests. Please wait {retry_minutes} minute{'s' if retry_minutes != 1 else ''} before trying again."
        if retry_minutes > 0
        else f"You've made too many requests. Please wait {retry_seconds} seconds before trying again."
    )

    return Template(
        template_name="errors/429.html.jinja2",
        context={
            "title": "Too Many Requests",
            "message": friendly_message,
            "retry_after": retry_after,
            "retry_minutes": retry_minutes,
        },
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        headers={"Retry-After": retry_after},
    )
