"""Success Stories domain API and page controllers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Body, Parameter
from litestar.response import Template

from pydotorg.domains.successstories.schemas import (
    StoryCategoryCreate,
    StoryCategoryRead,
    StoryCategoryUpdate,
    StoryCreate,
    StoryList,
    StoryRead,
    StoryUpdate,
    StoryWithCategory,
)
from pydotorg.domains.successstories.services import StoryCategoryService, StoryService


class StoryCategoryController(Controller):
    """Controller for StoryCategory CRUD operations."""

    path = "/api/v1/success-stories/categories"
    tags = ["Success Stories"]

    @get("/")
    async def list_categories(
        self,
        story_category_service: StoryCategoryService,
        limit_offset: LimitOffset,
    ) -> list[StoryCategoryRead]:
        """List all story categories with pagination."""
        categories, _total = await story_category_service.list_and_count(limit_offset)
        return [StoryCategoryRead.model_validate(category) for category in categories]

    @get("/{category_id:uuid}")
    async def get_category(
        self,
        story_category_service: StoryCategoryService,
        category_id: Annotated[UUID, Parameter(title="Category ID", description="The category ID")],
    ) -> StoryCategoryRead:
        """Get a story category by ID."""
        category = await story_category_service.get(category_id)
        return StoryCategoryRead.model_validate(category)

    @get("/slug/{slug:str}")
    async def get_category_by_slug(
        self,
        story_category_service: StoryCategoryService,
        slug: Annotated[str, Parameter(title="Slug", description="The category slug")],
    ) -> StoryCategoryRead:
        """Get a story category by slug."""
        category = await story_category_service.get_by_slug(slug)
        if not category:
            raise NotFoundException(f"Story category with slug {slug} not found")
        return StoryCategoryRead.model_validate(category)

    @post("/")
    async def create_category(
        self,
        story_category_service: StoryCategoryService,
        data: Annotated[StoryCategoryCreate, Body(title="Story Category", description="Story category to create")],
    ) -> StoryCategoryRead:
        """Create a new story category."""
        category = await story_category_service.create(data.model_dump())
        return StoryCategoryRead.model_validate(category)

    @put("/{category_id:uuid}")
    async def update_category(
        self,
        story_category_service: StoryCategoryService,
        data: Annotated[StoryCategoryUpdate, Body(title="Story Category", description="Story category data to update")],
        category_id: Annotated[UUID, Parameter(title="Category ID", description="The category ID")],
    ) -> StoryCategoryRead:
        """Update a story category."""
        update_data = data.model_dump(exclude_unset=True)
        category = await story_category_service.update(update_data, item_id=category_id)
        return StoryCategoryRead.model_validate(category)

    @delete("/{category_id:uuid}")
    async def delete_category(
        self,
        story_category_service: StoryCategoryService,
        category_id: Annotated[UUID, Parameter(title="Category ID", description="The category ID")],
    ) -> None:
        """Delete a story category."""
        await story_category_service.delete(category_id)


class StoryController(Controller):
    """Controller for Story CRUD operations."""

    path = "/api/v1/success-stories"
    tags = ["Success Stories"]

    @get("/")
    async def list_stories(
        self,
        story_service: StoryService,
        limit_offset: LimitOffset,
    ) -> list[StoryList]:
        """List all stories with pagination."""
        stories, _total = await story_service.list_and_count(limit_offset)
        return [StoryList.model_validate(story) for story in stories]

    @get("/{story_id:uuid}")
    async def get_story(
        self,
        story_service: StoryService,
        story_id: Annotated[UUID, Parameter(title="Story ID", description="The story ID")],
    ) -> StoryWithCategory:
        """Get a story by ID."""
        story = await story_service.get(story_id)
        return StoryWithCategory.model_validate(story)

    @get("/slug/{slug:str}")
    async def get_story_by_slug(
        self,
        story_service: StoryService,
        slug: Annotated[str, Parameter(title="Slug", description="The story slug")],
    ) -> StoryWithCategory:
        """Get a story by slug."""
        story = await story_service.get_by_slug(slug)
        if not story:
            raise NotFoundException(f"Story with slug {slug} not found")
        return StoryWithCategory.model_validate(story)

    @get("/published")
    async def list_published_stories(
        self,
        story_service: StoryService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[StoryList]:
        """List published stories."""
        stories = await story_service.get_published_stories(limit=limit, offset=offset)
        return [StoryList.model_validate(story) for story in stories]

    @get("/featured")
    async def list_featured_stories(
        self,
        story_service: StoryService,
        limit: Annotated[int, Parameter(ge=1, le=100)] = 10,
    ) -> list[StoryList]:
        """List featured stories."""
        stories = await story_service.get_featured_stories(limit=limit)
        return [StoryList.model_validate(story) for story in stories]

    @get("/category/{category_id:uuid}")
    async def list_stories_by_category(
        self,
        story_service: StoryService,
        category_id: Annotated[UUID, Parameter(title="Category ID", description="The category ID")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[StoryList]:
        """List stories by category."""
        stories = await story_service.get_by_category_id(category_id, limit=limit, offset=offset)
        return [StoryList.model_validate(story) for story in stories]

    @post("/")
    async def create_story(
        self,
        story_service: StoryService,
        data: Annotated[StoryCreate, Body(title="Success Story", description="Success story to create")],
    ) -> StoryRead:
        """Create a new story."""
        story = await story_service.create(data.model_dump())
        return StoryRead.model_validate(story)

    @put("/{story_id:uuid}")
    async def update_story(
        self,
        story_service: StoryService,
        data: Annotated[StoryUpdate, Body(title="Success Story", description="Success story data to update")],
        story_id: Annotated[UUID, Parameter(title="Story ID", description="The story ID")],
    ) -> StoryRead:
        """Update a story."""
        update_data = data.model_dump(exclude_unset=True)
        story = await story_service.update(update_data, item_id=story_id)
        return StoryRead.model_validate(story)

    @delete("/{story_id:uuid}")
    async def delete_story(
        self,
        story_service: StoryService,
        story_id: Annotated[UUID, Parameter(title="Story ID", description="The story ID")],
    ) -> None:
        """Delete a story."""
        await story_service.delete(story_id)


class SuccessStoriesPageController(Controller):
    """Controller for success stories HTML pages."""

    path = "/success-stories"
    include_in_schema = False

    @get("/")
    async def stories_index(
        self,
        story_service: StoryService,
        story_category_service: StoryCategoryService,
    ) -> Template:
        """Render the success stories index page."""
        featured_stories = await story_service.get_featured_stories(limit=6)
        stories = await story_service.get_published_stories(limit=50)
        categories, _ = await story_category_service.list_and_count()

        return Template(
            template_name="successstories/index.html.jinja2",
            context={
                "featured_stories": featured_stories,
                "stories": stories,
                "categories": list(categories),
                "page_title": "Success Stories",
            },
        )

    @get("/{slug:str}/")
    async def story_detail(
        self,
        story_service: StoryService,
        slug: str,
    ) -> Template:
        """Render the story detail page."""
        story = await story_service.get_by_slug(slug)
        if not story:
            raise NotFoundException(f"Story with slug {slug} not found")

        related_stories = await story_service.get_related_stories(
            story_id=story.id,
            category_id=story.category_id,
            limit=3,
        )

        return Template(
            template_name="successstories/detail.html.jinja2",
            context={
                "story": story,
                "related_stories": related_stories,
                "page_title": story.name,
            },
        )

    @get("/category/{slug:str}/")
    async def category_stories(
        self,
        story_service: StoryService,
        story_category_service: StoryCategoryService,
        slug: str,
    ) -> Template:
        """Render stories by category."""
        category = await story_category_service.get_by_slug(slug)
        if not category:
            raise NotFoundException(f"Category with slug {slug} not found")

        stories = await story_service.get_by_category_id(category.id, limit=100)

        return Template(
            template_name="successstories/category.html.jinja2",
            context={
                "category": category,
                "stories": stories,
                "page_title": f"Success Stories - {category.name}",
            },
        )
