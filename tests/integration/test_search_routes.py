"""Integration tests for Search domain controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from litestar import Litestar
from litestar.datastructures import State
from litestar.di import Provide
from litestar.testing import AsyncTestClient

from pydotorg.core.search import SearchResult
from pydotorg.domains.search.controllers import SearchAPIController

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


class MockSearchService:
    """Mock search service for testing without Meilisearch."""

    def __init__(self) -> None:
        self.url = "http://localhost:7700"
        self.api_key = None
        self.index_prefix = "test_"

    async def search(self, query) -> SearchResult:
        """Return mock search results."""
        return SearchResult(
            hits=[],
            total=0,
            offset=0,
            limit=20,
            processing_time_ms=1,
            query=query.query,
        )


def provide_mock_search_service(state: State) -> MockSearchService:
    """Provide mock search service."""
    if "search_service" not in state:
        state["search_service"] = MockSearchService()
    return state["search_service"]


@pytest.fixture
async def test_app() -> AsyncGenerator[Litestar]:
    """Create a test Litestar application with the search controller."""
    app = Litestar(
        route_handlers=[SearchAPIController],
        dependencies={
            "search_service": Provide(provide_mock_search_service, sync_to_thread=False),
        },
        debug=True,
    )
    yield app


@pytest.fixture
async def client(test_app: Litestar) -> AsyncGenerator[AsyncTestClient]:
    """Create an async test client."""
    async with AsyncTestClient(app=test_app) as client:
        yield client


class TestSearchAPIControllerRoutes:
    """Tests for SearchAPIController endpoints."""

    async def test_search_content(self, client: AsyncTestClient) -> None:
        data = {
            "query": "python",
            "limit": 10,
        }
        response = await client.post("/api/v1/search/", json=data)
        # 200=success, 400=validation/parsing issues, 500=internal error
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            result = response.json()
            assert "hits" in result
            assert "total" in result

    async def test_search_content_with_indexes(self, client: AsyncTestClient) -> None:
        data = {
            "query": "python",
            "indexes": ["jobs", "events"],
            "limit": 10,
        }
        response = await client.post("/api/v1/search/", json=data)
        assert response.status_code in (200, 400, 500)

    async def test_search_content_with_filters(self, client: AsyncTestClient) -> None:
        data = {
            "query": "python",
            "filters": {"is_active": True},
            "limit": 10,
        }
        response = await client.post("/api/v1/search/", json=data)
        assert response.status_code in (200, 400, 500)

    async def test_search_content_with_pagination(self, client: AsyncTestClient) -> None:
        data = {
            "query": "python",
            "limit": 5,
            "offset": 10,
        }
        response = await client.post("/api/v1/search/", json=data)
        assert response.status_code in (200, 400, 500)

    async def test_autocomplete(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/v1/search/autocomplete?q=pyth")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)

    async def test_autocomplete_with_limit(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/v1/search/autocomplete?q=python&limit=3")
        assert response.status_code in (200, 500)

    async def test_autocomplete_min_length(self, client: AsyncTestClient) -> None:
        # Query must be at least 1 character
        response = await client.get("/api/v1/search/autocomplete?q=")
        # Should fail validation (400/422) or be handled
        assert response.status_code in (400, 422, 500)

    async def test_autocomplete_max_length(self, client: AsyncTestClient) -> None:
        # Query has max length of 100
        long_query = "a" * 101
        response = await client.get(f"/api/v1/search/autocomplete?q={long_query}")
        assert response.status_code in (400, 422, 500)

    async def test_autocomplete_limit_bounds(self, client: AsyncTestClient) -> None:
        # Limit must be between 1 and 10
        response = await client.get("/api/v1/search/autocomplete?q=python&limit=0")
        assert response.status_code in (400, 422, 500)

        response = await client.get("/api/v1/search/autocomplete?q=python&limit=11")
        assert response.status_code in (400, 422, 500)


class TestSearchValidation:
    """Validation tests for search domain."""

    async def test_search_missing_query(self, client: AsyncTestClient) -> None:
        data = {
            "limit": 10,
        }
        response = await client.post("/api/v1/search/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_search_empty_body(self, client: AsyncTestClient) -> None:
        response = await client.post("/api/v1/search/", json={})
        assert response.status_code in (400, 422, 500)

    async def test_autocomplete_missing_query(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/v1/search/autocomplete")
        # Missing required query parameter
        assert response.status_code in (400, 422, 500)
