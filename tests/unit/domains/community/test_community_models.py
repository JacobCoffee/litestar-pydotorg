"""Unit tests for Community models."""

from __future__ import annotations

from uuid import uuid4

from pydotorg.domains.community.models import Link, Photo, Post, Video
from pydotorg.domains.pages.models import ContentType


class TestPostModel:
    def test_create_post(self) -> None:
        creator_id = uuid4()
        post = Post(
            title="Welcome to Python Community",
            slug="welcome-to-python-community",
            content="This is a community post about Python",
            creator_id=creator_id,
        )
        assert post.title == "Welcome to Python Community"
        assert post.slug == "welcome-to-python-community"
        assert post.content == "This is a community post about Python"
        assert post.creator_id == creator_id

    def test_post_explicit_values(self) -> None:
        post = Post(
            title="Test Post",
            slug="test-post",
            content="Test content",
            creator_id=uuid4(),
            content_type=ContentType.MARKDOWN,
            is_published=False,
        )
        assert post.content_type == ContentType.MARKDOWN
        assert post.is_published is False

    def test_post_with_markdown(self) -> None:
        post = Post(
            title="Markdown Post",
            slug="markdown-post",
            content="# Heading\n\nParagraph",
            content_type=ContentType.MARKDOWN,
            creator_id=uuid4(),
        )
        assert post.content_type == ContentType.MARKDOWN

    def test_post_with_restructuredtext(self) -> None:
        post = Post(
            title="RST Post",
            slug="rst-post",
            content="Heading\n=======\n\nParagraph",
            content_type=ContentType.RESTRUCTUREDTEXT,
            creator_id=uuid4(),
        )
        assert post.content_type == ContentType.RESTRUCTUREDTEXT

    def test_post_with_html(self) -> None:
        post = Post(
            title="HTML Post",
            slug="html-post",
            content="<h1>Heading</h1><p>Paragraph</p>",
            content_type=ContentType.HTML,
            creator_id=uuid4(),
        )
        assert post.content_type == ContentType.HTML

    def test_post_published(self) -> None:
        post = Post(
            title="Published Post",
            slug="published-post",
            content="Content",
            creator_id=uuid4(),
            is_published=True,
        )
        assert post.is_published is True


class TestPhotoModel:
    def test_create_photo(self) -> None:
        creator_id = uuid4()
        photo = Photo(
            image="/media/photos/python-meetup.jpg",
            creator_id=creator_id,
        )
        assert photo.image == "/media/photos/python-meetup.jpg"
        assert photo.creator_id == creator_id

    def test_photo_defaults(self) -> None:
        photo = Photo(
            image="/media/photos/test.jpg",
            creator_id=uuid4(),
        )
        assert photo.post_id is None
        assert photo.caption is None

    def test_photo_with_caption(self) -> None:
        photo = Photo(
            image="/media/photos/conference.jpg",
            caption="PyCon 2024 Group Photo",
            creator_id=uuid4(),
        )
        assert photo.caption == "PyCon 2024 Group Photo"

    def test_photo_attached_to_post(self) -> None:
        post_id = uuid4()
        photo = Photo(
            post_id=post_id,
            image="/media/photos/attached.jpg",
            creator_id=uuid4(),
        )
        assert photo.post_id == post_id


class TestVideoModel:
    def test_create_video(self) -> None:
        creator_id = uuid4()
        video = Video(
            url="https://youtube.com/watch?v=123",
            title="Introduction to Python",
            creator_id=creator_id,
        )
        assert video.url == "https://youtube.com/watch?v=123"
        assert video.title == "Introduction to Python"
        assert video.creator_id == creator_id

    def test_video_defaults(self) -> None:
        video = Video(
            url="https://youtube.com/watch?v=456",
            title="Test Video",
            creator_id=uuid4(),
        )
        assert video.post_id is None

    def test_video_attached_to_post(self) -> None:
        post_id = uuid4()
        video = Video(
            post_id=post_id,
            url="https://vimeo.com/123456",
            title="Python Tutorial",
            creator_id=uuid4(),
        )
        assert video.post_id == post_id


class TestLinkModel:
    def test_create_link(self) -> None:
        creator_id = uuid4()
        link = Link(
            url="https://docs.python.org",
            title="Python Documentation",
            creator_id=creator_id,
        )
        assert link.url == "https://docs.python.org"
        assert link.title == "Python Documentation"
        assert link.creator_id == creator_id

    def test_link_defaults(self) -> None:
        link = Link(
            url="https://example.com",
            title="Example Link",
            creator_id=uuid4(),
        )
        assert link.post_id is None

    def test_link_attached_to_post(self) -> None:
        post_id = uuid4()
        link = Link(
            post_id=post_id,
            url="https://python.org",
            title="Python.org",
            creator_id=uuid4(),
        )
        assert link.post_id == post_id
