"""Integration test configuration and shared fixtures.

Optimization Strategy:
- Smart TRUNCATE: Only truncate tables that actually have data (~50-80% faster)
- No duplicate TRUNCATE: This conftest handles it, test fixtures don't need to
- Module-scoped base fixtures reused from parent conftest.py

Connection Management:
- All fixtures use session-scoped engine from parent conftest.py
- SQLAlchemyAsyncConfig is session-scoped to prevent connection exhaustion
- NullPool prevents lingering connections

Usage:
    # Tests in this directory automatically get:
    # - integration marker (via pytestmark in test files)
    # - slow marker (for --skip-slow filtering)
    # - auto TRUNCATE before each test (via autouse fixture below)

    # To skip auto-truncate for specific tests:
    @pytest.mark.no_truncate
    async def test_uses_transaction_rollback(...):
        ...
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text

from pydotorg.core.database.base import AuditBase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


@pytest.fixture(autouse=True)
async def _integration_truncate_tables(async_engine: AsyncEngine, request: pytest.FixtureRequest) -> None:
    """Smart auto-truncate: only truncates tables that exist and have data.

    Optimizations applied:
    1. Skip tables that don't exist in schema (handles missing migrations)
    2. Skip tables with no rows (major speedup for sparse test data)
    3. Single CASCADE TRUNCATE for all non-empty tables (batch operation)
    4. Skip for tests marked @pytest.mark.no_truncate

    Performance: ~50-80% faster than naive TRUNCATE all tables approach.
    """
    if "no_truncate" in [marker.name for marker in request.node.iter_markers()]:
        return

    async with async_engine.begin() as conn:
        # Get existing tables in database
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        existing_tables = {row[0] for row in result.fetchall()}

        # Get tables that actually have data (skip empty and non-existent ones)
        tables_with_data = []
        for table in AuditBase.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            result = await conn.execute(text(f'SELECT EXISTS (SELECT 1 FROM "{table.name}" LIMIT 1)'))
            has_data = result.scalar()
            if has_data:
                tables_with_data.append(table.name)

        # Single TRUNCATE for all tables with data
        if tables_with_data:
            tables_str = ", ".join(f'"{t}"' for t in tables_with_data)
            await conn.execute(text(f"TRUNCATE TABLE {tables_str} CASCADE"))
