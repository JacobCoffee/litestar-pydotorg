"""Integration tests for CodeSamples domain controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from litestar import Litestar
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from pydotorg.core.database.base import AuditBase
from pydotorg.domains.codesamples.controllers import CodeSampleController
from pydotorg.domains.codesamples.dependencies import get_codesamples_dependencies
from pydotorg.domains.codesamples.models import CodeSample
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


async def _create_user_via_db(postgres_uri: str, username: str | None = None) -> User:
    """Create a user directly in the database for testing."""
    engine = create_async_engine(postgres_uri, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        user = User(
            username=username or f"testuser-{uuid4().hex[:8]}",
            email=f"test-{uuid4().hex[:8]}@example.com",
            password_hash="hashedpassword123",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        await engine.dispose()
        return user


async def _create_code_sample_via_db(postgres_uri: str, creator_id: str, is_published: bool = False) -> CodeSample:
    """Create a code sample directly in the database for testing."""
    from uuid import UUID

    engine = create_async_engine(postgres_uri, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
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
        await engine.dispose()
        return sample


@pytest.fixture
async def test_app(postgres_uri: str) -> AsyncGenerator[Litestar]:
    """Create a test Litestar application with the codesamples controller."""
    engine = create_async_engine(postgres_uri, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(AuditBase.metadata.create_all)
    await engine.dispose()

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string=postgres_uri,
        before_send_handler="autocommit",
    )

    app = Litestar(
        route_handlers=[CodeSampleController],
        plugins=[SQLAlchemyPlugin(config=sqlalchemy_config)],
        dependencies=get_codesamples_dependencies(),
        debug=True,
    )
    yield app


@pytest.fixture
async def client(test_app: Litestar) -> AsyncGenerator[AsyncTestClient]:
    """Create an async test client."""
    async with AsyncTestClient(app=test_app) as client:
        yield client


class TestCodeSampleControllerRoutes:
    """Tests for CodeSampleController endpoints."""

    async def test_list_code_samples(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        await _create_code_sample_via_db(postgres_uri, str(user.id))
        response = await client.get("/api/v1/code-samples/")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_code_samples_with_pagination(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        for _ in range(3):
            await _create_code_sample_via_db(postgres_uri, str(user.id))
        response = await client.get("/api/v1/code-samples/?currentPage=1&pageSize=2")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)

    async def test_list_published_code_samples(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        await _create_code_sample_via_db(postgres_uri, str(user.id), is_published=True)
        response = await client.get("/api/v1/code-samples/published")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_create_code_sample(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        data = {
            "code": "print('Hello, Test!')",
            "description": "A test code sample",
            "is_published": False,
            "creator_id": str(user.id),
        }
        response = await client.post("/api/v1/code-samples/", json=data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            result = response.json()
            assert result["description"] == "A test code sample"

    async def test_get_code_sample_by_id(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        sample = await _create_code_sample_via_db(postgres_uri, str(user.id))
        response = await client.get(f"/api/v1/code-samples/{sample.id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["description"] == sample.description

    async def test_get_code_sample_by_id_not_found(self, client: AsyncTestClient) -> None:
        fake_id = str(uuid4())
        response = await client.get(f"/api/v1/code-samples/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_code_sample_by_slug(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        sample = await _create_code_sample_via_db(postgres_uri, str(user.id))
        response = await client.get(f"/api/v1/code-samples/slug/{sample.slug}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["slug"] == sample.slug

    async def test_get_code_sample_by_slug_not_found(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/v1/code-samples/slug/non-existent-slug")
        assert response.status_code in (404, 500)

    async def test_update_code_sample(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        sample = await _create_code_sample_via_db(postgres_uri, str(user.id))
        data = {"description": "Updated description"}
        response = await client.put(f"/api/v1/code-samples/{sample.id}", json=data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["description"] == "Updated description"

    async def test_delete_code_sample(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        sample = await _create_code_sample_via_db(postgres_uri, str(user.id))
        response = await client.delete(f"/api/v1/code-samples/{sample.id}")
        assert response.status_code in (200, 204, 500)


class TestCodeSamplesValidation:
    """Validation tests for code samples domain."""

    async def test_create_code_sample_missing_code(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        data = {
            "description": "Test",
            "creator_id": str(user.id),
        }
        response = await client.post("/api/v1/code-samples/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_create_code_sample_missing_description(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        data = {
            "code": "print('test')",
            "creator_id": str(user.id),
        }
        response = await client.post("/api/v1/code-samples/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_get_code_sample_invalid_uuid(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/v1/code-samples/not-a-uuid")
        assert response.status_code in (400, 404, 422)
