"""Site-wide exception handlers with HTMX-aware flash message support."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING
from urllib.parse import quote

from advanced_alchemy.exceptions import (
    DuplicateKeyError as AADuplicateKeyError,
)
from advanced_alchemy.exceptions import (
    ForeignKeyError as AAForeignKeyError,
)
from advanced_alchemy.exceptions import (
    IntegrityError as AAIntegrityError,
)
from advanced_alchemy.exceptions import (
    NotFoundError as AANotFoundError,
)
from advanced_alchemy.exceptions import (
    RepositoryError as AARepositoryError,
)
from litestar.exceptions import (
    HTTPException,
    InternalServerException,
    NotFoundException,
    PermissionDeniedException,
)
from litestar.response import Redirect, Response, Template
from litestar.status_codes import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

if TYPE_CHECKING:
    from litestar import Request

logger = logging.getLogger(__name__)


def _is_htmx_request(request: Request) -> bool:
    """Check if the request is an HTMX request."""
    return request.headers.get("HX-Request") == "true"


def _is_api_request(request: Request) -> bool:
    """Check if the request is an API request.

    Returns True if:
    - Path starts with /api/
    - Accept header includes application/json
    """
    path = request.url.path
    accept = request.headers.get("Accept", "")
    return path.startswith("/api/") or "application/json" in accept


def _create_json_error_response(
    detail: str,
    status_code: int,
    extra: dict | None = None,
) -> Response:
    """Create a JSON error response for API requests.

    Args:
        detail: Error message
        status_code: HTTP status code
        extra: Additional error details

    Returns:
        JSON response with error information
    """
    content = {"detail": detail, "status_code": status_code}
    if extra:
        content["extra"] = extra
    return Response(
        content=content,
        status_code=status_code,
        media_type="application/json",
    )


def _create_toast_response(
    message: str,
    toast_type: str = "error",
    status_code: int = HTTP_404_NOT_FOUND,
) -> Response:
    """Create an HTMX-compatible response that triggers a toast notification.

    Args:
        message: The message to display in the toast
        toast_type: Type of toast (error, warning, info, success)
        status_code: HTTP status code for the response

    Returns:
        Response with HX-Trigger header for toast display
    """
    toast_event = json.dumps(
        {
            "showToast": {
                "message": message,
                "type": toast_type,
            }
        }
    )
    return Response(
        content=None,
        status_code=status_code,
        headers={"HX-Trigger": toast_event, "HX-Reswap": "none"},
    )


CACHE_404_MAX_AGE = 300


def not_found_exception_handler(request: Request, exc: NotFoundException) -> Response | Template:
    """Handle 404 Not Found exceptions site-wide.

    For API requests: Returns JSON error response.
    For HTMX requests: Returns empty response with HX-Trigger for toast notification.
    For regular requests: Renders the 404 error template with 5-minute cache.

    Args:
        request: The incoming request
        exc: The NotFoundException that was raised

    Returns:
        JSON response, HTMX toast response, or rendered error template
    """
    path = request.url.path
    detail = exc.detail if exc.detail else "Resource not found"
    logger.info("404 Not Found: %s", path)

    if _is_api_request(request):
        return _create_json_error_response(detail=detail, status_code=HTTP_404_NOT_FOUND)

    friendly_name = path.strip("/").replace("/", " → ").replace("-", " ").title() or "Home"
    friendly_detail = f"'{friendly_name}' is not available yet. This feature is coming soon."

    if _is_htmx_request(request):
        return _create_toast_response(
            message=friendly_detail,
            toast_type="info",
            status_code=HTTP_404_NOT_FOUND,
        )

    return Template(
        template_name="errors/404.html.jinja2",
        context={
            "title": "Page Not Found",
            "message": friendly_detail,
            "path": path,
        },
        status_code=HTTP_404_NOT_FOUND,
        headers={"Cache-Control": f"max-age={CACHE_404_MAX_AGE}"},
    )


def http_exception_handler(request: Request, exc: HTTPException) -> Response | Template | Redirect:
    """Handle generic HTTP exceptions site-wide.

    For API requests: Returns JSON error response.
    For HTMX requests: Returns toast notification.
    For browser requests: Returns HTML template or redirect.

    Args:
        request: The incoming request
        exc: The HTTPException that was raised

    Returns:
        Appropriate response based on request type and exception
    """
    status_code = exc.status_code
    detail = exc.detail if exc.detail else f"An error occurred (HTTP {status_code})"
    extra = getattr(exc, "extra", None)
    logger.warning("HTTP %d on %s: %s", status_code, request.url.path, detail)

    if _is_api_request(request):
        return _create_json_error_response(detail=detail, status_code=status_code, extra=extra)

    if _is_htmx_request(request):
        toast_type = "warning" if status_code < HTTP_500_INTERNAL_SERVER_ERROR else "error"
        return _create_toast_response(
            message=detail,
            toast_type=toast_type,
            status_code=status_code,
        )

    if status_code == HTTP_401_UNAUTHORIZED:
        next_url = quote(str(request.url), safe="")
        return Redirect(f"/auth/login?next={next_url}")

    if status_code == HTTP_403_FORBIDDEN:
        return Template(
            template_name="errors/403.html.jinja2",
            context={
                "title": "Access Denied",
                "message": detail,
            },
            status_code=status_code,
        )

    return Template(
        template_name="errors/generic.html.jinja2",
        context={
            "title": f"Error {status_code}",
            "message": detail,
            "status_code": status_code,
        },
        status_code=status_code,
    )


def permission_denied_handler(request: Request, exc: PermissionDeniedException) -> Response | Template:
    """Handle permission denied exceptions.

    For API requests: Returns JSON error response.
    For HTMX requests: Returns toast notification.
    For browser requests: Returns 403 template.

    Args:
        request: The incoming request
        exc: The PermissionDeniedException that was raised

    Returns:
        JSON response, HTMX toast response, or rendered 403 template
    """
    detail = exc.detail if exc.detail else "You do not have permission to access this resource."
    logger.warning("403 Forbidden on %s", request.url.path)

    if _is_api_request(request):
        return _create_json_error_response(detail=detail, status_code=HTTP_403_FORBIDDEN)

    if _is_htmx_request(request):
        return _create_toast_response(
            message=detail,
            toast_type="error",
            status_code=HTTP_403_FORBIDDEN,
        )

    return Template(
        template_name="errors/403.html.jinja2",
        context={
            "title": "Access Denied",
            "message": detail,
        },
        status_code=HTTP_403_FORBIDDEN,
    )


def internal_server_error_handler(request: Request, exc: InternalServerException) -> Response | Template:
    """Handle internal server errors.

    For API requests: Returns JSON error response.
    For HTMX requests: Returns toast notification.
    For browser requests: Returns 500 template.

    Args:
        request: The incoming request
        exc: The InternalServerException that was raised

    Returns:
        JSON response, HTMX toast response, or rendered 500 template
    """
    logger.exception("500 Internal Server Error on %s", request.url.path)

    message = "An unexpected error occurred. Please try again later."

    if _is_api_request(request):
        return _create_json_error_response(detail=message, status_code=HTTP_500_INTERNAL_SERVER_ERROR)

    if _is_htmx_request(request):
        return _create_toast_response(
            message=message,
            toast_type="error",
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Template(
        template_name="errors/500.html.jinja2",
        context={
            "title": "Server Error",
            "message": message,
        },
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
    )


HTTP_409_CONFLICT = 409


def repository_exception_handler(request: Request, exc: AARepositoryError) -> Response | Template:
    """Handle advanced-alchemy repository exceptions.

    Converts advanced-alchemy exceptions to appropriate HTTP responses:
    - NotFoundError -> 404 Not Found
    - DuplicateKeyError, IntegrityError, ForeignKeyError -> 409 Conflict
    - Other RepositoryError -> 500 Internal Server Error

    Args:
        request: The incoming request
        exc: The RepositoryError that was raised

    Returns:
        JSON response, HTMX toast response, or rendered error template
    """
    path = request.url.path
    detail = str(exc.detail) if hasattr(exc, "detail") and exc.detail else str(exc)

    if isinstance(exc, AANotFoundError):
        status_code = HTTP_404_NOT_FOUND
        logger.info("404 Not Found (Repository): %s - %s", path, detail)
    elif isinstance(exc, AADuplicateKeyError | AAIntegrityError | AAForeignKeyError):
        status_code = HTTP_409_CONFLICT
        logger.warning("409 Conflict (Repository): %s - %s", path, detail)
    else:
        status_code = HTTP_500_INTERNAL_SERVER_ERROR
        logger.error("500 Repository Error: %s - %s", path, detail)

    if _is_api_request(request):
        return _create_json_error_response(detail=detail, status_code=status_code)

    friendly_name = path.strip("/").replace("/", " → ").replace("-", " ").title() or "Home"

    if status_code == HTTP_404_NOT_FOUND:
        friendly_detail = f"'{friendly_name}' could not be found."
        template_name = "errors/404.html.jinja2"
        title = "Not Found"
    elif status_code == HTTP_409_CONFLICT:
        friendly_detail = "A conflict occurred with the requested resource."
        template_name = "errors/generic.html.jinja2"
        title = "Conflict"
    else:
        friendly_detail = "An unexpected error occurred. Please try again later."
        template_name = "errors/500.html.jinja2"
        title = "Server Error"

    if _is_htmx_request(request):
        toast_type = "error" if status_code >= HTTP_500_INTERNAL_SERVER_ERROR else "warning"
        return _create_toast_response(
            message=friendly_detail,
            toast_type=toast_type,
            status_code=status_code,
        )

    return Template(
        template_name=template_name,
        context={
            "title": title,
            "message": friendly_detail,
            "path": path,
            "status_code": status_code,
        },
        status_code=status_code,
    )


def get_exception_handlers() -> dict:
    """Get all site-wide exception handlers.

    Returns:
        Dictionary mapping exception types to their handlers
    """
    return {
        AARepositoryError: repository_exception_handler,
        NotFoundException: not_found_exception_handler,
        PermissionDeniedException: permission_denied_handler,
        InternalServerException: internal_server_error_handler,
        HTTPException: http_exception_handler,
    }
