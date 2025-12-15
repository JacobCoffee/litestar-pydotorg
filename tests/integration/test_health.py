"""Health check endpoint tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from litestar.testing import AsyncTestClient

pytestmark = [pytest.mark.integration, pytest.mark.slow]


@pytest.mark.asyncio
async def test_health_check(client: AsyncTestClient) -> None:
    """Test health endpoint returns database status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["status"] == "healthy"
    assert data[0]["database"] is True
