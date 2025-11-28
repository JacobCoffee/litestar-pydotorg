"""Documentation domain page controllers."""

from __future__ import annotations

from typing import Annotated

from litestar import Controller, get
from litestar.params import Parameter
from litestar.response import Redirect, Template


class DocsRenderController(Controller):
    """Controller for documentation HTML pages."""

    path = "/docs"
    include_in_schema = False

    @get("/")
    async def docs_index(
        self,
        version: Annotated[str, Parameter(query="version", default="3.13")] = "3.13",
    ) -> Template:
        """Render the main documentation portal page."""
        available_versions = ["3.13", "3.12", "3.11", "3.10", "3.9", "3.8"]

        if version not in available_versions:
            version = "3.13"

        return Template(
            template_name="docs/index.html.jinja2",
            context={
                "version": version,
                "versions": available_versions,
            },
        )

    @get("/search")
    async def search_redirect(
        self,
        q: Annotated[str, Parameter(query="q")],
        version: Annotated[str, Parameter(query="version", default="3.13")] = "3.13",
    ) -> Redirect:
        """Redirect documentation search to docs.python.org."""
        base_url = f"https://docs.python.org/{version}/search.html"
        return Redirect(path=f"{base_url}?q={q}")
