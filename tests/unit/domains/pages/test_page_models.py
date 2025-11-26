"""Unit tests for Page models."""

from __future__ import annotations

from uuid import uuid4

from pydotorg.domains.pages.models import ContentType, DocumentFile, Image, Page


class TestContentTypeEnum:
    def test_enum_values(self) -> None:
        assert ContentType.MARKDOWN.value == "markdown"
        assert ContentType.RESTRUCTUREDTEXT.value == "restructuredtext"
        assert ContentType.HTML.value == "html"

    def test_enum_members(self) -> None:
        members = list(ContentType)
        assert len(members) == 3
        assert ContentType.MARKDOWN in members
        assert ContentType.RESTRUCTUREDTEXT in members
        assert ContentType.HTML in members


class TestPageModel:
    def test_create_page(self) -> None:
        page = Page(
            title="Test Page",
            path="/test",
        )
        assert page.title == "Test Page"
        assert page.path == "/test"

    def test_page_with_explicit_defaults(self) -> None:
        page = Page(
            title="Test Page",
            path="/test",
            keywords="",
            description="",
            content="",
            content_type=ContentType.MARKDOWN,
            is_published=True,
            template_name="pages/default.html",
        )
        assert page.keywords == ""
        assert page.description == ""
        assert page.content == ""
        assert page.content_type == ContentType.MARKDOWN
        assert page.is_published is True
        assert page.template_name == "pages/default.html"

    def test_page_with_all_fields(self) -> None:
        page = Page(
            title="About Python",
            keywords="python, programming, language",
            description="Learn about Python programming language",
            path="/about",
            content="# About Python\n\nPython is awesome!",
            content_type=ContentType.MARKDOWN,
            is_published=True,
            template_name="pages/custom.html",
        )
        assert page.title == "About Python"
        assert page.keywords == "python, programming, language"
        assert page.description == "Learn about Python programming language"
        assert page.path == "/about"
        assert page.content == "# About Python\n\nPython is awesome!"
        assert page.content_type == ContentType.MARKDOWN
        assert page.is_published is True
        assert page.template_name == "pages/custom.html"

    def test_page_markdown_content_type(self) -> None:
        page = Page(
            title="Test",
            path="/test",
            content_type=ContentType.MARKDOWN,
        )
        assert page.content_type == ContentType.MARKDOWN

    def test_page_restructuredtext_content_type(self) -> None:
        page = Page(
            title="Test",
            path="/test",
            content_type=ContentType.RESTRUCTUREDTEXT,
        )
        assert page.content_type == ContentType.RESTRUCTUREDTEXT

    def test_page_html_content_type(self) -> None:
        page = Page(
            title="Test",
            path="/test",
            content_type=ContentType.HTML,
        )
        assert page.content_type == ContentType.HTML

    def test_page_unpublished(self) -> None:
        page = Page(
            title="Draft Page",
            path="/draft",
            is_published=False,
        )
        assert page.is_published is False


class TestImageModel:
    def test_create_image(self) -> None:
        page_id = uuid4()
        image = Image(
            page_id=page_id,
            image="/media/images/test.png",
        )
        assert image.page_id == page_id
        assert image.image == "/media/images/test.png"


class TestDocumentFileModel:
    def test_create_document(self) -> None:
        page_id = uuid4()
        doc = DocumentFile(
            page_id=page_id,
            document="/media/documents/test.pdf",
        )
        assert doc.page_id == page_id
        assert doc.document == "/media/documents/test.pdf"
