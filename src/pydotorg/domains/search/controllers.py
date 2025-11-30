"""Search domain controllers."""

from __future__ import annotations

from typing import Annotated

from litestar import Controller, Request, get, post
from litestar.params import Body, Parameter
from litestar.response import Template

from pydotorg.core.search import SearchQuery, SearchResult, SearchService


class SearchAPIController(Controller):
    """API controller for search operations."""

    path = "/api/v1/search"
    tags = ["Search"]

    @post("/")
    async def search_content(
        self,
        search_service: SearchService,
        query: Annotated[SearchQuery, Body(title="Search Query", description="Search query parameters")],
    ) -> SearchResult:
        """Search across all content types.

        Args:
            search_service: Search service instance.
            query: Search query parameters.

        Returns:
            Search results.
        """
        return await search_service.search(query)

    @get("/autocomplete")
    async def autocomplete(
        self,
        search_service: SearchService,
        q: Annotated[str, Parameter(min_length=1, max_length=100, description="Search query")],
        limit: Annotated[int, Parameter(ge=1, le=10)] = 5,
    ) -> list[dict[str, str]]:
        """Get autocomplete suggestions.

        Args:
            search_service: Search service instance.
            q: Search query string.
            limit: Maximum number of suggestions.

        Returns:
            List of autocomplete suggestions.
        """
        query = SearchQuery(
            query=q,
            limit=limit,
            attributes_to_retrieve=["id", "title", "url", "content_type"],
        )

        results = await search_service.search(query)

        return [
            {
                "id": hit.id,
                "title": hit.title,
                "url": hit.url,
                "type": hit.content_type,
            }
            for hit in results.hits
        ]


class SearchRenderController(Controller):
    """Controller for rendering search pages."""

    path = "/search"
    include_in_schema = False

    @get("/")
    async def search_page(
        self,
        request: Request,
        search_service: SearchService,
        q: Annotated[str | None, Parameter(description="Search query")] = None,
        indexes: Annotated[list[str] | None, Parameter(description="Filter by content types")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100)] = 20,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> Template:
        """Render the search page with results.

        Args:
            request: The request object.
            search_service: Search service instance.
            q: Search query string.
            indexes: Optional content type filters.
            limit: Maximum results per page.
            offset: Results offset for pagination.

        Returns:
            Rendered search page template.
        """
        results = None
        if q:
            query = SearchQuery(
                query=q,
                indexes=indexes,
                limit=limit,
                offset=offset,
                attributes_to_highlight=["title", "description", "content"],
            )
            results = await search_service.search(query)

        is_htmx = request.headers.get("hx-request") == "true"

        if is_htmx and results:
            return Template(
                template_name="search/partials/results.html.jinja2",
                context={
                    "results": results,
                    "query": q,
                },
            )

        return Template(
            template_name="search/index.html.jinja2",
            context={
                "results": results,
                "query": q,
                "title": f"Search: {q}" if q else "Search",
                "description": "Search Python.org content",
                "indexes": indexes or [],
                "limit": limit,
                "offset": offset,
            },
        )

    @get("/results")
    async def search_results(
        self,
        request: Request,
        search_service: SearchService,
        q: Annotated[str, Parameter(min_length=1, description="Search query")],
        indexes: Annotated[list[str] | None, Parameter(description="Filter by content types")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100)] = 20,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> Template:
        """Render search results (htmx compatible).

        Args:
            request: The request object.
            search_service: Search service instance.
            q: Search query string.
            indexes: Optional content type filters.
            limit: Maximum results per page.
            offset: Results offset for pagination.

        Returns:
            Rendered search results template.
        """
        query = SearchQuery(
            query=q,
            indexes=indexes,
            limit=limit,
            offset=offset,
            attributes_to_highlight=["title", "description", "content"],
        )

        results = await search_service.search(query)

        is_htmx = request.headers.get("hx-request") == "true"

        if is_htmx:
            return Template(
                template_name="search/partials/results.html.jinja2",
                context={
                    "results": results,
                    "query": q,
                },
            )

        return Template(
            template_name="search/results.html.jinja2",
            context={
                "results": results,
                "query": q,
                "title": f"Search: {q}",
                "description": "Search results",
            },
        )
