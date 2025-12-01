"""Tests for about and PSF controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from litestar.status_codes import HTTP_200_OK

if TYPE_CHECKING:
    from litestar.testing import TestClient


class TestAboutRenderController:
    """Tests for AboutRenderController."""

    @pytest.mark.asyncio
    async def test_about_index(self, about_test_client: TestClient) -> None:
        """Test about index page renders correctly."""
        response = about_test_client.get("/about/")
        assert response.status_code == HTTP_200_OK
        assert b"About Python" in response.content

    @pytest.mark.asyncio
    async def test_about_psf_page(self, about_test_client: TestClient) -> None:
        """Test PSF page renders correctly."""
        response = about_test_client.get("/about/psf/")
        assert response.status_code == HTTP_200_OK
        assert b"Python Software Foundation" in response.content

    @pytest.mark.asyncio
    async def test_about_governance_page(self, about_test_client: TestClient) -> None:
        """Test governance page renders correctly."""
        response = about_test_client.get("/about/governance/")
        assert response.status_code == HTTP_200_OK
        assert b"Python Governance" in response.content


class TestPSFRenderController:
    """Tests for PSFRenderController."""

    @pytest.mark.asyncio
    async def test_psf_diversity_page(self, about_test_client: TestClient) -> None:
        """Test PSF diversity page renders correctly."""
        response = about_test_client.get("/psf/diversity/")
        assert response.status_code == HTTP_200_OK
        assert b"Diversity" in response.content
        assert b"Python Software Foundation" in response.content

    @pytest.mark.asyncio
    async def test_psf_diversity_page_contains_key_content(self, about_test_client: TestClient) -> None:
        """Test PSF diversity page contains key content sections."""
        response = about_test_client.get("/psf/diversity/")
        assert response.status_code == HTTP_200_OK

        content = response.content

        assert b"welcome and encourage participation by everyone" in content
        assert b"Our Commitment" in content
        assert b"How We Work Together" in content
        assert b"Be Welcoming" in content
        assert b"Be Considerate" in content
        assert b"Be Respectful" in content
        assert b"Be Careful" in content

    @pytest.mark.asyncio
    async def test_psf_diversity_page_contains_related_links(self, about_test_client: TestClient) -> None:
        """Test PSF diversity page contains related resource links."""
        response = about_test_client.get("/psf/diversity/")
        assert response.status_code == HTTP_200_OK

        content = response.content

        assert b"/community/" in content
        assert b"/about/psf/" in content
        assert b"Code of Conduct" in content

    @pytest.mark.asyncio
    async def test_psf_diversity_page_meta_description(self, about_test_client: TestClient) -> None:
        """Test PSF diversity page has proper meta description."""
        response = about_test_client.get("/psf/diversity/")
        assert response.status_code == HTTP_200_OK

        assert b"welcomes and encourages participation by everyone" in response.content
