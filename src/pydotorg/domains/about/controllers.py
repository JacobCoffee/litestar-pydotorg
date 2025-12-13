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

    @get("/help/")
    async def about_help(self) -> Template:
        """Render the Help & FAQ page."""
        return Template(
            template_name="about/help.html.jinja2",
            context={
                "page_title": "Help & FAQ",
            },
        )

    @get("/apps/")
    async def about_apps(self) -> Template:
        """Render the Python applications showcase page."""
        return Template(
            template_name="about/apps.html.jinja2",
            context={
                "page_title": "Applications Built with Python",
            },
        )

    @get("/quotes/")
    async def about_quotes(self) -> Template:
        """Render the testimonials page."""
        return Template(
            template_name="about/quotes.html.jinja2",
            context={
                "page_title": "What People Say About Python",
            },
        )

    @get("/gettingstarted/")
    async def about_gettingstarted(self) -> Template:
        """Render the getting started guide."""
        return Template(
            template_name="about/gettingstarted.html.jinja2",
            context={
                "page_title": "Getting Started with Python",
            },
        )

    @get("/legal/")
    async def about_legal(self) -> Template:
        """Render the legal information page."""
        return Template(
            template_name="about/legal.html.jinja2",
            context={
                "page_title": "Legal Information",
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
    async def psf_diversity(self) -> Redirect:
        """Redirect /psf/diversity/ to /community/diversity/."""
        return Redirect(path="/community/diversity/")
