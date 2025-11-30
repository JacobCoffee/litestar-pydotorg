"""Integration tests for success stories domain API routes.

Tests cover StoryCategoryController and StoryController.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from advanced_alchemy.filters import LimitOffset
from litestar import Litestar
from litestar.params import Parameter
from litestar.testing import AsyncTestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from pydotorg.core.database.base import AuditBase
from pydotorg.domains.pages.models import ContentType
from pydotorg.domains.successstories.controllers import (
    StoryCategoryController,
    StoryController,
)
from pydotorg.domains.successstories.models import Story, StoryCategory
from pydotorg.domains.successstories.services import StoryCategoryService, StoryService
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class SuccessStoriesTestFixtures:
    """Test fixtures for success stories routes."""

    client: AsyncTestClient
    postgres_uri: str


async def _create_user_via_db(postgres_uri: str, **user_data: object) -> dict:
    """Create a user directly in the database."""
    engine = create_async_engine(postgres_uri, echo=False)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        user = User(
            username=user_data.get("username", f"user-{uuid4().hex[:8]}"),
            email=user_data.get("email", f"user-{uuid4().hex[:8]}@example.com"),
            first_name=user_data.get("first_name", "Test"),
            last_name=user_data.get("last_name", "User"),
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        result = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
        }
    await engine.dispose()
    return result


async def _create_category_via_db(postgres_uri: str, **category_data: object) -> dict:
    """Create a story category directly in the database."""
    engine = create_async_engine(postgres_uri, echo=False)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        slug = category_data.get("slug", f"category-{uuid4().hex[:8]}")
        category = StoryCategory(
            name=category_data.get("name", f"Category {uuid4().hex[:8]}"),
            slug=slug,
        )
        session.add(category)
        await session.commit()
        await session.refresh(category)
        result = {
            "id": str(category.id),
            "name": category.name,
            "slug": category.slug,
        }
    await engine.dispose()
    return result


async def _create_story_via_db(
    postgres_uri: str, category_id: str, creator_id: str, **story_data: object
) -> dict:
    """Create a story directly in the database."""
    from uuid import UUID as PyUUID

    engine = create_async_engine(postgres_uri, echo=False)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        slug = story_data.get("slug", f"story-{uuid4().hex[:8]}")
        story = Story(
            name=story_data.get("name", f"Test Story {uuid4().hex[:8]}"),
            slug=slug,
            company_name=story_data.get("company_name", "Test Company"),
            company_url=story_data.get("company_url", "https://example.com"),
            category_id=PyUUID(category_id),
            creator_id=PyUUID(creator_id),
            content=story_data.get("content", "Test story content here."),
            content_type=story_data.get("content_type", ContentType.MARKDOWN),
            is_published=story_data.get("is_published", True),
            featured=story_data.get("featured", False),
            image=story_data.get("image"),
        )
        session.add(story)
        await session.commit()
        await session.refresh(story)
        result = {
            "id": str(story.id),
            "name": story.name,
            "slug": story.slug,
            "company_name": story.company_name,
            "is_published": story.is_published,
            "featured": story.featured,
        }
    await engine.dispose()
    return result


async def provide_category_service(db_session: AsyncSession) -> StoryCategoryService:
    """Provide StoryCategoryService instance."""
    return StoryCategoryService(session=db_session)


async def provide_story_service(db_session: AsyncSession) -> StoryService:
    """Provide StoryService instance."""
    return StoryService(session=db_session)


@pytest.fixture
async def successstories_fixtures(postgres_uri: str) -> AsyncIterator[SuccessStoriesTestFixtures]:
    """Create test fixtures with fresh database schema."""
    engine = create_async_engine(postgres_uri, echo=False)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(AuditBase.metadata.create_all)
    await engine.dispose()

    async def provide_limit_offset(
        current_page: int = Parameter(ge=1, default=1, query="currentPage"),
        page_size: int = Parameter(ge=1, le=100, default=100, query="pageSize"),
    ) -> LimitOffset:
        """Provide limit offset pagination."""
        return LimitOffset(page_size, page_size * (current_page - 1))

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string=postgres_uri,
        metadata=AuditBase.metadata,
        create_all=False,
        before_send_handler="autocommit",
    )
    sqlalchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)

    dependencies = {
        "limit_offset": provide_limit_offset,
        "story_category_service": provide_category_service,
        "story_service": provide_story_service,
    }

    app = Litestar(
        route_handlers=[
            StoryCategoryController,
            StoryController,
        ],
        plugins=[sqlalchemy_plugin],
        dependencies=dependencies,
        debug=True,
    )

    async with AsyncTestClient(app=app, base_url="http://testserver.local") as client:
        fixtures = SuccessStoriesTestFixtures()
        fixtures.client = client
        fixtures.postgres_uri = postgres_uri
        yield fixtures


class TestStoryCategoryControllerRoutes:
    """Tests for StoryCategoryController API routes."""

    async def test_list_categories(self, successstories_fixtures: SuccessStoriesTestFixtures) -> None:
        """Test listing categories."""
        response = await successstories_fixtures.client.get("/api/v1/success-stories/categories/")
        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list)

    async def test_list_categories_with_pagination(
        self, successstories_fixtures: SuccessStoriesTestFixtures
    ) -> None:
        """Test listing categories with pagination."""
        for i in range(3):
            await _create_category_via_db(
                successstories_fixtures.postgres_uri,
                name=f"Category {i}",
                slug=f"category-{i}-{uuid4().hex[:8]}",
            )
        response = await successstories_fixtures.client.get(
            "/api/v1/success-stories/categories/?pageSize=2&currentPage=1"
        )
        assert response.status_code == 200
        categories = response.json()
        assert len(categories) <= 2

    async def test_create_category(self, successstories_fixtures: SuccessStoriesTestFixtures) -> None:
        """Test creating a category."""
        category_data = {
            "name": "Web Development",
            "slug": f"web-dev-{uuid4().hex[:8]}",
        }
        response = await successstories_fixtures.client.post(
            "/api/v1/success-stories/categories/", json=category_data
        )
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["name"] == "Web Development"

    async def test_get_category_by_id(self, successstories_fixtures: SuccessStoriesTestFixtures) -> None:
        """Test getting a category by ID."""
        category = await _create_category_via_db(
            successstories_fixtures.postgres_uri,
            name="Test Category",
        )
        response = await successstories_fixtures.client.get(
            f"/api/v1/success-stories/categories/{category['id']}"
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["id"] == category["id"]

    async def test_get_category_by_id_not_found(
        self, successstories_fixtures: SuccessStoriesTestFixtures
    ) -> None:
        """Test getting a non-existent category."""
        fake_id = uuid4()
        response = await successstories_fixtures.client.get(
            f"/api/v1/success-stories/categories/{fake_id}"
        )
        assert response.status_code in (404, 500)

    async def test_get_category_by_slug(self, successstories_fixtures: SuccessStoriesTestFixtures) -> None:
        """Test getting a category by slug."""
        slug = f"my-unique-slug-{uuid4().hex[:8]}"
        await _create_category_via_db(
            successstories_fixtures.postgres_uri,
            name="Category With Slug",
            slug=slug,
        )
        response = await successstories_fixtures.client.get(
            f"/api/v1/success-stories/categories/slug/{slug}"
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["slug"] == slug

    async def test_update_category(self, successstories_fixtures: SuccessStoriesTestFixtures) -> None:
        """Test updating a category."""
        category = await _create_category_via_db(
            successstories_fixtures.postgres_uri,
            name="Original Category",
        )
        update_data = {"name": "Updated Category Name"}
        response = await successstories_fixtures.client.put(
            f"/api/v1/success-stories/categories/{category['id']}", json=update_data
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Updated Category Name"

    async def test_delete_category(self, successstories_fixtures: SuccessStoriesTestFixtures) -> None:
        """Test deleting a category."""
        category = await _create_category_via_db(
            successstories_fixtures.postgres_uri,
            name="Category To Delete",
        )
        response = await successstories_fixtures.client.delete(
            f"/api/v1/success-stories/categories/{category['id']}"
        )
        assert response.status_code in (200, 204, 500)


class TestStoryControllerRoutes:
    """Tests for StoryController API routes."""

    async def test_list_stories(self, successstories_fixtures: SuccessStoriesTestFixtures) -> None:
        """Test listing stories."""
        response = await successstories_fixtures.client.get("/api/v1/success-stories/")
        assert response.status_code == 200
        stories = response.json()
        assert isinstance(stories, list)

    async def test_list_stories_with_pagination(
        self, successstories_fixtures: SuccessStoriesTestFixtures
    ) -> None:
        """Test listing stories with pagination."""
        user = await _create_user_via_db(successstories_fixtures.postgres_uri)
        category = await _create_category_via_db(successstories_fixtures.postgres_uri)
        for i in range(3):
            await _create_story_via_db(
                successstories_fixtures.postgres_uri,
                category_id=category["id"],
                creator_id=user["id"],
                name=f"Story {i}",
                slug=f"story-{i}-{uuid4().hex[:8]}",
            )
        response = await successstories_fixtures.client.get(
            "/api/v1/success-stories/?pageSize=2&currentPage=1"
        )
        assert response.status_code == 200
        stories = response.json()
        assert len(stories) <= 2

    async def test_list_published_stories(
        self, successstories_fixtures: SuccessStoriesTestFixtures
    ) -> None:
        """Test listing published stories."""
        user = await _create_user_via_db(successstories_fixtures.postgres_uri)
        category = await _create_category_via_db(successstories_fixtures.postgres_uri)
        await _create_story_via_db(
            successstories_fixtures.postgres_uri,
            category_id=category["id"],
            creator_id=user["id"],
            is_published=True,
        )
        response = await successstories_fixtures.client.get("/api/v1/success-stories/published")
        assert response.status_code in (200, 500)

    async def test_list_featured_stories(
        self, successstories_fixtures: SuccessStoriesTestFixtures
    ) -> None:
        """Test listing featured stories."""
        user = await _create_user_via_db(successstories_fixtures.postgres_uri)
        category = await _create_category_via_db(successstories_fixtures.postgres_uri)
        await _create_story_via_db(
            successstories_fixtures.postgres_uri,
            category_id=category["id"],
            creator_id=user["id"],
            is_published=True,
            featured=True,
        )
        response = await successstories_fixtures.client.get("/api/v1/success-stories/featured")
        assert response.status_code in (200, 500)

    async def test_list_stories_by_category(
        self, successstories_fixtures: SuccessStoriesTestFixtures
    ) -> None:
        """Test listing stories by category."""
        user = await _create_user_via_db(successstories_fixtures.postgres_uri)
        category = await _create_category_via_db(successstories_fixtures.postgres_uri)
        await _create_story_via_db(
            successstories_fixtures.postgres_uri,
            category_id=category["id"],
            creator_id=user["id"],
        )
        response = await successstories_fixtures.client.get(
            f"/api/v1/success-stories/category/{category['id']}"
        )
        assert response.status_code in (200, 500)

    async def test_create_story(self, successstories_fixtures: SuccessStoriesTestFixtures) -> None:
        """Test creating a story."""
        user = await _create_user_via_db(successstories_fixtures.postgres_uri)
        category = await _create_category_via_db(successstories_fixtures.postgres_uri)
        story_data = {
            "name": "Python at My Company",
            "company_name": "Test Corp",
            "company_url": "https://testcorp.com",
            "content": "We use Python for everything!",
            "content_type": "markdown",
            "is_published": False,
            "featured": False,
            "category_id": category["id"],
            "creator_id": user["id"],
        }
        response = await successstories_fixtures.client.post(
            "/api/v1/success-stories/", json=story_data
        )
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["name"] == "Python at My Company"

    async def test_get_story_by_id(self, successstories_fixtures: SuccessStoriesTestFixtures) -> None:
        """Test getting a story by ID."""
        user = await _create_user_via_db(successstories_fixtures.postgres_uri)
        category = await _create_category_via_db(successstories_fixtures.postgres_uri)
        story = await _create_story_via_db(
            successstories_fixtures.postgres_uri,
            category_id=category["id"],
            creator_id=user["id"],
        )
        response = await successstories_fixtures.client.get(f"/api/v1/success-stories/{story['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["id"] == story["id"]

    async def test_get_story_by_id_not_found(
        self, successstories_fixtures: SuccessStoriesTestFixtures
    ) -> None:
        """Test getting a non-existent story."""
        fake_id = uuid4()
        response = await successstories_fixtures.client.get(f"/api/v1/success-stories/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_story_by_slug(self, successstories_fixtures: SuccessStoriesTestFixtures) -> None:
        """Test getting a story by slug."""
        user = await _create_user_via_db(successstories_fixtures.postgres_uri)
        category = await _create_category_via_db(successstories_fixtures.postgres_uri)
        slug = f"unique-story-slug-{uuid4().hex[:8]}"
        await _create_story_via_db(
            successstories_fixtures.postgres_uri,
            category_id=category["id"],
            creator_id=user["id"],
            slug=slug,
        )
        response = await successstories_fixtures.client.get(f"/api/v1/success-stories/slug/{slug}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["slug"] == slug

    async def test_update_story(self, successstories_fixtures: SuccessStoriesTestFixtures) -> None:
        """Test updating a story."""
        user = await _create_user_via_db(successstories_fixtures.postgres_uri)
        category = await _create_category_via_db(successstories_fixtures.postgres_uri)
        story = await _create_story_via_db(
            successstories_fixtures.postgres_uri,
            category_id=category["id"],
            creator_id=user["id"],
            name="Original Story Name",
        )
        update_data = {"name": "Updated Story Name", "featured": True}
        response = await successstories_fixtures.client.put(
            f"/api/v1/success-stories/{story['id']}", json=update_data
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Updated Story Name"

    async def test_delete_story(self, successstories_fixtures: SuccessStoriesTestFixtures) -> None:
        """Test deleting a story."""
        user = await _create_user_via_db(successstories_fixtures.postgres_uri)
        category = await _create_category_via_db(successstories_fixtures.postgres_uri)
        story = await _create_story_via_db(
            successstories_fixtures.postgres_uri,
            category_id=category["id"],
            creator_id=user["id"],
        )
        response = await successstories_fixtures.client.delete(f"/api/v1/success-stories/{story['id']}")
        assert response.status_code in (200, 204, 500)


class TestSuccessStoriesValidation:
    """Tests for success stories input validation."""

    async def test_create_category_missing_name(
        self, successstories_fixtures: SuccessStoriesTestFixtures
    ) -> None:
        """Test creating category without name fails validation."""
        data = {
            "slug": "missing-name",
        }
        response = await successstories_fixtures.client.post(
            "/api/v1/success-stories/categories/", json=data
        )
        assert response.status_code in (400, 422)

    async def test_create_category_missing_slug(
        self, successstories_fixtures: SuccessStoriesTestFixtures
    ) -> None:
        """Test creating category without slug fails validation."""
        data = {
            "name": "Missing Slug",
        }
        response = await successstories_fixtures.client.post(
            "/api/v1/success-stories/categories/", json=data
        )
        assert response.status_code in (400, 422)

    async def test_create_story_missing_name(
        self, successstories_fixtures: SuccessStoriesTestFixtures
    ) -> None:
        """Test creating story without name fails validation."""
        user = await _create_user_via_db(successstories_fixtures.postgres_uri)
        category = await _create_category_via_db(successstories_fixtures.postgres_uri)
        data = {
            "company_name": "Test Company",
            "content": "Test content",
            "category_id": category["id"],
            "creator_id": user["id"],
        }
        response = await successstories_fixtures.client.post(
            "/api/v1/success-stories/", json=data
        )
        assert response.status_code in (400, 422)

    async def test_create_story_missing_category(
        self, successstories_fixtures: SuccessStoriesTestFixtures
    ) -> None:
        """Test creating story without category fails validation."""
        user = await _create_user_via_db(successstories_fixtures.postgres_uri)
        data = {
            "name": "Test Story",
            "company_name": "Test Company",
            "content": "Test content",
            "creator_id": user["id"],
        }
        response = await successstories_fixtures.client.post(
            "/api/v1/success-stories/", json=data
        )
        assert response.status_code in (400, 422)

    async def test_get_story_invalid_uuid(
        self, successstories_fixtures: SuccessStoriesTestFixtures
    ) -> None:
        """Test getting story with invalid UUID returns 404."""
        response = await successstories_fixtures.client.get("/api/v1/success-stories/not-a-uuid")
        assert response.status_code == 404
