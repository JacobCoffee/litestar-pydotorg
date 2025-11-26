"""Dependencies for search domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.config import settings
from pydotorg.core.search import SearchService

if TYPE_CHECKING:
    from litestar.datastructures import State


def provide_search_service(state: State) -> SearchService:
    """Provide the search service instance.

    Args:
        state: Application state.

    Returns:
        SearchService instance.
    """
    if "search_service" not in state:
        state["search_service"] = SearchService(
            url=settings.meilisearch_url,
            api_key=settings.meilisearch_api_key,
            index_prefix=settings.meilisearch_index_prefix,
        )
    return state["search_service"]


def get_search_dependencies() -> dict:
    """Get search domain dependencies.

    Returns:
        Dictionary of dependencies.
    """
    return {
        "search_service": provide_search_service,
    }
