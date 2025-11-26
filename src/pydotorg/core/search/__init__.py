"""Search functionality using Meilisearch."""

from __future__ import annotations

from pydotorg.core.search.schemas import IndexedDocument, SearchQuery, SearchResult
from pydotorg.core.search.service import SearchService

__all__ = [
    "IndexedDocument",
    "SearchQuery",
    "SearchResult",
    "SearchService",
]
