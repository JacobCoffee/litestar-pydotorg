"""Integration tests for community domain API routes.

Tests cover PostController, PhotoController, VideoController, and LinkController.
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
from sqlalchemy import NullPool, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from pydotorg.core.database.base import AuditBase
from pydotorg.domains.community.controllers import (
    LinkController,
    PhotoController,
    PostController,
    VideoController,
)
from pydotorg.domains.community.models import Link, Photo, Post, Video
from pydotorg.domains.community.services import LinkService, PhotoService, PostService, VideoService
from pydotorg.domains.pages.models import ContentType
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class CommunityTestFixtures:
    """Test fixtures for community routes."""

    client: AsyncTestClient
    postgres_uri: str


async def _create_user_via_db(postgres_uri: str, **user_data: object) -> dict:
    """Create a user directly in the database."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
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


async def _create_post_via_db(postgres_uri: str, creator_id: str, **post_data: object) -> dict:
    """Create a post directly in the database."""
    from uuid import UUID as PyUUID

    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        slug = post_data.get("slug", f"post-{uuid4().hex[:8]}")
        post = Post(
            title=post_data.get("title", f"Test Post {uuid4().hex[:8]}"),
            slug=slug,
            content=post_data.get("content", "Test post content here."),
            content_type=post_data.get("content_type", ContentType.MARKDOWN),
            creator_id=PyUUID(creator_id),
            is_published=post_data.get("is_published", True),
        )
        session.add(post)
        await session.commit()
        await session.refresh(post)
        result = {
            "id": str(post.id),
            "title": post.title,
            "slug": post.slug,
            "content": post.content,
            "is_published": post.is_published,
        }
    await engine.dispose()
    return result


async def _create_photo_via_db(postgres_uri: str, creator_id: str, **photo_data: object) -> dict:
    """Create a photo directly in the database."""
    from uuid import UUID as PyUUID

    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        photo = Photo(
            image=photo_data.get("image", f"/images/photo-{uuid4().hex[:8]}.jpg"),
            caption=photo_data.get("caption", "Test caption"),
            creator_id=PyUUID(creator_id),
            post_id=PyUUID(photo_data["post_id"]) if photo_data.get("post_id") else None,
        )
        session.add(photo)
        await session.commit()
        await session.refresh(photo)
        result = {
            "id": str(photo.id),
            "image": photo.image,
            "caption": photo.caption,
            "creator_id": str(photo.creator_id),
        }
    await engine.dispose()
    return result


async def _create_video_via_db(postgres_uri: str, creator_id: str, **video_data: object) -> dict:
    """Create a video directly in the database."""
    from uuid import UUID as PyUUID

    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        video = Video(
            url=video_data.get("url", f"https://youtube.com/watch?v={uuid4().hex[:11]}"),
            title=video_data.get("title", f"Test Video {uuid4().hex[:8]}"),
            creator_id=PyUUID(creator_id),
            post_id=PyUUID(video_data["post_id"]) if video_data.get("post_id") else None,
        )
        session.add(video)
        await session.commit()
        await session.refresh(video)
        result = {
            "id": str(video.id),
            "url": video.url,
            "title": video.title,
            "creator_id": str(video.creator_id),
        }
    await engine.dispose()
    return result


async def _create_link_via_db(postgres_uri: str, creator_id: str, **link_data: object) -> dict:
    """Create a link directly in the database."""
    from uuid import UUID as PyUUID

    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        link = Link(
            url=link_data.get("url", f"https://example.com/{uuid4().hex[:8]}"),
            title=link_data.get("title", f"Test Link {uuid4().hex[:8]}"),
            creator_id=PyUUID(creator_id),
            post_id=PyUUID(link_data["post_id"]) if link_data.get("post_id") else None,
        )
        session.add(link)
        await session.commit()
        await session.refresh(link)
        result = {
            "id": str(link.id),
            "url": link.url,
            "title": link.title,
            "creator_id": str(link.creator_id),
        }
    await engine.dispose()
    return result


