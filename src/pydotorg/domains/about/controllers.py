"""About domain page controllers."""

from __future__ import annotations

from litestar import Controller, get
from litestar.response import Redirect, Template


class AboutRenderController(Controller):
    """Controller for rendering about page templates."""

    path = "/about"
    include_in_schema = False

    @get("/")
    async def about_index(self) -> Template:
        """Render the main about page."""
        return Template(
            template_name="about/index.html.jinja2",
            context={
                "page_title": "About Python",
            },
        )

    @get("/psf/")
    async def about_psf(self) -> Template:
        """Render the Python Software Foundation page."""
        return Template(
            template_name="about/psf.html.jinja2",
            context={
                "page_title": "Python Software Foundation",
            },
        )

    @get("/governance/")
    async def about_governance(self) -> Template:
        """Render the Python Governance page."""
        return Template(
            template_name="about/governance.html.jinja2",
            context={
                "page_title": "Python Governance",
            },
        )


class PSFRenderController(Controller):
    """Controller for rendering PSF-specific pages at /psf/ route."""

    path = "/psf"
    include_in_schema = False

    @get("/")
    async def psf_index(self) -> Redirect:
        """Redirect /psf/ to /about/psf/."""
        return Redirect(path="/about/psf/")

    @get("/diversity/")
    async def psf_diversity(self) -> Template:
        """Render the PSF Diversity Statement page."""
        return Template(
            template_name="psf/diversity.html.jinja2",
            context={
                "page_title": "Diversity | Python Software Foundation",
            },
        )
