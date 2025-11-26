"""Custom OpenAPI UI plugins with Python.org theming."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar.openapi.plugins import ScalarRenderPlugin, SwaggerRenderPlugin

if TYPE_CHECKING:
    from litestar.connection import Request


class PythonOrgScalarPlugin(ScalarRenderPlugin):
    """Scalar OpenAPI UI plugin with Python.org custom theme.

    Serves the API documentation at /docs (default) with custom
    Python-branded styling.
    """

    def __init__(
        self,
        *,
        path: str = "/docs",
        title: str | None = None,
        favicon: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Python.org Scalar plugin.

        Args:
            path: URL path for the documentation UI.
            title: Custom title for the documentation page.
            favicon: Custom favicon HTML tag.
            **kwargs: Additional arguments passed to ScalarRenderPlugin.
        """
        super().__init__(
            path=path,
            favicon=favicon or '<link rel="icon" type="image/x-icon" href="/static/images/favicon.ico">',
            **kwargs,
        )
        self._custom_title = title

    def render(self, openapi_schema: dict[str, Any], request: Request) -> str:
        """Render the Scalar UI with Python.org custom theme.

        Args:
            openapi_schema: The OpenAPI schema dictionary.
            request: The incoming request.

        Returns:
            HTML string for the Scalar documentation page.
        """
        schema_json = self._encode_json(openapi_schema)
        title = self._custom_title or openapi_schema.get("info", {}).get("title", "API Documentation")

        return f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - API Documentation</title>
    {self.favicon}
    <link rel="stylesheet" href="/static/css/scalar-theme.css">
    <style>
        /* Base Scalar configuration */
        body {{
            margin: 0;
            padding: 0;
        }}

        /* Python.org branding header */
        .python-header {{
            background: linear-gradient(135deg, #3776AB 0%, #2B5B8A 100%);
            padding: 12px 24px;
            display: flex;
            align-items: center;
            gap: 12px;
            border-bottom: 3px solid #FFD43B;
        }}

        .python-header img {{
            height: 40px;
        }}

        .python-header h1 {{
            color: white;
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0;
            font-family: system-ui, -apple-system, sans-serif;
        }}

        .python-header .subtitle {{
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.875rem;
            margin-left: auto;
            font-family: system-ui, -apple-system, sans-serif;
        }}

        /* Dark mode toggle */
        .theme-toggle {{
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            padding: 6px 12px;
            color: white;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.2s ease;
        }}

        .theme-toggle:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
    </style>
</head>
<body>
    <div class="python-header">
        <svg height="40" viewBox="0 0 110 110" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="pyYellow" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#FFD43B"/>
                    <stop offset="100%" style="stop-color:#FFE873"/>
                </linearGradient>
                <linearGradient id="pyBlue" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#5A9BD5"/>
                    <stop offset="100%" style="stop-color:#3776AB"/>
                </linearGradient>
            </defs>
            <path fill="url(#pyBlue)" d="M54.3 0C26.5 0 28.1 12 28.1 12l.1 12.4h26.6v3.7H17.5S0 25.6 0 54c0 28.4 15.2 27.4 15.2 27.4h9.1V68.2s-.5-15.2 15-15.2h25.8s14.5.2 14.5-14V14.5S82.1 0 54.3 0zM39.7 8.4c2.7 0 4.8 2.2 4.8 4.8s-2.2 4.8-4.8 4.8-4.8-2.2-4.8-4.8 2.2-4.8 4.8-4.8z"/>
            <path fill="url(#pyYellow)" d="M55.7 110c27.8 0 26.2-12 26.2-12l-.1-12.4H55.2v-3.7h37.3S110 84.4 110 56c0-28.4-15.2-27.4-15.2-27.4h-9.1v13.2s.5 15.2-15 15.2H44.9s-14.5-.2-14.5 14v24.5s-2.5 14.5 25.3 14.5zm14.6-8.4c-2.7 0-4.8-2.2-4.8-4.8s2.2-4.8 4.8-4.8 4.8 2.2 4.8 4.8-2.2 4.8-4.8 4.8z"/>
        </svg>
        <h1>{title}</h1>
        <span class="subtitle">API Documentation</span>
        <button class="theme-toggle" onclick="toggleTheme()">
            <span id="theme-icon">Toggle Theme</span>
        </button>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
    <script>
        // Theme toggle functionality
        function toggleTheme() {{
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('scalar-theme', newTheme);
        }}

        // Load saved theme
        const savedTheme = localStorage.getItem('scalar-theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);

        // Initialize Scalar
        const configuration = {{
            spec: {{
                content: {schema_json}
            }},
            theme: savedTheme,
            darkMode: savedTheme === 'dark',
            hideModels: false,
            hideDownloadButton: false,
            hiddenClients: [],
            defaultHttpClient: {{
                targetKey: 'python',
                clientKey: 'requests',
            }},
            customCss: `
                .scalar-app {{ font-family: system-ui, -apple-system, sans-serif; }}
            `,
        }};

        const apiReference = document.createElement('div');
        apiReference.id = 'scalar-api-reference';
        document.body.appendChild(apiReference);

        Scalar.createApiReference(apiReference, configuration);
    </script>
</body>
</html>"""


class PythonOrgSwaggerPlugin(SwaggerRenderPlugin):
    """Swagger UI OpenAPI plugin with Python.org theming.

    Serves as an alternative documentation UI at /swagger.
    """

    def __init__(
        self,
        *,
        path: str = "/swagger",
        **kwargs: Any,
    ) -> None:
        """Initialize the Python.org Swagger plugin.

        Args:
            path: URL path for the Swagger UI.
            **kwargs: Additional arguments passed to SwaggerRenderPlugin.
        """
        super().__init__(
            path=path,
            favicon='<link rel="icon" type="image/x-icon" href="/static/images/favicon.ico">',
            **kwargs,
        )


def get_openapi_plugins() -> list[ScalarRenderPlugin | SwaggerRenderPlugin]:
    """Get the configured OpenAPI UI plugins.

    Returns:
        List of OpenAPI UI plugins with Scalar as primary and Swagger as secondary.
    """
    return [
        PythonOrgScalarPlugin(path="/docs"),
        PythonOrgSwaggerPlugin(path="/swagger"),
    ]
