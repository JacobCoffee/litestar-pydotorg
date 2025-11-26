"""Custom OpenAPI UI plugins with Python.org theming."""

from __future__ import annotations

from litestar.openapi.plugins import ScalarRenderPlugin, SwaggerRenderPlugin


def get_openapi_plugins() -> list[ScalarRenderPlugin | SwaggerRenderPlugin]:
    """Get the configured OpenAPI UI plugins.

    Returns:
        List of OpenAPI UI plugins with Scalar as primary and Swagger as secondary.

    Endpoints (relative to OpenAPIConfig.path which is /api):
        - /api/ or /api/docs - Scalar UI (default)
        - /api/swagger - Swagger UI
        - /api/openapi.json - OpenAPI schema
    """
    return [
        ScalarRenderPlugin(
            path="/",
            favicon='<link rel="icon" type="image/x-icon" href="/static/images/favicon.ico">',
        ),
        SwaggerRenderPlugin(
            path="/swagger",
            favicon='<link rel="icon" type="image/x-icon" href="/static/images/favicon.ico">',
        ),
    ]