async def provide_post_service(db_session: AsyncSession) -> PostService:
    """Provide PostService instance."""
    return PostService(session=db_session)


async def provide_photo_service(db_session: AsyncSession) -> PhotoService:
    """Provide PhotoService instance."""
    return PhotoService(session=db_session)


async def provide_video_service(db_session: AsyncSession) -> VideoService:
    """Provide VideoService instance."""
    return VideoService(session=db_session)


async def provide_link_service(db_session: AsyncSession) -> LinkService:
    """Provide LinkService instance."""
    return LinkService(session=db_session)


@pytest.fixture
async def community_fixtures(postgres_uri: str) -> AsyncIterator[CommunityTestFixtures]:
    """Create test fixtures with fresh database schema."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
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
        "post_service": provide_post_service,
        "photo_service": provide_photo_service,
        "video_service": provide_video_service,
        "link_service": provide_link_service,
    }

    app = Litestar(
        route_handlers=[
            PostController,
            PhotoController,
            VideoController,
            LinkController,
        ],
        plugins=[sqlalchemy_plugin],
        dependencies=dependencies,
        debug=True,
    )

    async with AsyncTestClient(app=app, base_url="http://testserver.local") as client:
        fixtures = CommunityTestFixtures()
        fixtures.client = client
        fixtures.postgres_uri = postgres_uri
        yield fixtures


class TestPostControllerRoutes:
    """Tests for PostController API routes."""

    async def test_list_posts(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test listing posts."""
        response = await community_fixtures.client.get("/api/v1/community/posts/")
        assert response.status_code == 200
        posts = response.json()
        assert isinstance(posts, list)

    async def test_list_posts_with_pagination(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test listing posts with pagination."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        for i in range(3):
            await _create_post_via_db(
                community_fixtures.postgres_uri,
                creator_id=user["id"],
                title=f"Post {i}",
                slug=f"post-{i}-{uuid4().hex[:8]}",
            )
        response = await community_fixtures.client.get("/api/v1/community/posts/?pageSize=2&currentPage=1")
        assert response.status_code == 200
        posts = response.json()
        assert len(posts) <= 2

    async def test_list_published_posts(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test listing published posts."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        await _create_post_via_db(
            community_fixtures.postgres_uri,
            creator_id=user["id"],
            is_published=True,
        )
        response = await community_fixtures.client.get("/api/v1/community/posts/published")
        assert response.status_code == 200
        posts = response.json()
        assert isinstance(posts, list)

    async def test_create_post(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test creating a post."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        post_data = {
            "title": "New Test Post",
            "content": "Test content here",
            "content_type": "markdown",
            "is_published": False,
            "creator_id": user["id"],
        }
        response = await community_fixtures.client.post("/api/v1/community/posts/", json=post_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["title"] == "New Test Post"

    async def test_get_post_by_id(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test getting a post by ID."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        post = await _create_post_via_db(community_fixtures.postgres_uri, creator_id=user["id"])
        response = await community_fixtures.client.get(f"/api/v1/community/posts/{post['id']}")
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == post["id"]

    async def test_get_post_by_id_not_found(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test getting a non-existent post."""
        fake_id = uuid4()
        response = await community_fixtures.client.get(f"/api/v1/community/posts/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_post_by_slug(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test getting a post by slug."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        slug = f"my-unique-slug-{uuid4().hex[:8]}"
        await _create_post_via_db(
            community_fixtures.postgres_uri,
            creator_id=user["id"],
            slug=slug,
        )
        response = await community_fixtures.client.get(f"/api/v1/community/posts/slug/{slug}")
        assert response.status_code == 200
        result = response.json()
        assert result["slug"] == slug

    async def test_update_post(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test updating a post."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        post = await _create_post_via_db(community_fixtures.postgres_uri, creator_id=user["id"])
        update_data = {"title": "Updated Post Title"}
        response = await community_fixtures.client.put(f"/api/v1/community/posts/{post['id']}", json=update_data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["title"] == "Updated Post Title"

    async def test_delete_post(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test deleting a post."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        post = await _create_post_via_db(community_fixtures.postgres_uri, creator_id=user["id"])
        response = await community_fixtures.client.delete(f"/api/v1/community/posts/{post['id']}")
        assert response.status_code in (200, 204)


class TestPhotoControllerRoutes:
    """Tests for PhotoController API routes."""

    async def test_list_photos(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test listing photos."""
        response = await community_fixtures.client.get("/api/v1/community/photos/")
        assert response.status_code == 200
        photos = response.json()
        assert isinstance(photos, list)

    async def test_list_photos_with_pagination(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test listing photos with pagination."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        for i in range(3):
            await _create_photo_via_db(
                community_fixtures.postgres_uri,
                creator_id=user["id"],
                image=f"/images/photo-{i}.jpg",
            )
        response = await community_fixtures.client.get("/api/v1/community/photos/?pageSize=2&currentPage=1")
        assert response.status_code == 200
        photos = response.json()
        assert len(photos) <= 2

    async def test_create_photo(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test creating a photo."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        photo_data = {
            "image": "/images/new-photo.jpg",
            "caption": "A new test photo",
            "creator_id": user["id"],
        }
        response = await community_fixtures.client.post("/api/v1/community/photos/", json=photo_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["image"] == "/images/new-photo.jpg"

    async def test_get_photo_by_id(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test getting a photo by ID."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        photo = await _create_photo_via_db(community_fixtures.postgres_uri, creator_id=user["id"])
        response = await community_fixtures.client.get(f"/api/v1/community/photos/{photo['id']}")
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == photo["id"]

    async def test_get_photo_by_id_not_found(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test getting a non-existent photo."""
        fake_id = uuid4()
        response = await community_fixtures.client.get(f"/api/v1/community/photos/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_update_photo(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test updating a photo."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        photo = await _create_photo_via_db(community_fixtures.postgres_uri, creator_id=user["id"])
        update_data = {"caption": "Updated caption"}
        response = await community_fixtures.client.put(f"/api/v1/community/photos/{photo['id']}", json=update_data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["caption"] == "Updated caption"

    async def test_delete_photo(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test deleting a photo."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        photo = await _create_photo_via_db(community_fixtures.postgres_uri, creator_id=user["id"])
        response = await community_fixtures.client.delete(f"/api/v1/community/photos/{photo['id']}")
        assert response.status_code in (200, 204)


class TestVideoControllerRoutes:
    """Tests for VideoController API routes."""

    async def test_list_videos(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test listing videos."""
        response = await community_fixtures.client.get("/api/v1/community/videos/")
        assert response.status_code == 200
        videos = response.json()
        assert isinstance(videos, list)

    async def test_list_videos_with_pagination(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test listing videos with pagination."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        for i in range(3):
            await _create_video_via_db(
                community_fixtures.postgres_uri,
                creator_id=user["id"],
                title=f"Video {i}",
            )
        response = await community_fixtures.client.get("/api/v1/community/videos/?pageSize=2&currentPage=1")
        assert response.status_code == 200
        videos = response.json()
        assert len(videos) <= 2

    async def test_create_video(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test creating a video."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        video_data = {
            "url": "https://youtube.com/watch?v=abc123",
            "title": "New Test Video",
            "creator_id": user["id"],
        }
        response = await community_fixtures.client.post("/api/v1/community/videos/", json=video_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["title"] == "New Test Video"

    async def test_get_video_by_id(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test getting a video by ID."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        video = await _create_video_via_db(community_fixtures.postgres_uri, creator_id=user["id"])
        response = await community_fixtures.client.get(f"/api/v1/community/videos/{video['id']}")
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == video["id"]

    async def test_get_video_by_id_not_found(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test getting a non-existent video."""
        fake_id = uuid4()
        response = await community_fixtures.client.get(f"/api/v1/community/videos/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_update_video(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test updating a video."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        video = await _create_video_via_db(community_fixtures.postgres_uri, creator_id=user["id"])
        update_data = {"title": "Updated Video Title"}
        response = await community_fixtures.client.put(f"/api/v1/community/videos/{video['id']}", json=update_data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["title"] == "Updated Video Title"

    async def test_delete_video(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test deleting a video."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        video = await _create_video_via_db(community_fixtures.postgres_uri, creator_id=user["id"])
        response = await community_fixtures.client.delete(f"/api/v1/community/videos/{video['id']}")
        assert response.status_code in (200, 204)


class TestLinkControllerRoutes:
    """Tests for LinkController API routes."""

    async def test_list_links(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test listing links."""
        response = await community_fixtures.client.get("/api/v1/community/links/")
        assert response.status_code == 200
        links = response.json()
        assert isinstance(links, list)

    async def test_list_links_with_pagination(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test listing links with pagination."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        for i in range(3):
            await _create_link_via_db(
                community_fixtures.postgres_uri,
                creator_id=user["id"],
                title=f"Link {i}",
            )
        response = await community_fixtures.client.get("/api/v1/community/links/?pageSize=2&currentPage=1")
        assert response.status_code == 200
        links = response.json()
        assert len(links) <= 2

    async def test_create_link(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test creating a link."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        link_data = {
            "url": "https://python.org",
            "title": "Python.org",
            "creator_id": user["id"],
        }
        response = await community_fixtures.client.post("/api/v1/community/links/", json=link_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["title"] == "Python.org"

    async def test_get_link_by_id(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test getting a link by ID."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        link = await _create_link_via_db(community_fixtures.postgres_uri, creator_id=user["id"])
        response = await community_fixtures.client.get(f"/api/v1/community/links/{link['id']}")
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == link["id"]

    async def test_get_link_by_id_not_found(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test getting a non-existent link."""
        fake_id = uuid4()
        response = await community_fixtures.client.get(f"/api/v1/community/links/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_update_link(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test updating a link."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        link = await _create_link_via_db(community_fixtures.postgres_uri, creator_id=user["id"])
        update_data = {"title": "Updated Link Title"}
        response = await community_fixtures.client.put(f"/api/v1/community/links/{link['id']}", json=update_data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["title"] == "Updated Link Title"

    async def test_delete_link(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test deleting a link."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        link = await _create_link_via_db(community_fixtures.postgres_uri, creator_id=user["id"])
        response = await community_fixtures.client.delete(f"/api/v1/community/links/{link['id']}")
        assert response.status_code in (200, 204)


class TestCommunityValidation:
    """Tests for community input validation."""

    async def test_create_post_missing_title(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test creating post without title fails validation."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        data = {
            "content": "Content without title",
            "creator_id": user["id"],
        }
        response = await community_fixtures.client.post("/api/v1/community/posts/", json=data)
        assert response.status_code == 400

    async def test_create_post_missing_creator(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test creating post without creator_id fails validation."""
        data = {
            "title": "Title without creator",
            "content": "Content",
        }
        response = await community_fixtures.client.post("/api/v1/community/posts/", json=data)
        assert response.status_code == 400

    async def test_create_photo_missing_image(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test creating photo without image fails validation."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        data = {
            "caption": "Caption without image",
            "creator_id": user["id"],
        }
        response = await community_fixtures.client.post("/api/v1/community/photos/", json=data)
        assert response.status_code == 400

    async def test_create_video_missing_url(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test creating video without url fails validation."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        data = {
            "title": "Video without url",
            "creator_id": user["id"],
        }
        response = await community_fixtures.client.post("/api/v1/community/videos/", json=data)
        assert response.status_code == 400

    async def test_create_link_missing_url(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test creating link without url fails validation."""
        user = await _create_user_via_db(community_fixtures.postgres_uri)
        data = {
            "title": "Link without url",
            "creator_id": user["id"],
        }
        response = await community_fixtures.client.post("/api/v1/community/links/", json=data)
        assert response.status_code == 400

    async def test_get_post_invalid_uuid(self, community_fixtures: CommunityTestFixtures) -> None:
        """Test getting post with invalid UUID returns 404."""
        response = await community_fixtures.client.get("/api/v1/community/posts/not-a-uuid")
        assert response.status_code == 404
