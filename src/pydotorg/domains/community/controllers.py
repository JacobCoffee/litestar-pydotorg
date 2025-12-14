"""Community domain API and page controllers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Body, Parameter
from litestar.response import Template

from pydotorg.domains.community.schemas import (
    LinkCreate,
    LinkRead,
    LinkUpdate,
    PhotoCreate,
    PhotoRead,
    PhotoUpdate,
    PostCreate,
    PostList,
    PostRead,
    PostUpdate,
    PostWithMedia,
    VideoCreate,
    VideoRead,
    VideoUpdate,
)
from pydotorg.domains.community.services import LinkService, PhotoService, PostService, VideoService


class PostController(Controller):
    """Controller for Post CRUD operations."""

    path = "/api/v1/community/posts"
    tags = ["Community"]

    @get("/")
    async def list_posts(
        self,
        post_service: PostService,
        limit_offset: LimitOffset,
    ) -> list[PostList]:
        """List all posts with pagination."""
        posts, _total = await post_service.list_and_count(limit_offset)
        return [PostList.model_validate(post) for post in posts]

    @get("/{post_id:uuid}")
    async def get_post(
        self,
        post_service: PostService,
        post_id: Annotated[UUID, Parameter(title="Post ID", description="The post ID")],
    ) -> PostWithMedia:
        """Get a post by ID."""
        post = await post_service.get(post_id)
        return PostWithMedia.model_validate(post)

    @get("/slug/{slug:str}")
    async def get_post_by_slug(
        self,
        post_service: PostService,
        slug: Annotated[str, Parameter(title="Slug", description="The post slug")],
    ) -> PostWithMedia:
        """Get a post by slug."""
        post = await post_service.get_by_slug(slug)
        return PostWithMedia.model_validate(post)

    @get("/published")
    async def list_published_posts(
        self,
        post_service: PostService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[PostList]:
        """List published posts."""
        posts = await post_service.get_published_posts(limit=limit, offset=offset)
        return [PostList.model_validate(post) for post in posts]

    @post("/")
    async def create_post(
        self,
        post_service: PostService,
        data: Annotated[PostCreate, Body(title="Post", description="Post to create")],
    ) -> PostRead:
        """Create a new post."""
        post = await post_service.create(data.model_dump())
        return PostRead.model_validate(post)

    @put("/{post_id:uuid}")
    async def update_post(
        self,
        post_service: PostService,
        data: Annotated[PostUpdate, Body(title="Post", description="Post data to update")],
        post_id: Annotated[UUID, Parameter(title="Post ID", description="The post ID")],
    ) -> PostRead:
        """Update a post."""
        update_data = data.model_dump(exclude_unset=True)
        post = await post_service.update(post_id, update_data)
        return PostRead.model_validate(post)

    @delete("/{post_id:uuid}")
    async def delete_post(
        self,
        post_service: PostService,
        post_id: Annotated[UUID, Parameter(title="Post ID", description="The post ID")],
    ) -> None:
        """Delete a post."""
        await post_service.delete(post_id)


class PhotoController(Controller):
    """Controller for Photo CRUD operations."""

    path = "/api/v1/community/photos"
    tags = ["Community"]

    @get("/")
    async def list_photos(
        self,
        photo_service: PhotoService,
        limit_offset: LimitOffset,
    ) -> list[PhotoRead]:
        """List all photos with pagination."""
        photos, _total = await photo_service.list_and_count(limit_offset)
        return [PhotoRead.model_validate(photo) for photo in photos]

    @get("/{photo_id:uuid}")
    async def get_photo(
        self,
        photo_service: PhotoService,
        photo_id: Annotated[UUID, Parameter(title="Photo ID", description="The photo ID")],
    ) -> PhotoRead:
        """Get a photo by ID."""
        photo = await photo_service.get(photo_id)
        return PhotoRead.model_validate(photo)

    @post("/")
    async def create_photo(
        self,
        photo_service: PhotoService,
        data: Annotated[PhotoCreate, Body(title="Photo", description="Photo to create")],
    ) -> PhotoRead:
        """Create a new photo."""
        photo = await photo_service.create(data.model_dump())
        return PhotoRead.model_validate(photo)

    @put("/{photo_id:uuid}")
    async def update_photo(
        self,
        photo_service: PhotoService,
        data: Annotated[PhotoUpdate, Body(title="Photo", description="Photo data to update")],
        photo_id: Annotated[UUID, Parameter(title="Photo ID", description="The photo ID")],
    ) -> PhotoRead:
        """Update a photo."""
        update_data = data.model_dump(exclude_unset=True)
        photo = await photo_service.update(photo_id, update_data)
        return PhotoRead.model_validate(photo)

    @delete("/{photo_id:uuid}")
    async def delete_photo(
        self,
        photo_service: PhotoService,
        photo_id: Annotated[UUID, Parameter(title="Photo ID", description="The photo ID")],
    ) -> None:
        """Delete a photo."""
        await photo_service.delete(photo_id)


class VideoController(Controller):
    """Controller for Video CRUD operations."""

    path = "/api/v1/community/videos"
    tags = ["Community"]

    @get("/")
    async def list_videos(
        self,
        video_service: VideoService,
        limit_offset: LimitOffset,
    ) -> list[VideoRead]:
        """List all videos with pagination."""
        videos, _total = await video_service.list_and_count(limit_offset)
        return [VideoRead.model_validate(video) for video in videos]

    @get("/{video_id:uuid}")
    async def get_video(
        self,
        video_service: VideoService,
        video_id: Annotated[UUID, Parameter(title="Video ID", description="The video ID")],
    ) -> VideoRead:
        """Get a video by ID."""
        video = await video_service.get(video_id)
        return VideoRead.model_validate(video)

    @post("/")
    async def create_video(
        self,
        video_service: VideoService,
        data: Annotated[VideoCreate, Body(title="Video", description="Video to create")],
    ) -> VideoRead:
        """Create a new video."""
        video = await video_service.create(data.model_dump())
        return VideoRead.model_validate(video)

    @put("/{video_id:uuid}")
    async def update_video(
        self,
        video_service: VideoService,
        data: Annotated[VideoUpdate, Body(title="Video", description="Video data to update")],
        video_id: Annotated[UUID, Parameter(title="Video ID", description="The video ID")],
    ) -> VideoRead:
        """Update a video."""
        update_data = data.model_dump(exclude_unset=True)
        video = await video_service.update(video_id, update_data)
        return VideoRead.model_validate(video)

    @delete("/{video_id:uuid}")
    async def delete_video(
        self,
        video_service: VideoService,
        video_id: Annotated[UUID, Parameter(title="Video ID", description="The video ID")],
    ) -> None:
        """Delete a video."""
        await video_service.delete(video_id)


class LinkController(Controller):
    """Controller for Link CRUD operations."""

    path = "/api/v1/community/links"
    tags = ["Community"]

    @get("/")
    async def list_links(
        self,
        link_service: LinkService,
        limit_offset: LimitOffset,
    ) -> list[LinkRead]:
        """List all links with pagination."""
        links, _total = await link_service.list_and_count(limit_offset)
        return [LinkRead.model_validate(link) for link in links]

    @get("/{link_id:uuid}")
    async def get_link(
        self,
        link_service: LinkService,
        link_id: Annotated[UUID, Parameter(title="Link ID", description="The link ID")],
    ) -> LinkRead:
        """Get a link by ID."""
        link = await link_service.get(link_id)
        return LinkRead.model_validate(link)

    @post("/")
    async def create_link(
        self,
        link_service: LinkService,
        data: Annotated[LinkCreate, Body(title="Link", description="Link to create")],
    ) -> LinkRead:
        """Create a new link."""
        link = await link_service.create(data.model_dump())
        return LinkRead.model_validate(link)

    @put("/{link_id:uuid}")
    async def update_link(
        self,
        link_service: LinkService,
        data: Annotated[LinkUpdate, Body(title="Link", description="Link data to update")],
        link_id: Annotated[UUID, Parameter(title="Link ID", description="The link ID")],
    ) -> LinkRead:
        """Update a link."""
        update_data = data.model_dump(exclude_unset=True)
        link = await link_service.update(link_id, update_data)
        return LinkRead.model_validate(link)

    @delete("/{link_id:uuid}")
    async def delete_link(
        self,
        link_service: LinkService,
        link_id: Annotated[UUID, Parameter(title="Link ID", description="The link ID")],
    ) -> None:
        """Delete a link."""
        await link_service.delete(link_id)


class CommunityPageController(Controller):
    """Controller for community HTML pages."""

    path = "/community"
    include_in_schema = False

    @get("/")
    async def community_index(
        self,
        post_service: PostService,
    ) -> Template:
        """Render the community index page."""
        posts = await post_service.get_published_posts(limit=20)

        return Template(
            template_name="community/index.html.jinja2",
            context={
                "posts": posts,
                "page_title": "Python Community",
            },
        )

    @get("/posts/")
    async def posts_list(
        self,
        post_service: PostService,
        limit: Annotated[int, Parameter(ge=1, le=100, description="Page size")] = 20,
        offset: Annotated[int, Parameter(ge=0, description="Offset")] = 0,
    ) -> Template:
        """Render the community posts listing page."""
        posts = await post_service.get_published_posts(limit=limit, offset=offset)
        total = await post_service.count_published_posts()
        featured_posts = [p for p in posts if getattr(p, "is_featured", False)]

        return Template(
            template_name="community/posts.html.jinja2",
            context={
                "posts": posts,
                "featured_posts": featured_posts,
                "page_title": "Community Updates | Python Community",
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                },
            },
        )

    @get("/posts/{slug:str}/")
    async def post_detail(
        self,
        post_service: PostService,
        slug: str,
    ) -> Template:
        """Render the community post detail page."""
        post = await post_service.get_by_slug(slug)
        if not post:
            raise NotFoundException(f"Post with slug {slug} not found")

        return Template(
            template_name="community/post_detail.html.jinja2",
            context={
                "post": post,
                "page_title": post.title,
            },
        )

    @get("/diversity/")
    async def community_diversity(self) -> Template:
        """Render the PSF Diversity Statement page."""
        return Template(
            template_name="psf/diversity.html.jinja2",
            context={
                "page_title": "Diversity | Python Software Foundation",
            },
        )

    @get("/workshops/")
    async def community_workshops(self) -> Template:
        """Render the community workshops and user groups page."""
        return Template(
            template_name="community/workshops.html.jinja2",
            context={
                "page_title": "Workshops & User Groups | Python Community",
            },
        )

    @get("/irc/")
    async def community_irc(self) -> Template:
        """Render the IRC channels information page."""
        return Template(
            template_name="community/irc.html.jinja2",
            context={
                "page_title": "IRC Channels | Python Community",
            },
        )

    @get("/forums/")
    async def community_forums(self) -> Template:
        """Render the Python forums page."""
        return Template(
            template_name="community/forums.html.jinja2",
            context={
                "page_title": "Forums & Discussion | Python Community",
            },
        )

    @get("/lists/")
    async def community_lists(self) -> Template:
        """Render the mailing lists directory page."""
        return Template(
            template_name="community/lists.html.jinja2",
            context={
                "page_title": "Mailing Lists | Python Community",
            },
        )


class PSFPageController(Controller):
    """Controller for PSF HTML pages."""

    path = "/psf"
    include_in_schema = False

    @get("/membership/")
    async def psf_membership(self) -> Template:
        """Render the PSF membership page."""
        return Template(
            template_name="psf/membership.html.jinja2",
            context={
                "page_title": "Membership | Python Software Foundation",
            },
        )

    @get("/about/")
    async def psf_about(self) -> Template:
        """Render the About PSF page."""
        return Template(
            template_name="psf/about.html.jinja2",
            context={
                "page_title": "About | Python Software Foundation",
            },
        )

    @get("/conduct/")
    async def psf_conduct(self) -> Template:
        """Render the Code of Conduct page."""
        return Template(
            template_name="psf/conduct.html.jinja2",
            context={
                "page_title": "Code of Conduct | Python Software Foundation",
            },
        )

    @get("/get-involved/")
    async def psf_get_involved(self) -> Template:
        """Render the Get Involved page."""
        return Template(
            template_name="psf/get-involved.html.jinja2",
            context={
                "page_title": "Get Involved | Python Software Foundation",
            },
        )
