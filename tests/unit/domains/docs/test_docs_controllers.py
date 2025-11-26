"""Tests for documentation controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from litestar.status_codes import HTTP_200_OK, HTTP_302_FOUND

if TYPE_CHECKING:
    from litestar.testing import TestClient


@pytest.mark.asyncio
async def test_docs_index_default_version(docs_test_client: TestClient) -> None:
    """Test docs index page with default version."""
    response = docs_test_client.get("/docs/")
    assert response.status_code == HTTP_200_OK
    assert b"Python Documentation" in response.content
    assert b"3.13" in response.content


@pytest.mark.asyncio
async def test_docs_index_with_version_param(docs_test_client: TestClient) -> None:
    """Test docs index page with version parameter."""
    response = docs_test_client.get("/docs/?version=3.12")
    assert response.status_code == HTTP_200_OK
    assert b"Python Documentation" in response.content
    assert b"3.12" in response.content


@pytest.mark.asyncio
async def test_docs_search_redirect(docs_test_client: TestClient) -> None:
    """Test docs search redirects to docs.python.org."""
    response = docs_test_client.get("/docs/search?q=asyncio", follow_redirects=False)
    assert response.status_code == HTTP_302_FOUND
    assert "docs.python.org" in response.headers["location"]
    assert "asyncio" in response.headers["location"]


@pytest.mark.asyncio
async def test_docs_search_redirect_with_version(docs_test_client: TestClient) -> None:
    """Test docs search with specific version."""
    response = docs_test_client.get("/docs/search?q=typing&version=3.11", follow_redirects=False)
    assert response.status_code == HTTP_302_FOUND
    assert "docs.python.org/3.11" in response.headers["location"]
    assert "typing" in response.headers["location"]


@pytest.mark.asyncio
async def test_docs_index_invalid_version_defaults_to_latest(docs_test_client: TestClient) -> None:
    """Test docs index with invalid version defaults to 3.13."""
    response = docs_test_client.get("/docs/?version=9.99")
    assert response.status_code == HTTP_200_OK
    assert b"3.13" in response.content
