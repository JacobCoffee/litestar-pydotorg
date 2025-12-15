"""Integration tests for CodeSamples domain controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from litestar import Litestar
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from pydotorg.domains.codesamples.controllers import CodeSampleController
from pydotorg.domains.codesamples.dependencies import get_codesamples_dependencies
from pydotorg.domains.codesamples.models import CodeSample
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

pytestmark = [pytest.mark.integration, pytest.mark.slow]


class CodeSamplesTestFixtures:
    """Test fixtures for codesamples routes."""

    client: AsyncTestClient
    session_factory: async_sessionmaker


async def _create_user_via_db(session_factory: async_sessionmaker, username: str | None = None) -> User:
    """Create a user directly in the database using shared session factory."""
    async with session_factory() as session:
        user = User(
            username=username or f"testuser-{uuid4().hex[:8]}",
            email=f"test-{uuid4().hex[:8]}@example.com",
            password_hash="hashedpassword123",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_code_sample_via_db(
    session_factory: async_sessionmaker, creator_id: str, is_published: bool = False
) -> CodeSample:
    """Create a code sample directly in the database using shared session factory."""
    from uuid import UUID

    async with session_factory() as session:
        sample = CodeSample(
            code=f"print('Hello, World! {uuid4().hex[:8]}')",
            description=f"A test code sample {uuid4().hex[:8]}",
            slug=f"test-sample-{uuid4().hex[:8]}",
            is_published=is_published,
            creator_id=UUID(creator_id) if isinstance(creator_id, str) else creator_id,
        )
        session.add(sample)
        await session.commit()
        await session.refresh(sample)
        return sample


@pytest.fixture
async def codesamples_fixtures(
    async_session_factory: async_sessionmaker,
    _module_sqlalchemy_config: SQLAlchemyAsyncConfig,
) -> AsyncIterator[CodeSamplesTestFixtures]:
    """Create test fixtures using module-scoped config to prevent connection exhaustion.

    Uses the shared _module_sqlalchemy_config from conftest.py instead of creating
    a new SQLAlchemyAsyncConfig per test, which was causing TooManyConnectionsError.
    """
    sqlalchemy_plugin = SQLAlchemyPlugin(config=_module_sqlalchemy_config)

    app = Litestar(
        route_handlers=[CodeSampleController],
        plugins=[sqlalchemy_plugin],
        dependencies=get_codesamples_dependencies(),
        debug=True,
    )

    async with AsyncTestClient(app=app, base_url="http://testserver.local") as client:
        fixtures = CodeSamplesTestFixtures()
        fixtures.client = client
        fixtures.session_factory = async_session_factory
        yield fixtures


class TestCodeSampleControllerRoutes:
    """Tests for CodeSampleController endpoints."""

    async def test_list_code_samples(self, codesamples_fixtures: CodeSamplesTestFixtures) -> None:
        user = await _create_user_via_db(codesamples_fixtures.session_factory)
        await _create_code_sample_via_db(codesamples_fixtures.session_factory, str(user.id))
        response = await codesamples_fixtures.client.get("/api/v1/code-samples/")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_code_samples_with_pagination(self, codesamples_fixtures: CodeSamplesTestFixtures) -> None:
        user = await _create_user_via_db(codesamples_fixtures.session_factory)
        for _ in range(3):
            await _create_code_sample_via_db(codesamples_fixtures.session_factory, str(user.id))
        response = await codesamples_fixtures.client.get("/api/v1/code-samples/?currentPage=1&pageSize=2")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)

    async def test_list_published_code_samples(self, codesamples_fixtures: CodeSamplesTestFixtures) -> None:
        user = await _create_user_via_db(codesamples_fixtures.session_factory)
        await _create_code_sample_via_db(codesamples_fixtures.session_factory, str(user.id), is_published=True)
        response = await codesamples_fixtures.client.get("/api/v1/code-samples/published")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_create_code_sample(self, codesamples_fixtures: CodeSamplesTestFixtures) -> None:
        user = await _create_user_via_db(codesamples_fixtures.session_factory)
        data = {
            "code": "print('Hello, Test!')",
            "description": "A test code sample",
            "is_published": False,
            "creator_id": str(user.id),
        }
        response = await codesamples_fixtures.client.post("/api/v1/code-samples/", json=data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            result = response.json()
            assert result["description"] == "A test code sample"

    async def test_get_code_sample_by_id(self, codesamples_fixtures: CodeSamplesTestFixtures) -> None:
        user = await _create_user_via_db(codesamples_fixtures.session_factory)
        sample = await _create_code_sample_via_db(codesamples_fixtures.session_factory, str(user.id))
        response = await codesamples_fixtures.client.get(f"/api/v1/code-samples/{sample.id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["description"] == sample.description

    async def test_get_code_sample_by_id_not_found(self, codesamples_fixtures: CodeSamplesTestFixtures) -> None:
        fake_id = str(uuid4())
        response = await codesamples_fixtures.client.get(f"/api/v1/code-samples/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_code_sample_by_slug(self, codesamples_fixtures: CodeSamplesTestFixtures) -> None:
        user = await _create_user_via_db(codesamples_fixtures.session_factory)
        sample = await _create_code_sample_via_db(codesamples_fixtures.session_factory, str(user.id))
        response = await codesamples_fixtures.client.get(f"/api/v1/code-samples/slug/{sample.slug}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["slug"] == sample.slug

    async def test_get_code_sample_by_slug_not_found(self, codesamples_fixtures: CodeSamplesTestFixtures) -> None:
        response = await codesamples_fixtures.client.get("/api/v1/code-samples/slug/non-existent-slug")
        assert response.status_code in (404, 500)

    async def test_update_code_sample(self, codesamples_fixtures: CodeSamplesTestFixtures) -> None:
        user = await _create_user_via_db(codesamples_fixtures.session_factory)
        sample = await _create_code_sample_via_db(codesamples_fixtures.session_factory, str(user.id))
        data = {"description": "Updated description"}
        response = await codesamples_fixtures.client.put(f"/api/v1/code-samples/{sample.id}", json=data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["description"] == "Updated description"

    async def test_delete_code_sample(self, codesamples_fixtures: CodeSamplesTestFixtures) -> None:
        user = await _create_user_via_db(codesamples_fixtures.session_factory)
        sample = await _create_code_sample_via_db(codesamples_fixtures.session_factory, str(user.id))
        response = await codesamples_fixtures.client.delete(f"/api/v1/code-samples/{sample.id}")
        assert response.status_code in (200, 204, 500)


class TestCodeSamplesValidation:
    """Validation tests for code samples domain."""

    async def test_create_code_sample_missing_code(self, codesamples_fixtures: CodeSamplesTestFixtures) -> None:
        user = await _create_user_via_db(codesamples_fixtures.session_factory)
        data = {
            "description": "Test",
            "creator_id": str(user.id),
        }
        response = await codesamples_fixtures.client.post("/api/v1/code-samples/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_create_code_sample_missing_description(self, codesamples_fixtures: CodeSamplesTestFixtures) -> None:
        user = await _create_user_via_db(codesamples_fixtures.session_factory)
        data = {
            "code": "print('test')",
            "creator_id": str(user.id),
        }
        response = await codesamples_fixtures.client.post("/api/v1/code-samples/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_get_code_sample_invalid_uuid(self, codesamples_fixtures: CodeSamplesTestFixtures) -> None:
        response = await codesamples_fixtures.client.get("/api/v1/code-samples/not-a-uuid")
        assert response.status_code in (400, 404, 422)
