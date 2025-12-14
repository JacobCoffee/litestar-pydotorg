"""Custom OpenAPI UI plugins with Python.org theming."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar import Controller, Request, Response, get
from litestar.exceptions import NotAuthorizedException
from litestar.openapi.plugins import ScalarRenderPlugin, SwaggerRenderPlugin
from litestar.openapi.spec import OpenAPI
from litestar.status_codes import HTTP_200_OK

from pydotorg.config import settings

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from litestar.handlers.base import BaseRouteHandler


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
            css_url="/static/css/scalar-theme.css",
        ),
        SwaggerRenderPlugin(
            path="/swagger",
            favicon='<link rel="icon" type="image/x-icon" href="/static/images/favicon.ico">',
        ),
    ]


def _require_admin_session(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Guard that requires admin session (same as SQLAdmin).

    Checks for valid Litestar session with superuser privileges.
    """
    from pydotorg.core.auth.session import SessionService

    session_service = SessionService()

    session_id = connection.cookies.get(settings.session_cookie_name)
    if not session_id:
        raise NotAuthorizedException("Admin authentication required")

    user_id = session_service.get_user_id_from_session(session_id)
    if not user_id:
        raise NotAuthorizedException("Invalid or expired session")

    user = connection.user
    if not user or not user.is_superuser:
        raise NotAuthorizedException("Administrator privileges required")


def _generate_admin_schema(app: Any) -> dict[str, Any]:
    """Generate OpenAPI schema including admin routes.

    This creates a complete schema by iterating through all registered routes
    and including those marked with include_in_schema=False (admin routes).
    """
    from litestar.openapi.spec import (
        Components,
        Contact,
        ExternalDocumentation,
        Info,
        License,
        PathItem,
        SecurityScheme,
        Server,
        Tag,
    )

    base_schema = app.openapi_schema
    admin_paths: dict[str, PathItem] = {}

    for route in app.routes:
        if hasattr(route, "route_handlers"):
            for handler in route.route_handlers:
                if hasattr(handler, "include_in_schema") and not handler.include_in_schema:
                    if hasattr(handler, "paths"):
                        for path in handler.paths:
                            full_path = f"{route.path}{path}" if path != "/" else route.path
                            if full_path.startswith("/api/admin"):
                                method = handler.http_method.lower() if hasattr(handler, "http_method") else "get"
                                if isinstance(method, list):
                                    method = method[0].lower()

                                if full_path not in admin_paths:
                                    admin_paths[full_path] = PathItem()

                                operation = {
                                    "tags": handler.tags if hasattr(handler, "tags") and handler.tags else ["Admin"],
                                    "summary": handler.name.replace("_", " ").title() if hasattr(handler, "name") else "",
                                    "description": handler.fn.__doc__ or "" if hasattr(handler, "fn") else "",
                                    "operationId": handler.operation_id if hasattr(handler, "operation_id") else handler.name,
                                    "security": [{"BearerAuth": []}, {"SessionAuth": []}],
                                    "responses": {
                                        "200": {"description": "Successful response"},
                                        "401": {"description": "Authentication required"},
                                        "403": {"description": "Administrator privileges required"},
                                    },
                                }
                                setattr(admin_paths[full_path], method, operation)

    all_paths = {**base_schema.paths, **admin_paths} if base_schema.paths else admin_paths

    admin_schema = OpenAPI(
        openapi="3.1.0",
        info=Info(
            title=f"{settings.site_name} - Admin API",
            version="0.1.0",
            description=f"{settings.site_description}\n\n**Admin API Documentation** - Requires administrator authentication.",
            contact=Contact(
                name="Python.org",
                url="https://www.python.org",
                email="webmaster@python.org",
            ),
            license=License(
                name="Apache 2.0",
                identifier="Apache-2.0",
                url="https://www.apache.org/licenses/LICENSE-2.0",
            ),
        ),
        servers=[
            Server(url="http://localhost:8000", description="Development"),
            Server(url="https://staging.python.org", description="Staging"),
            Server(url="https://www.python.org", description="Production"),
        ],
        paths=all_paths,
        components=Components(
            security_schemes={
                "BearerAuth": SecurityScheme(
                    type="http",
                    scheme="bearer",
                    bearer_format="JWT",
                    description="JWT token from /api/auth/login",
                ),
                "SessionAuth": SecurityScheme(
                    type="apiKey",
                    in_="cookie",
                    name=settings.session_cookie_name,
                    description="Session cookie from admin login",
                ),
            },
            schemas=base_schema.components.schemas if base_schema.components else None,
        ),
        external_docs=ExternalDocumentation(
            url="https://docs.python.org",
            description="Python Documentation",
        ),
        tags=[
            Tag(name="Admin", description="Administrative endpoints for system management"),
            Tag(name="Application", description="Core application endpoints"),
            Tag(name="Authentication", description="User authentication endpoints"),
            Tag(name="Users", description="User management"),
            Tag(name="Pages", description="Content management"),
            Tag(name="Downloads", description="Python releases"),
            Tag(name="Jobs", description="Job board"),
            Tag(name="Events", description="Community events"),
            Tag(name="Blogs", description="Blog aggregation"),
            Tag(name="Sponsors", description="PSF sponsors"),
        ],
    )

    return admin_schema.to_schema()


SCALAR_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{title} - Admin API Docs</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="icon" type="image/x-icon" href="/static/images/favicon.ico">
    <link rel="stylesheet" href="/static/css/scalar-theme.css">
</head>
<body>
    <script id="api-reference" data-url="{schema_url}"></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
</body>
</html>
"""


class AdminOpenAPIController(Controller):
    """Admin-only OpenAPI documentation controller.

    Provides access to full API documentation including admin endpoints.
    Protected by session authentication (same as SQLAdmin).

    Endpoints:
        - /api/admin/docs/ - Scalar UI
        - /api/admin/docs/openapi.json - Full OpenAPI schema
    """

    path = "/api/admin/docs"
    tags = ["Admin"]
    guards = [_require_admin_session]
    include_in_schema = False

    @get("/openapi.json", status_code=HTTP_200_OK, media_type="application/json")
    async def get_admin_schema(self, request: Request) -> dict[str, Any]:
        """Get the full OpenAPI schema including admin routes.

        Returns:
            Complete OpenAPI 3.1 schema with admin endpoints included.
        """
        return _generate_admin_schema(request.app)

    @get("/", status_code=HTTP_200_OK, media_type="text/html")
    async def get_admin_docs_ui(self, request: Request) -> Response[str]:
        """Render Scalar UI for admin API documentation.

        Returns:
            HTML page with Scalar API reference viewer.
        """
        html = SCALAR_HTML_TEMPLATE.format(
            title=settings.site_name,
            schema_url="/api/admin/docs/openapi.json",
        )
        return Response(content=html, media_type="text/html")
