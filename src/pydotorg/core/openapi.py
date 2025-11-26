"""Custom OpenAPI UI plugins with Python.org theming."""

from __future__ import annotations

from litestar.openapi.plugins import ScalarRenderPlugin, SwaggerRenderPlugin

# Python.org branded styles for Scalar
PYTHON_SCALAR_STYLE = """
:root {
  --scalar-color-accent: #3776AB;
  --scalar-color-background-1: #FFFFFF;
  --scalar-color-background-2: #F5F5F5;
  --scalar-color-background-3: #E5E5E5;
  --scalar-button-1: #3776AB;
  --scalar-button-1-hover: #2B5B8A;
  --scalar-button-1-color: #FFFFFF;
  --scalar-sidebar-color-active: #3776AB;
}
.dark-mode {
  --scalar-color-accent: #4B8BBE;
  --scalar-color-background-1: #1F2937;
  --scalar-color-background-2: #1A1F2E;
  --scalar-color-background-3: #14161F;
  --scalar-button-1: #4B8BBE;
  --scalar-button-1-hover: #3776AB;
  --scalar-sidebar-color-active: #4B8BBE;
}
"""


def get_openapi_plugins() -> list[ScalarRenderPlugin | SwaggerRenderPlugin]:
    """Get the configured OpenAPI UI plugins.

    Returns:
        List with Scalar at /docs (default) and Swagger at /swagger.
    """
    return [
        ScalarRenderPlugin(
            path="/docs",
            style=PYTHON_SCALAR_STYLE,
        ),
        SwaggerRenderPlugin(path="/swagger"),
    ]
