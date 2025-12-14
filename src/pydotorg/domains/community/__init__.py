"""Community domain."""

from pydotorg.domains.community.controllers import (
    CommunityPageController,
    LinkController,
    PhotoController,
    PostController,
    PSFPageController,
    VideoController,
)
from pydotorg.domains.community.dependencies import get_community_dependencies
from pydotorg.domains.community.models import Link, Photo, Post, Video
from pydotorg.domains.community.repositories import LinkRepository, PhotoRepository, PostRepository, VideoRepository
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

__all__ = [
    "CommunityPageController",
    "Link",
    "LinkController",
    "LinkCreate",
    "LinkRead",
    "LinkRepository",
    "LinkService",
    "LinkUpdate",
    "PSFPageController",
    "Photo",
    "PhotoController",
    "PhotoCreate",
    "PhotoRead",
    "PhotoRepository",
    "PhotoService",
    "PhotoUpdate",
    "Post",
    "PostController",
    "PostCreate",
    "PostList",
    "PostRead",
    "PostRepository",
    "PostService",
    "PostUpdate",
    "PostWithMedia",
    "Video",
    "VideoController",
    "VideoCreate",
    "VideoRead",
    "VideoRepository",
    "VideoService",
    "VideoUpdate",
    "get_community_dependencies",
]
