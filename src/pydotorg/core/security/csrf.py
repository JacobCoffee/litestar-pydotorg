"""CSRF (Cross-Site Request Forgery) protection configuration.

This module provides CSRF protection for the Litestar application using Litestar's
built-in CSRFConfig. CSRF tokens are automatically injected into templates and
validated on form submissions.

Usage in Templates:
    Use the form_start macro from forms.html.jinja2 which automatically includes
    the CSRF token for POST/PUT/PATCH/DELETE methods:

    {% from 'macros/forms.html.jinja2' import form_start, form_end, input_field %}

    {{ form_start(action='/submit', method='post') }}
        {{ input_field('username', 'Username', required=true) }}
        <button type="submit">Submit</button>
    {{ form_end() }}

    Or manually include the CSRF token using the csrf_token_field macro:

    <form method="post" action="/submit">
        {{ csrf_token_field() }}
        <input type="text" name="username">
        <button type="submit">Submit</button>
    </form>

Configuration:
    CSRF protection is configured in config.py with the following settings:
    - csrf_secret: Secret key for CSRF token generation
    - csrf_cookie_name: Name of the CSRF cookie (default: csrftoken)
    - csrf_header_name: Name of the CSRF header (default: x-csrftoken)

Excluded Routes:
    The following routes are excluded from CSRF protection:
    - /api/auth/* (JWT authentication endpoints)
    - /api/v1/* (API endpoints)
    - /health (health check endpoint)
    - /static/* (static files)
    - /admin/tasks/* (admin task operations, protected by admin auth guards)
"""

from __future__ import annotations

from litestar.config.csrf import CSRFConfig

from pydotorg.config import settings


def create_csrf_config() -> CSRFConfig:
    """Create CSRF configuration for the application.

    Configures CSRF protection with:
    - Secure cookie settings
    - Exclusion of API routes that use JWT authentication
    - Safe methods (GET, HEAD, OPTIONS) excluded from CSRF checks

    Returns:
        CSRFConfig: Configured CSRF protection instance
    """
    return CSRFConfig(
        secret=settings.csrf_secret,
        cookie_name=settings.csrf_cookie_name,
        header_name=settings.csrf_header_name,
        cookie_secure=not settings.debug,
        cookie_httponly=False,
        cookie_samesite="lax",
        cookie_path="/",
        exclude=[
            "/api/auth/*",
            "/api/v1/*",
            "/health",
            "/static/*",
            "/admin/tasks/*",
        ],
    )
