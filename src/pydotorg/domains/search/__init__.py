"""Search domain for site-wide search functionality."""

from __future__ import annotations

from pydotorg.domains.search.controllers import SearchAPIController, SearchRenderController
from pydotorg.domains.search.dependencies import get_search_dependencies

__all__ = [
    "SearchAPIController",
    "SearchRenderController",
    "get_search_dependencies",
]
