"""Domain modules for pydotorg.

Import all models here to ensure SQLAlchemy mappers are properly initialized
before any cross-module relationships are resolved.
"""

from pydotorg.domains.banners.models import Banner
from pydotorg.domains.blogs.models import BlogEntry, Feed, FeedAggregate, RelatedBlog
from pydotorg.domains.codesamples.models import CodeSample
from pydotorg.domains.community.models import Link, Photo, Post, Video
from pydotorg.domains.downloads.models import OS, PythonVersion, Release, ReleaseFile
from pydotorg.domains.minutes.models import Minutes
from pydotorg.domains.pages.models import ContentType, DocumentFile, Image, Page
from pydotorg.domains.sponsors.models import Sponsor, Sponsorship, SponsorshipStatus
from pydotorg.domains.successstories.models import Story, StoryCategory
from pydotorg.domains.users.models import (
    EmailPrivacy,
    Membership,
    MembershipType,
    SearchVisibility,
    User,
    UserGroup,
    UserGroupType,
)
from pydotorg.domains.work_groups.models import WorkGroup

__all__ = [
    "OS",
    "Banner",
    "BlogEntry",
    "CodeSample",
    "ContentType",
    "DocumentFile",
    "EmailPrivacy",
    "Feed",
    "FeedAggregate",
    "Image",
    "Link",
    "Membership",
    "MembershipType",
    "Minutes",
    "Page",
    "Photo",
    "Post",
    "PythonVersion",
    "RelatedBlog",
    "Release",
    "ReleaseFile",
    "SearchVisibility",
    "Sponsor",
    "Sponsorship",
    "SponsorshipStatus",
    "Story",
    "StoryCategory",
    "User",
    "UserGroup",
    "UserGroupType",
    "Video",
    "WorkGroup",
]
