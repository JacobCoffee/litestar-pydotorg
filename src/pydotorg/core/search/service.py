"""Meilisearch service for search functionality."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from meilisearch_python_sdk import AsyncClient

from pydotorg.core.search.schemas import IndexedDocument, SearchHit, SearchResult

if TYPE_CHECKING:
    from meilisearch_python_sdk.models.search import SearchResults
    from meilisearch_python_sdk.task import TaskInfo

    from pydotorg.core.search.schemas import SearchQuery

logger = logging.getLogger(__name__)


class SearchService:
    """Service for interacting with Meilisearch."""

    def __init__(self, url: str, api_key: str | None = None, index_prefix: str = "pydotorg_") -> None:
        """Initialize the Meilisearch service.

        Args:
            url: Meilisearch server URL.
            api_key: Optional API key for authentication.
            index_prefix: Prefix for all index names.
        """
        self.url = url
        self.api_key = api_key
        self.index_prefix = index_prefix
        self._client: AsyncClient | None = None

    @property
    def client(self) -> AsyncClient:
        """Get or create the Meilisearch async client."""
        if self._client is None:
            self._client = AsyncClient(self.url, self.api_key)
        return self._client

    async def close(self) -> None:
        """Close the Meilisearch client connection."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _get_index_name(self, index: str) -> str:
        """Get the full index name with prefix.

        Args:
            index: Base index name (jobs, events, blogs, pages).

        Returns:
            Full index name with prefix.
        """
        return f"{self.index_prefix}{index}"

    async def create_index(
        self,
        index: str,
        primary_key: str = "id",
    ) -> TaskInfo:
        """Create a new search index.

        Args:
            index: Base index name.
            primary_key: Primary key field name.

        Returns:
            Task information for the index creation.
        """
        index_name = self._get_index_name(index)
        logger.info(f"Creating index: {index_name}")

        try:
            task = await self.client.create_index(index_name, primary_key=primary_key)
        except Exception:
            logger.exception(f"Failed to create index: {index_name}")
            raise
        else:
            logger.info(f"Index creation task created: {task.task_uid}")
            return task

    async def delete_index(self, index: str) -> TaskInfo:
        """Delete a search index.

        Args:
            index: Base index name.

        Returns:
            Task information for the index deletion.
        """
        index_name = self._get_index_name(index)
        logger.info(f"Deleting index: {index_name}")

        try:
            task = await self.client.delete_index(index_name)
        except Exception:
            logger.exception(f"Failed to delete index: {index_name}")
            raise
        else:
            logger.info(f"Index deletion task created: {task.task_uid}")
            return task

    async def configure_index(
        self,
        index: str,
        searchable_attributes: list[str] | None = None,
        filterable_attributes: list[str] | None = None,
        sortable_attributes: list[str] | None = None,
        ranking_rules: list[str] | None = None,
    ) -> None:
        """Configure index settings.

        Args:
            index: Base index name.
            searchable_attributes: Fields to search in (order matters for ranking).
            filterable_attributes: Fields that can be used in filters.
            sortable_attributes: Fields that can be used for sorting.
            ranking_rules: Custom ranking rules.
        """
        index_name = self._get_index_name(index)
        idx = self.client.index(index_name)

        logger.info(f"Configuring index: {index_name}")

        try:
            if searchable_attributes:
                await idx.update_searchable_attributes(searchable_attributes)

            if filterable_attributes:
                await idx.update_filterable_attributes(filterable_attributes)

            if sortable_attributes:
                await idx.update_sortable_attributes(sortable_attributes)

            if ranking_rules:
                await idx.update_ranking_rules(ranking_rules)

            logger.info(f"Index configured successfully: {index_name}")
        except Exception:
            logger.exception(f"Failed to configure index: {index_name}")
            raise

    async def index_documents(
        self,
        index: str,
        documents: list[IndexedDocument] | list[dict[str, Any]],
        primary_key: str = "id",
    ) -> TaskInfo:
        """Index documents into Meilisearch.

        Args:
            index: Base index name.
            documents: List of documents to index.
            primary_key: Primary key field name.

        Returns:
            Task information for the indexing operation.
        """
        index_name = self._get_index_name(index)
        idx = self.client.index(index_name)

        doc_dicts = []
        for doc in documents:
            if isinstance(doc, IndexedDocument):
                doc_dicts.append(doc.model_dump(mode="json"))
            else:
                doc_dicts.append(doc)

        logger.info(f"Indexing {len(doc_dicts)} documents into {index_name}")

        try:
            task = await idx.add_documents(doc_dicts, primary_key=primary_key)
        except Exception:
            logger.exception(f"Failed to index documents into {index_name}")
            raise
        else:
            logger.info(f"Documents indexed successfully: {task.task_uid}")
            return task

    async def update_documents(
        self,
        index: str,
        documents: list[IndexedDocument] | list[dict[str, Any]],
        primary_key: str = "id",
    ) -> TaskInfo:
        """Update existing documents in Meilisearch.

        Args:
            index: Base index name.
            documents: List of documents to update.
            primary_key: Primary key field name.

        Returns:
            Task information for the update operation.
        """
        index_name = self._get_index_name(index)
        idx = self.client.index(index_name)

        doc_dicts = []
        for doc in documents:
            if isinstance(doc, IndexedDocument):
                doc_dicts.append(doc.model_dump(mode="json"))
            else:
                doc_dicts.append(doc)

        logger.info(f"Updating {len(doc_dicts)} documents in {index_name}")

        try:
            task = await idx.update_documents(doc_dicts, primary_key=primary_key)
        except Exception:
            logger.exception(f"Failed to update documents in {index_name}")
            raise
        else:
            logger.info(f"Documents updated successfully: {task.task_uid}")
            return task

    async def delete_documents(self, index: str, document_ids: list[str]) -> TaskInfo:
        """Delete documents from an index.

        Args:
            index: Base index name.
            document_ids: List of document IDs to delete.

        Returns:
            Task information for the deletion operation.
        """
        index_name = self._get_index_name(index)
        idx = self.client.index(index_name)

        logger.info(f"Deleting {len(document_ids)} documents from {index_name}")

        try:
            task = await idx.delete_documents(document_ids)
        except Exception:
            logger.exception(f"Failed to delete documents from {index_name}")
            raise
        else:
            logger.info(f"Documents deleted successfully: {task.task_uid}")
            return task

    async def clear_index(self, index: str) -> TaskInfo:
        """Clear all documents from an index.

        Args:
            index: Base index name.

        Returns:
            Task information for the clear operation.
        """
        index_name = self._get_index_name(index)
        idx = self.client.index(index_name)

        logger.info(f"Clearing all documents from {index_name}")

        try:
            task = await idx.delete_all_documents()
        except Exception:
            logger.exception(f"Failed to clear index: {index_name}")
            raise
        else:
            logger.info(f"Index cleared successfully: {task.task_uid}")
            return task

    async def is_available(self) -> bool:
        """Check if Meilisearch service is available.

        Returns:
            True if Meilisearch is reachable, False otherwise.
        """
        try:
            await self.client.health()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Meilisearch is not available at {self.url}: {e}")
            return False
        else:
            return True

    async def search(
        self,
        query: SearchQuery,
    ) -> SearchResult:
        """Search across specified indexes.

        Args:
            query: Search query parameters.

        Returns:
            Aggregated search results.
        """
        try:
            if not await self.is_available():
                logger.warning("Meilisearch unavailable, returning empty search results")
                return SearchResult(
                    hits=[],
                    total=0,
                    offset=query.offset,
                    limit=query.limit,
                    processing_time_ms=0,
                    query=query.query,
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to check Meilisearch availability: {e}, returning empty results")
            return SearchResult(
                hits=[],
                total=0,
                offset=query.offset,
                limit=query.limit,
                processing_time_ms=0,
                query=query.query,
            )

        indexes = query.indexes or ["jobs", "events", "blogs", "pages"]

        all_hits: list[SearchHit] = []
        total_results = 0
        max_processing_time = 0

        for index_name in indexes:
            try:
                results = await self._search_single_index(
                    index=index_name,
                    query_str=query.query,
                    filters=query.filters,
                    limit=query.limit,
                    offset=query.offset,
                    attributes_to_retrieve=query.attributes_to_retrieve,
                    attributes_to_highlight=query.attributes_to_highlight,
                )

                hits = self._convert_results_to_hits(results, index_name)
                all_hits.extend(hits)
                total_results += results.estimated_total_hits or 0
                max_processing_time = max(max_processing_time, results.processing_time_ms or 0)

            except Exception:
                logger.exception(f"Failed to search index: {index_name}")
                continue

        all_hits.sort(key=lambda x: x.created or x.modified or "", reverse=True)

        return SearchResult(
            hits=all_hits[: query.limit],
            total=total_results,
            offset=query.offset,
            limit=query.limit,
            processing_time_ms=max_processing_time,
            query=query.query,
        )

    async def _search_single_index(
        self,
        index: str,
        query_str: str,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
        offset: int = 0,
        attributes_to_retrieve: list[str] | None = None,
        attributes_to_highlight: list[str] | None = None,
    ) -> SearchResults:
        """Search a single index.

        Args:
            index: Base index name.
            query_str: Search query string.
            filters: Optional filters to apply.
            limit: Maximum results to return.
            offset: Number of results to skip.
            attributes_to_retrieve: Specific attributes to retrieve.
            attributes_to_highlight: Attributes to highlight.

        Returns:
            Raw Meilisearch search results.
        """
        index_name = self._get_index_name(index)
        idx = self.client.index(index_name)

        filter_str = None
        if filters:
            filter_parts = []
            for key, value in filters.items():
                if isinstance(value, bool):
                    filter_parts.append(f"{key} = {str(value).lower()}")
                elif isinstance(value, str):
                    filter_parts.append(f'{key} = "{value}"')
                else:
                    filter_parts.append(f"{key} = {value}")
            if filter_parts:
                filter_str = " AND ".join(filter_parts)

        logger.debug(
            f"Searching {index_name}: query='{query_str}', filter='{filter_str}', limit={limit}, offset={offset}"
        )

        return await idx.search(
            query_str,
            filter=filter_str,
            limit=limit,
            offset=offset,
            attributes_to_retrieve=attributes_to_retrieve,
            attributes_to_highlight=attributes_to_highlight,
        )

    def _convert_results_to_hits(self, results: SearchResults, index: str) -> list[SearchHit]:
        """Convert Meilisearch results to SearchHit objects.

        Args:
            results: Raw Meilisearch results.
            index: Index name the results came from.

        Returns:
            List of SearchHit objects.
        """
        hits: list[SearchHit] = []

        for hit in results.hits:
            created = hit.get("created")
            if created and isinstance(created, str):
                try:
                    created = datetime.fromisoformat(created)
                except Exception:
                    logger.exception(f"Failed to parse created date: {created}")
                    created = None

            modified = hit.get("modified")
            if modified and isinstance(modified, str):
                try:
                    modified = datetime.fromisoformat(modified)
                except Exception:
                    logger.exception(f"Failed to parse modified date: {modified}")
                    modified = None

            search_hit = SearchHit(
                id=hit.get("id", ""),
                index=index,
                title=hit.get("title", "Untitled"),
                description=hit.get("description"),
                url=hit.get("url", ""),
                content_type=hit.get("content_type", index),
                created=created,
                modified=modified,
                highlight=getattr(hit, "_formatted", None),
                extra={k: v for k, v in hit.items() if k not in SearchHit.model_fields},
            )
            hits.append(search_hit)

        return hits

    async def get_index_stats(self, index: str) -> dict[str, Any]:
        """Get statistics for an index.

        Args:
            index: Base index name.

        Returns:
            Index statistics.
        """
        index_name = self._get_index_name(index)
        idx = self.client.index(index_name)

        try:
            stats = await idx.get_stats()
        except Exception:
            logger.exception(f"Failed to get stats for index: {index_name}")
            raise
        else:
            return {
                "number_of_documents": stats.number_of_documents,
                "is_indexing": stats.is_indexing,
                "field_distribution": stats.field_distribution,
            }
