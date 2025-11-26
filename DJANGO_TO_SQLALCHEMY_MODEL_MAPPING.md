# Django to SQLAlchemy Model Mapping - Python.org

## Executive Summary

This document provides a comprehensive mapping of all Django models in the pythondotorg repository to their SQLAlchemy equivalents for the Litestar-based reimplementation.

**Total Models Analyzed:** 50+

**Key Insights:**
- Heavy use of Django's `ContentManageable` mixin for tracking creation/modification
- Extensive use of `MarkupField` for content with multiple markup types (markdown, restructuredtext, html)
- Complex polymorphic models in sponsors app
- Custom managers for querysets
- Signal-based workflows for caching and updates
- Use of `ordered_model` for sortable models

---

## Table of Contents

1. [Common Base Classes & Mixins](#common-base-classes--mixins)
2. [Users App](#users-app)
3. [Events App](#events-app)
4. [Downloads App](#downloads-app)
5. [Blogs App](#blogs-app)
6. [Jobs App](#jobs-app)
7. [Pages App](#pages-app)
8. [Community App](#community-app)
9. [Success Stories App](#successstories-app)
10. [Sponsors App](#sponsors-app)
11. [Field Type Mappings](#field-type-mappings)
12. [Relationship Mappings](#relationship-mappings)
13. [Special Handling Required](#special-handling-required)

---

## Common Base Classes & Mixins

### ContentManageable (cms/models.py)

**Django Implementation:**
```python
class ContentManageable(models.Model):
    created = models.DateTimeField(default=timezone.now, blank=True, db_index=True)
    updated = models.DateTimeField(default=timezone.now, blank=True)
    creator = models.ForeignKey(AUTH_USER_MODEL, related_name='%(app_label)s_%(class)s_creator',
                                null=True, blank=True, on_delete=models.CASCADE)
    last_modified_by = models.ForeignKey(AUTH_USER_MODEL,
                                         related_name='%(app_label)s_%(class)s_modified',
                                         null=True, blank=True, on_delete=models.CASCADE)
```

**SQLAlchemy Equivalent:**
```python
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, declared_attr, relationship

class ContentManageableMixin:
    """Mixin for models that track creation and modification."""

    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        index=True,
        nullable=False
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    @declared_attr
    def creator_id(cls) -> Mapped[int | None]:
        return mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    @declared_attr
    def creator(cls) -> Mapped["User | None"]:
        return relationship("User", foreign_keys=[cls.creator_id],
                          back_populates=f"{cls.__tablename__}_created")

    @declared_attr
    def last_modified_by_id(cls) -> Mapped[int | None]:
        return mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    @declared_attr
    def last_modified_by(cls) -> Mapped["User | None"]:
        return relationship("User", foreign_keys=[cls.last_modified_by_id],
                          back_populates=f"{cls.__tablename__}_modified")
```

### NameSlugModel (cms/models.py)

**Django Implementation:**
```python
class NameSlugModel(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
```

**SQLAlchemy Equivalent:**
```python
from sqlalchemy import String, event
from slugify import slugify

class NameSlugMixin:
    """Mixin for models with name and auto-generated slug."""

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)

    def __str__(self) -> str:
        return self.name

# Event listener to auto-generate slug
@event.listens_for(NameSlugMixin, "before_insert", propagate=True)
def generate_slug(mapper, connection, target):
    if not target.slug and target.name:
        target.slug = slugify(target.name)
```

---

## Users App

### User Model

**Location:** `/Users/coffee/git/internal/python/pythondotorg/users/models.py`

**Django Fields:**
```python
class User(AbstractUser):
    bio = MarkupField(blank=True, default_markup_type='markdown', escape_html=True)
    search_visibility = models.IntegerField(choices=SEARCH_CHOICES, default=SEARCH_PUBLIC)
    email_privacy = models.IntegerField(choices=EMAIL_CHOICES, default=EMAIL_NEVER)
    public_profile = models.BooleanField(default=True)
```

**SQLAlchemy Mapping:**
```python
from sqlalchemy import Integer, Boolean, Text, String
from litestar.contrib.sqlalchemy.base import UUIDAuditBase

class User(UUIDAuditBase):
    __tablename__ = "users"

    # From AbstractUser
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    last_name: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    date_joined: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    # Custom fields
    bio_raw: Mapped[str] = mapped_column(Text, default="")
    bio_markup_type: Mapped[str] = mapped_column(String(30), default="markdown")
    bio_rendered: Mapped[str] = mapped_column(Text, default="")  # Cached rendered version

    search_visibility: Mapped[int] = mapped_column(Integer, default=1)  # 1=PUBLIC, 0=PRIVATE
    email_privacy: Mapped[int] = mapped_column(Integer, default=2)  # 0=PUBLIC, 1=PRIVATE, 2=NEVER
    public_profile: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    membership: Mapped["Membership | None"] = relationship("Membership", back_populates="creator",
                                                           uselist=False)
```

**Special Handling:**
- MarkupField needs to be split into 3 fields: `_raw`, `_markup_type`, `_rendered`
- Custom UserManager replaced with SQLAlchemy queries
- Signals (post_save for API key creation) need to be replaced with event listeners

### Membership Model

**Django Fields:**
```python
class Membership(models.Model):
    membership_type = models.IntegerField(default=BASIC, choices=MEMBERSHIP_CHOICES)
    legal_name = models.CharField(max_length=100)
    preferred_name = models.CharField(max_length=100)
    email_address = models.EmailField(max_length=100)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    psf_code_of_conduct = models.BooleanField(blank=True, null=True)
    psf_announcements = models.BooleanField(blank=True, null=True)
    votes = models.BooleanField(default=False)
    last_vote_affirmation = models.DateTimeField(blank=True, null=True)
    created = models.DateTimeField(default=timezone.now, blank=True)
    updated = models.DateTimeField(default=timezone.now, blank=True)
    creator = models.OneToOneField(User, related_name='membership', on_delete=models.CASCADE)
```

**SQLAlchemy Mapping:**
```python
from enum import IntEnum

class MembershipType(IntEnum):
    BASIC = 0
    SUPPORTING = 1
    SPONSOR = 2
    MANAGING = 3
    CONTRIBUTING = 4
    FELLOW = 5

class Membership(UUIDAuditBase):
    __tablename__ = "memberships"

    membership_type: Mapped[int] = mapped_column(Integer, default=MembershipType.BASIC)
    legal_name: Mapped[str] = mapped_column(String(100), nullable=False)
    preferred_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email_address: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), default="")
    region: Mapped[str] = mapped_column(String(100), default="")
    country: Mapped[str] = mapped_column(String(100), default="")
    postal_code: Mapped[str] = mapped_column(String(20), default="")

    psf_code_of_conduct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    psf_announcements: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    votes: Mapped[bool] = mapped_column(Boolean, default=False)
    last_vote_affirmation: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),
                                                                    nullable=True)

    # One-to-One relationship
    creator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                                    unique=True, nullable=True)
    creator: Mapped["User | None"] = relationship("User", back_populates="membership")
```

### UserGroup Model

**SQLAlchemy Mapping:**
```python
class UserGroup(UUIDAuditBase):
    __tablename__ = "user_groups"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(200), nullable=False)
    url_type: Mapped[str] = mapped_column(String(20), nullable=False)  # meetup, distribution list, other
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    trusted: Mapped[bool] = mapped_column(Boolean, default=False)
```

---

## Events App

### Calendar Model

**Location:** `/Users/coffee/git/internal/python/pythondotorg/events/models.py`

**SQLAlchemy Mapping:**
```python
class Calendar(ContentManageableMixin, UUIDAuditBase):
    __tablename__ = "calendars"

    url: Mapped[str | None] = mapped_column(String(200), nullable=True)  # iCal URL
    rss: Mapped[str | None] = mapped_column(String(200), nullable=True)
    embed: Mapped[str | None] = mapped_column(String(200), nullable=True)
    twitter: Mapped[str | None] = mapped_column(String(200), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    categories: Mapped[list["EventCategory"]] = relationship("EventCategory", back_populates="calendar")
    locations: Mapped[list["EventLocation"]] = relationship("EventLocation", back_populates="calendar")
    events: Mapped[list["Event"]] = relationship("Event", back_populates="calendar")
```

### EventCategory Model

**SQLAlchemy Mapping:**
```python
class EventCategory(NameSlugMixin, UUIDAuditBase):
    __tablename__ = "event_categories"

    calendar_id: Mapped[int | None] = mapped_column(ForeignKey("calendars.id", ondelete="CASCADE"),
                                                     nullable=True)
    calendar: Mapped["Calendar | None"] = relationship("Calendar", back_populates="categories")
```

### EventLocation Model

**SQLAlchemy Mapping:**
```python
class EventLocation(UUIDAuditBase):
    __tablename__ = "event_locations"

    calendar_id: Mapped[int | None] = mapped_column(ForeignKey("calendars.id", ondelete="CASCADE"),
                                                     nullable=True)
    calendar: Mapped["Calendar | None"] = relationship("Calendar", back_populates="locations")

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(200), nullable=True)
```

### Event Model

**SQLAlchemy Mapping:**
```python
# Association table for many-to-many relationship
event_categories = Table(
    "event_categories_association",
    Base.metadata,
    Column("event_id", ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("event_categories.id", ondelete="CASCADE"), primary_key=True),
)

class Event(ContentManageableMixin, UUIDAuditBase):
    __tablename__ = "events"

    uid: Mapped[str | None] = mapped_column(String(200), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    calendar_id: Mapped[int] = mapped_column(ForeignKey("calendars.id", ondelete="CASCADE"),
                                             nullable=False)
    calendar: Mapped["Calendar"] = relationship("Calendar", back_populates="events")

    description_raw: Mapped[str] = mapped_column(Text, default="")
    description_markup_type: Mapped[str] = mapped_column(String(30), default="restructuredtext")
    description_rendered: Mapped[str] = mapped_column(Text, default="")

    venue_id: Mapped[int | None] = mapped_column(ForeignKey("event_locations.id", ondelete="CASCADE"),
                                                  nullable=True)
    venue: Mapped["EventLocation | None"] = relationship("EventLocation")

    featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Relationships
    categories: Mapped[list["EventCategory"]] = relationship("EventCategory",
                                                             secondary=event_categories)
    occurring_rule: Mapped["OccurringRule | None"] = relationship("OccurringRule",
                                                                   back_populates="event",
                                                                   uselist=False)
    recurring_rules: Mapped[list["RecurringRule"]] = relationship("RecurringRule",
                                                                   back_populates="event")
```

### OccurringRule Model

**SQLAlchemy Mapping:**
```python
class OccurringRule(UUIDAuditBase):
    __tablename__ = "occurring_rules"

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"),
                                          unique=True, nullable=False)
    event: Mapped["Event"] = relationship("Event", back_populates="occurring_rule")

    dt_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    dt_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    all_day: Mapped[bool] = mapped_column(Boolean, default=False)
```

### RecurringRule Model

**SQLAlchemy Mapping:**
```python
from dateutil.rrule import YEARLY, MONTHLY, WEEKLY, DAILY

class RecurringRule(UUIDAuditBase):
    __tablename__ = "recurring_rules"

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"),
                                          nullable=False)
    event: Mapped["Event"] = relationship("Event", back_populates="recurring_rules")

    begin: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    finish: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    duration_internal: Mapped[timedelta] = mapped_column(Interval,
                                                         default=timedelta(minutes=15))
    duration: Mapped[str] = mapped_column(String(50), default="15 min")
    interval: Mapped[int] = mapped_column(SmallInteger, default=1)
    frequency: Mapped[int] = mapped_column(SmallInteger, default=WEEKLY)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False)
```

### Alarm Model

**SQLAlchemy Mapping:**
```python
class Alarm(ContentManageableMixin, UUIDAuditBase):
    __tablename__ = "alarms"

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"),
                                          nullable=False)
    event: Mapped["Event"] = relationship("Event")

    trigger: Mapped[int] = mapped_column(SmallInteger, default=24)  # hours before event
```

---

## Downloads App

### OS Model

**Location:** `/Users/coffee/git/internal/python/pythondotorg/downloads/models.py`

**SQLAlchemy Mapping:**
```python
class OS(ContentManageableMixin, NameSlugMixin, UUIDAuditBase):
    __tablename__ = "operating_systems"

    # Inherits name and slug from NameSlugMixin
    # Inherits created/updated/creator from ContentManageableMixin

    # Relationships
    releases: Mapped[list["ReleaseFile"]] = relationship("ReleaseFile", back_populates="os")
```

### Release Model

**SQLAlchemy Mapping:**
```python
class ReleaseVersion(IntEnum):
    PYTHON1 = 1
    PYTHON2 = 2
    PYTHON3 = 3
    PYMANAGER = 100

class Release(ContentManageableMixin, NameSlugMixin, UUIDAuditBase):
    __tablename__ = "releases"

    version: Mapped[int] = mapped_column(Integer, default=ReleaseVersion.PYTHON3)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    pre_release: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    show_on_download_page: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    release_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    release_page_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"),
                                                         nullable=True)
    release_page: Mapped["Page | None"] = relationship("Page")

    release_notes_url: Mapped[str] = mapped_column(String(200), default="")

    content_raw: Mapped[str] = mapped_column(Text, default="")
    content_markup_type: Mapped[str] = mapped_column(String(30), default="markdown")
    content_rendered: Mapped[str] = mapped_column(Text, default="")

    # Relationships
    files: Mapped[list["ReleaseFile"]] = relationship("ReleaseFile", back_populates="release")
```

### ReleaseFile Model

**SQLAlchemy Mapping:**
```python
class ReleaseFile(ContentManageableMixin, NameSlugMixin, UUIDAuditBase):
    __tablename__ = "release_files"

    os_id: Mapped[int] = mapped_column(ForeignKey("operating_systems.id", ondelete="CASCADE"),
                                       nullable=False)
    os: Mapped["OS"] = relationship("OS", back_populates="releases")

    release_id: Mapped[int] = mapped_column(ForeignKey("releases.id", ondelete="CASCADE"),
                                            nullable=False)
    release: Mapped["Release"] = relationship("Release", back_populates="files")

    description: Mapped[str] = mapped_column(Text, default="")
    is_source: Mapped[bool] = mapped_column(Boolean, default=False)
    url: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    gpg_signature_file: Mapped[str] = mapped_column(String(200), default="")
    sigstore_signature_file: Mapped[str] = mapped_column(String(200), default="")
    sigstore_cert_file: Mapped[str] = mapped_column(String(200), default="")
    sigstore_bundle_file: Mapped[str] = mapped_column(String(200), default="")
    sbom_spdx2_file: Mapped[str] = mapped_column(String(200), default="")
    md5_sum: Mapped[str] = mapped_column(String(200), default="")
    filesize: Mapped[int] = mapped_column(Integer, default=0)
    download_button: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("os_id", "release_id", "download_button",
                        name="only_one_download_per_os_per_release"),
    )
```

**Special Handling:**
- Signals (post_save) for promoting latest release need SQLAlchemy event listeners
- Fastly cache purging signals need to be replaced
- Complex box updating logic needs service layer

---

## Blogs App

### Feed Model

**Location:** `/Users/coffee/git/internal/python/pythondotorg/blogs/models.py`

**SQLAlchemy Mapping:**
```python
class Feed(UUIDAuditBase):
    __tablename__ = "feeds"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    website_url: Mapped[str] = mapped_column(String(200), nullable=False)
    feed_url: Mapped[str] = mapped_column(String(200), nullable=False)
    last_import: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    entries: Mapped[list["BlogEntry"]] = relationship("BlogEntry", back_populates="feed")
```

### BlogEntry Model

**SQLAlchemy Mapping:**
```python
class BlogEntry(UUIDAuditBase):
    __tablename__ = "blog_entries"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    pub_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(200), nullable=False)

    feed_id: Mapped[int] = mapped_column(ForeignKey("feeds.id", ondelete="CASCADE"),
                                         nullable=False)
    feed: Mapped["Feed"] = relationship("Feed", back_populates="entries")
```

### FeedAggregate Model

**SQLAlchemy Mapping:**
```python
# Association table for many-to-many
feed_aggregate_feeds = Table(
    "feed_aggregate_feeds",
    Base.metadata,
    Column("aggregate_id", ForeignKey("feed_aggregates.id", ondelete="CASCADE"),
           primary_key=True),
    Column("feed_id", ForeignKey("feeds.id", ondelete="CASCADE"), primary_key=True),
)

class FeedAggregate(UUIDAuditBase):
    __tablename__ = "feed_aggregates"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    feeds: Mapped[list["Feed"]] = relationship("Feed", secondary=feed_aggregate_feeds)
```

### RelatedBlog Model

**SQLAlchemy Mapping:**
```python
class RelatedBlog(ContentManageableMixin, UUIDAuditBase):
    __tablename__ = "related_blogs"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    feed_url: Mapped[str] = mapped_column(String(200), nullable=False)
    blog_url: Mapped[str] = mapped_column(String(200), nullable=False)
    blog_name: Mapped[str] = mapped_column(String(200), nullable=False)
    last_entry_published: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                           nullable=False, index=True)
    last_entry_title: Mapped[str] = mapped_column(String(500), nullable=False)
```

---

## Jobs App

### JobType Model

**Location:** `/Users/coffee/git/internal/python/pythondotorg/jobs/models.py`

**SQLAlchemy Mapping:**
```python
class JobType(NameSlugMixin, UUIDAuditBase):
    __tablename__ = "job_types"

    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    jobs: Mapped[list["Job"]] = relationship("Job", secondary="job_job_types",
                                            back_populates="job_types")
```

### JobCategory Model

**SQLAlchemy Mapping:**
```python
class JobCategory(NameSlugMixin, UUIDAuditBase):
    __tablename__ = "job_categories"

    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="category")
```

### Job Model

**SQLAlchemy Mapping:**
```python
# Association table for many-to-many
job_job_types = Table(
    "job_job_types",
    Base.metadata,
    Column("job_id", ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True),
    Column("job_type_id", ForeignKey("job_types.id", ondelete="CASCADE"), primary_key=True),
)

class Job(ContentManageableMixin, UUIDAuditBase):
    __tablename__ = "jobs"

    category_id: Mapped[int] = mapped_column(ForeignKey("job_categories.id", ondelete="CASCADE"),
                                             nullable=False)
    category: Mapped["JobCategory"] = relationship("JobCategory", back_populates="jobs")

    job_types: Mapped[list["JobType"]] = relationship("JobType", secondary=job_job_types,
                                                      back_populates="jobs")

    other_job_type: Mapped[str] = mapped_column(String(100), default="")
    company_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    company_description_raw: Mapped[str] = mapped_column(Text, default="")
    company_description_markup_type: Mapped[str] = mapped_column(String(30),
                                                                  default="restructuredtext")
    company_description_rendered: Mapped[str] = mapped_column(Text, default="")

    job_title: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(100), default="")
    country: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    location_slug: Mapped[str] = mapped_column(String(350), nullable=False)  # Auto-generated
    country_slug: Mapped[str] = mapped_column(String(100), nullable=False)  # Auto-generated

    description_raw: Mapped[str] = mapped_column(Text, nullable=False)
    description_markup_type: Mapped[str] = mapped_column(String(30), default="restructuredtext")
    description_rendered: Mapped[str] = mapped_column(Text, nullable=False)

    requirements_raw: Mapped[str] = mapped_column(Text, nullable=False)
    requirements_markup_type: Mapped[str] = mapped_column(String(30), default="restructuredtext")
    requirements_rendered: Mapped[str] = mapped_column(Text, nullable=False)

    contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    url: Mapped[str | None] = mapped_column(String(200), nullable=True)

    submitted_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"),
                                                         nullable=True)
    submitted_by: Mapped["User | None"] = relationship("User")

    status: Mapped[str] = mapped_column(String(20), default="review", index=True)
    expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    telecommuting: Mapped[bool] = mapped_column(Boolean, default=False)
    agencies: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Relationships
    review_comments: Mapped[list["JobReviewComment"]] = relationship("JobReviewComment",
                                                                     back_populates="job")
```

### JobReviewComment Model

**SQLAlchemy Mapping:**
```python
class JobReviewComment(ContentManageableMixin, UUIDAuditBase):
    __tablename__ = "job_review_comments"

    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"),
                                        nullable=False)
    job: Mapped["Job"] = relationship("Job", back_populates="review_comments")

    comment_raw: Mapped[str] = mapped_column(Text, nullable=False)
    comment_markup_type: Mapped[str] = mapped_column(String(30), default="restructuredtext")
    comment_rendered: Mapped[str] = mapped_column(Text, nullable=False)
```

---

## Pages App

### Page Model

**Location:** `/Users/coffee/git/internal/python/pythondotorg/pages/models.py`

**SQLAlchemy Mapping:**
```python
class Page(ContentManageableMixin, UUIDAuditBase):
    __tablename__ = "pages"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    keywords: Mapped[str] = mapped_column(String(1000), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    path: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)

    content_raw: Mapped[str] = mapped_column(Text, nullable=False)
    content_markup_type: Mapped[str] = mapped_column(String(30), default="restructuredtext")
    content_rendered: Mapped[str] = mapped_column(Text, nullable=False)

    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    content_type: Mapped[str] = mapped_column(String(150), default="text/html")
    template_name: Mapped[str] = mapped_column(String(100), default="")

    # Relationships
    images: Mapped[list["Image"]] = relationship("Image", back_populates="page")
    documents: Mapped[list["DocumentFile"]] = relationship("DocumentFile", back_populates="page")
```

### Image Model

**SQLAlchemy Mapping:**
```python
class Image(UUIDAuditBase):
    __tablename__ = "page_images"

    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"),
                                         nullable=False)
    page: Mapped["Page"] = relationship("Page", back_populates="images")

    image: Mapped[str] = mapped_column(String(400), nullable=False)  # Path to uploaded image
```

### DocumentFile Model

**SQLAlchemy Mapping:**
```python
class DocumentFile(UUIDAuditBase):
    __tablename__ = "page_documents"

    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"),
                                         nullable=False)
    page: Mapped["Page"] = relationship("Page", back_populates="documents")

    document: Mapped[str] = mapped_column(String(500), nullable=False)  # Path to uploaded file
```

---

## Community App

### Post Model

**Location:** `/Users/coffee/git/internal/python/pythondotorg/community/models.py`

**SQLAlchemy Mapping:**
```python
class MediaType(IntEnum):
    TEXT = 1
    PHOTO = 2
    VIDEO = 3
    LINK = 4

class PostStatus(IntEnum):
    PRIVATE = 1
    PUBLIC = 2

class Post(ContentManageableMixin, UUIDAuditBase):
    __tablename__ = "posts"

    title: Mapped[str | None] = mapped_column(String(200), nullable=True)

    content_raw: Mapped[str] = mapped_column(Text, nullable=False)
    content_markup_type: Mapped[str] = mapped_column(String(30), default="html")
    content_rendered: Mapped[str] = mapped_column(Text, nullable=False)

    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_type: Mapped[int] = mapped_column(Integer, default=MediaType.TEXT)
    source_url: Mapped[str] = mapped_column(String(1000), default="")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[int] = mapped_column(Integer, default=PostStatus.PRIVATE, index=True)

    # Relationships
    related_link: Mapped[list["Link"]] = relationship("Link", back_populates="post")
    related_photo: Mapped[list["Photo"]] = relationship("Photo", back_populates="post")
    related_video: Mapped[list["Video"]] = relationship("Video", back_populates="post")
```

### Link Model

**SQLAlchemy Mapping:**
```python
class Link(ContentManageableMixin, UUIDAuditBase):
    __tablename__ = "links"

    post_id: Mapped[int | None] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"),
                                                 nullable=True)
    post: Mapped["Post | None"] = relationship("Post", back_populates="related_link")

    url: Mapped[str] = mapped_column(String(1000), default="")
```

### Photo Model

**SQLAlchemy Mapping:**
```python
class Photo(ContentManageableMixin, UUIDAuditBase):
    __tablename__ = "photos"

    post_id: Mapped[int | None] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"),
                                                 nullable=True)
    post: Mapped["Post | None"] = relationship("Post", back_populates="related_photo")

    image: Mapped[str] = mapped_column(String(400), default="")  # Upload path
    image_url: Mapped[str] = mapped_column(String(1000), default="")
    caption: Mapped[str] = mapped_column(Text, default="")
    click_through_url: Mapped[str] = mapped_column(String(200), default="")
```

### Video Model

**SQLAlchemy Mapping:**
```python
class Video(ContentManageableMixin, UUIDAuditBase):
    __tablename__ = "videos"

    post_id: Mapped[int | None] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"),
                                                 nullable=True)
    post: Mapped["Post | None"] = relationship("Post", back_populates="related_video")

    video_embed: Mapped[str] = mapped_column(Text, default="")
    video_data: Mapped[str] = mapped_column(String(400), default="")  # Upload path
    caption: Mapped[str] = mapped_column(Text, default="")
    click_through_url: Mapped[str] = mapped_column(String(200), default="")
```

---

## Success Stories App

### StoryCategory Model

**Location:** `/Users/coffee/git/internal/python/pythondotorg/successstories/models.py`

**SQLAlchemy Mapping:**
```python
class StoryCategory(NameSlugMixin, UUIDAuditBase):
    __tablename__ = "story_categories"

    # Inherits name and slug from NameSlugMixin

    # Relationships
    success_stories: Mapped[list["Story"]] = relationship("Story", back_populates="category")
```

### Story Model

**SQLAlchemy Mapping:**
```python
class Story(NameSlugMixin, ContentManageableMixin, UUIDAuditBase):
    __tablename__ = "stories"

    company_name: Mapped[str] = mapped_column(String(500), nullable=False)
    company_url: Mapped[str] = mapped_column(String(200), nullable=False)

    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"),
                                                    nullable=True)
    company: Mapped["Company | None"] = relationship("Company", back_populates="success_stories")

    category_id: Mapped[int] = mapped_column(ForeignKey("story_categories.id", ondelete="CASCADE"),
                                             nullable=False)
    category: Mapped["StoryCategory"] = relationship("StoryCategory",
                                                     back_populates="success_stories")

    author: Mapped[str] = mapped_column(String(500), nullable=False)
    author_email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pull_quote: Mapped[str] = mapped_column(Text, nullable=False)

    content_raw: Mapped[str] = mapped_column(Text, nullable=False)
    content_markup_type: Mapped[str] = mapped_column(String(30), default="restructuredtext")
    content_rendered: Mapped[str] = mapped_column(Text, nullable=False)

    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    image: Mapped[str | None] = mapped_column(String(400), nullable=True)  # Upload path

    submitted_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"),
                                                         nullable=True)
    submitted_by: Mapped["User | None"] = relationship("User")
```

---

## Sponsors App

**Location:** `/Users/coffee/git/internal/python/pythondotorg/sponsors/models/`

This is the most complex app with polymorphic models and multiple interdependencies.

### GenericAsset (Polymorphic Base)

**SQLAlchemy Mapping:**
```python
from sqlalchemy.ext.declarative import declared_attr
import uuid

class GenericAsset(UUIDAuditBase):
    __tablename__ = "generic_assets"

    # Polymorphic discriminator
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)

    __mapper_args__ = {
        "polymorphic_on": asset_type,
        "polymorphic_identity": "generic",
    }

    uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4,
                                       nullable=False, unique=True)

    # Generic foreign key pattern - replaced with separate FKs
    sponsor_id: Mapped[int | None] = mapped_column(ForeignKey("sponsors.id", ondelete="CASCADE"),
                                                    nullable=True)
    sponsorship_id: Mapped[int | None] = mapped_column(ForeignKey("sponsorships.id",
                                                                   ondelete="CASCADE"),
                                                       nullable=True)

    internal_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    __table_args__ = (
        CheckConstraint(
            "(sponsor_id IS NOT NULL AND sponsorship_id IS NULL) OR "
            "(sponsor_id IS NULL AND sponsorship_id IS NOT NULL)",
            name="check_one_parent"
        ),
        UniqueConstraint("sponsor_id", "sponsorship_id", "internal_name",
                        name="unique_asset_per_parent"),
    )
```

### ImgAsset (Polymorphic Child)

**SQLAlchemy Mapping:**
```python
class ImgAsset(GenericAsset):
    __tablename__ = "img_assets"

    __mapper_args__ = {
        "polymorphic_identity": "image",
    }

    id: Mapped[int] = mapped_column(ForeignKey("generic_assets.id", ondelete="CASCADE"),
                                    primary_key=True)
    image: Mapped[str | None] = mapped_column(String(400), nullable=True)  # Upload path
```

### TextAsset (Polymorphic Child)

**SQLAlchemy Mapping:**
```python
class TextAsset(GenericAsset):
    __tablename__ = "text_assets"

    __mapper_args__ = {
        "polymorphic_identity": "text",
    }

    id: Mapped[int] = mapped_column(ForeignKey("generic_assets.id", ondelete="CASCADE"),
                                    primary_key=True)
    text: Mapped[str] = mapped_column(Text, default="")
```

### FileAsset (Polymorphic Child)

**SQLAlchemy Mapping:**
```python
class FileAsset(GenericAsset):
    __tablename__ = "file_assets"

    __mapper_args__ = {
        "polymorphic_identity": "file",
    }

    id: Mapped[int] = mapped_column(ForeignKey("generic_assets.id", ondelete="CASCADE"),
                                    primary_key=True)
    file: Mapped[str | None] = mapped_column(String(400), nullable=True)  # Upload path
```

### ResponseAsset (Polymorphic Child)

**SQLAlchemy Mapping:**
```python
class Response(str, Enum):
    YES = "Yes"
    NO = "No"

class ResponseAsset(GenericAsset):
    __tablename__ = "response_assets"

    __mapper_args__ = {
        "polymorphic_identity": "response",
    }

    id: Mapped[int] = mapped_column(ForeignKey("generic_assets.id", ondelete="CASCADE"),
                                    primary_key=True)
    response: Mapped[str | None] = mapped_column(String(32), nullable=True)
```

### Sponsor Model

**SQLAlchemy Mapping:**
```python
from sqlalchemy_utils import CountryType

class Sponsor(ContentManageableMixin, UUIDAuditBase):
    __tablename__ = "sponsors"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    landing_page_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    twitter_handle: Mapped[str | None] = mapped_column(String(32), nullable=True)
    linked_in_page_url: Mapped[str | None] = mapped_column(String(200), nullable=True)

    web_logo: Mapped[str] = mapped_column(String(400), nullable=False)  # Upload path
    print_logo: Mapped[str | None] = mapped_column(String(400), nullable=True)  # Upload path

    primary_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    mailing_address_line_1: Mapped[str] = mapped_column(String(128), nullable=False)
    mailing_address_line_2: Mapped[str] = mapped_column(String(128), default="")
    city: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(64), default="")
    postal_code: Mapped[str] = mapped_column(String(64), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO country code
    country_of_incorporation: Mapped[str | None] = mapped_column(String(2), nullable=True)
    state_of_incorporation: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    contacts: Mapped[list["SponsorContact"]] = relationship("SponsorContact",
                                                           back_populates="sponsor")
    sponsorships: Mapped[list["Sponsorship"]] = relationship("Sponsorship",
                                                             back_populates="sponsor")
    assets: Mapped[list["GenericAsset"]] = relationship("GenericAsset",
                                                        foreign_keys="[GenericAsset.sponsor_id]")
```

### SponsorContact Model

**SQLAlchemy Mapping:**
```python
class SponsorContact(UUIDAuditBase):
    __tablename__ = "sponsor_contacts"

    sponsor_id: Mapped[int] = mapped_column(ForeignKey("sponsors.id", ondelete="CASCADE"),
                                            nullable=False)
    sponsor: Mapped["Sponsor"] = relationship("Sponsor", back_populates="contacts")

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                                 nullable=True)
    user: Mapped["User | None"] = relationship("User")

    primary: Mapped[bool] = mapped_column(Boolean, default=False)
    administrative: Mapped[bool] = mapped_column(Boolean, default=False)
    accounting: Mapped[bool] = mapped_column(Boolean, default=False)
    manager: Mapped[bool] = mapped_column(Boolean, default=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(256), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
```

### SponsorshipPackage Model

**SQLAlchemy Mapping:**
```python
class SponsorshipPackage(UUIDAuditBase):
    __tablename__ = "sponsorship_packages"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    sponsorship_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    advertise: Mapped[bool] = mapped_column(Boolean, default=False)
    logo_dimension: Mapped[int] = mapped_column(Integer, default=175)
    slug: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    allow_a_la_carte: Mapped[bool] = mapped_column(Boolean, default=True)
    order: Mapped[int] = mapped_column(Integer, default=0)  # For ordering

    # Relationships
    benefits: Mapped[list["SponsorshipBenefit"]] = relationship("SponsorshipBenefit",
                                                               secondary="sponsorship_package_benefits")
```

### SponsorshipProgram Model

**SQLAlchemy Mapping:**
```python
class SponsorshipProgram(UUIDAuditBase):
    __tablename__ = "sponsorship_programs"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    benefits: Mapped[list["SponsorshipBenefit"]] = relationship("SponsorshipBenefit",
                                                               back_populates="program")
```

### Sponsorship Model

**SQLAlchemy Mapping:**
```python
class SponsorshipStatus(str, Enum):
    APPLIED = "applied"
    REJECTED = "rejected"
    APPROVED = "approved"
    FINALIZED = "finalized"

class Sponsorship(UUIDAuditBase):
    __tablename__ = "sponsorships"

    submited_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id",
                                                                   ondelete="SET NULL"),
                                                        nullable=True)
    submited_by: Mapped["User | None"] = relationship("User")

    sponsor_id: Mapped[int | None] = mapped_column(ForeignKey("sponsors.id", ondelete="SET NULL"),
                                                    nullable=True)
    sponsor: Mapped["Sponsor | None"] = relationship("Sponsor", back_populates="sponsorships")

    status: Mapped[str] = mapped_column(String(20), default=SponsorshipStatus.APPLIED,
                                       index=True)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)

    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    applied_on: Mapped[date] = mapped_column(Date, default=func.current_date())
    approved_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    rejected_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    finalized_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    for_modified_package: Mapped[bool] = mapped_column(Boolean, default=False)
    level_name_old: Mapped[str] = mapped_column(String(64), default="")

    package_id: Mapped[int | None] = mapped_column(ForeignKey("sponsorship_packages.id",
                                                               ondelete="SET NULL"),
                                                    nullable=True)
    package: Mapped["SponsorshipPackage | None"] = relationship("SponsorshipPackage")

    sponsorship_fee: Mapped[int | None] = mapped_column(Integer, nullable=True)

    overlapped_by_id: Mapped[int | None] = mapped_column(ForeignKey("sponsorships.id",
                                                                     ondelete="SET NULL"),
                                                         nullable=True)
    overlapped_by: Mapped["Sponsorship | None"] = relationship("Sponsorship",
                                                               remote_side="Sponsorship.id")

    renewal: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Relationships
    benefits: Mapped[list["SponsorBenefit"]] = relationship("SponsorBenefit",
                                                           back_populates="sponsorship")
    contract: Mapped["Contract | None"] = relationship("Contract", back_populates="sponsorship",
                                                       uselist=False)
    assets: Mapped[list["GenericAsset"]] = relationship("GenericAsset",
                                                        foreign_keys="[GenericAsset.sponsorship_id]")
```

### SponsorshipBenefit Model

**SQLAlchemy Mapping:**
```python
# Association table
sponsorship_package_benefits = Table(
    "sponsorship_package_benefits",
    Base.metadata,
    Column("package_id", ForeignKey("sponsorship_packages.id", ondelete="CASCADE"),
           primary_key=True),
    Column("benefit_id", ForeignKey("sponsorship_benefits.id", ondelete="CASCADE"),
           primary_key=True),
)

# Association table for legal clauses
sponsorship_benefit_legal_clauses = Table(
    "sponsorship_benefit_legal_clauses",
    Base.metadata,
    Column("benefit_id", ForeignKey("sponsorship_benefits.id", ondelete="CASCADE"),
           primary_key=True),
    Column("clause_id", ForeignKey("legal_clauses.id", ondelete="CASCADE"),
           primary_key=True),
)

# Self-referential many-to-many for conflicts
sponsorship_benefit_conflicts = Table(
    "sponsorship_benefit_conflicts",
    Base.metadata,
    Column("benefit_id", ForeignKey("sponsorship_benefits.id", ondelete="CASCADE"),
           primary_key=True),
    Column("conflicting_benefit_id", ForeignKey("sponsorship_benefits.id", ondelete="CASCADE"),
           primary_key=True),
)

class SponsorshipBenefit(UUIDAuditBase):
    __tablename__ = "sponsorship_benefits"

    name: Mapped[str] = mapped_column(String(1024), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    program_id: Mapped[int] = mapped_column(ForeignKey("sponsorship_programs.id",
                                                        ondelete="CASCADE"),
                                            nullable=False)
    program: Mapped["SponsorshipProgram"] = relationship("SponsorshipProgram",
                                                         back_populates="benefits")

    packages: Mapped[list["SponsorshipPackage"]] = relationship("SponsorshipPackage",
                                                               secondary=sponsorship_package_benefits)

    package_only: Mapped[bool] = mapped_column(Boolean, default=False)
    new: Mapped[bool] = mapped_column(Boolean, default=False)
    unavailable: Mapped[bool] = mapped_column(Boolean, default=False)
    standalone: Mapped[bool] = mapped_column(Boolean, default=False)

    legal_clauses: Mapped[list["LegalClause"]] = relationship("LegalClause",
                                                              secondary=sponsorship_benefit_legal_clauses)

    internal_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    soft_capacity: Mapped[bool] = mapped_column(Boolean, default=False)

    conflicts: Mapped[list["SponsorshipBenefit"]] = relationship(
        "SponsorshipBenefit",
        secondary=sponsorship_benefit_conflicts,
        primaryjoin="SponsorshipBenefit.id==sponsorship_benefit_conflicts.c.benefit_id",
        secondaryjoin="SponsorshipBenefit.id==sponsorship_benefit_conflicts.c.conflicting_benefit_id",
    )

    year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    features_config: Mapped[list["BenefitFeatureConfiguration"]] = relationship(
        "BenefitFeatureConfiguration", back_populates="benefit"
    )
```

### SponsorBenefit Model

**SQLAlchemy Mapping:**
```python
class SponsorBenefit(UUIDAuditBase):
    __tablename__ = "sponsor_benefits"

    sponsorship_id: Mapped[int] = mapped_column(ForeignKey("sponsorships.id",
                                                            ondelete="CASCADE"),
                                                nullable=False)
    sponsorship: Mapped["Sponsorship"] = relationship("Sponsorship", back_populates="benefits")

    sponsorship_benefit_id: Mapped[int | None] = mapped_column(
        ForeignKey("sponsorship_benefits.id", ondelete="SET NULL"),
        nullable=True
    )
    sponsorship_benefit: Mapped["SponsorshipBenefit | None"] = relationship("SponsorshipBenefit")

    program_name: Mapped[str] = mapped_column(String(1024), nullable=False)
    name: Mapped[str] = mapped_column(String(1024), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    program_id: Mapped[int | None] = mapped_column(ForeignKey("sponsorship_programs.id",
                                                               ondelete="SET NULL"),
                                                    nullable=True)
    program: Mapped["SponsorshipProgram | None"] = relationship("SponsorshipProgram")

    benefit_internal_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    added_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    standalone: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    features: Mapped[list["BenefitFeature"]] = relationship("BenefitFeature",
                                                           back_populates="sponsor_benefit")
```

### BenefitFeatureConfiguration (Polymorphic Base)

**SQLAlchemy Mapping:**
```python
class BenefitFeatureConfiguration(UUIDAuditBase):
    __tablename__ = "benefit_feature_configurations"

    feature_type: Mapped[str] = mapped_column(String(50), nullable=False)

    __mapper_args__ = {
        "polymorphic_on": feature_type,
        "polymorphic_identity": "base",
    }

    benefit_id: Mapped[int] = mapped_column(ForeignKey("sponsorship_benefits.id",
                                                        ondelete="CASCADE"),
                                            nullable=False)
    benefit: Mapped["SponsorshipBenefit"] = relationship("SponsorshipBenefit",
                                                         back_populates="features_config")
```

### BenefitFeature (Polymorphic Base)

**SQLAlchemy Mapping:**
```python
class BenefitFeature(UUIDAuditBase):
    __tablename__ = "benefit_features"

    feature_type: Mapped[str] = mapped_column(String(50), nullable=False)

    __mapper_args__ = {
        "polymorphic_on": feature_type,
        "polymorphic_identity": "base",
    }

    sponsor_benefit_id: Mapped[int] = mapped_column(ForeignKey("sponsor_benefits.id",
                                                                ondelete="CASCADE"),
                                                    nullable=False)
    sponsor_benefit: Mapped["SponsorBenefit"] = relationship("SponsorBenefit",
                                                            back_populates="features")
```

### LegalClause Model

**SQLAlchemy Mapping:**
```python
class LegalClause(UUIDAuditBase):
    __tablename__ = "legal_clauses"

    internal_name: Mapped[str] = mapped_column(String(1024), nullable=False)
    clause: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    order: Mapped[int] = mapped_column(Integer, default=0)
```

### Contract Model

**SQLAlchemy Mapping:**
```python
class ContractStatus(str, Enum):
    DRAFT = "draft"
    OUTDATED = "outdated"
    AWAITING_SIGNATURE = "awaiting signature"
    EXECUTED = "executed"
    NULLIFIED = "nullified"

class Contract(UUIDAuditBase):
    __tablename__ = "contracts"

    status: Mapped[str] = mapped_column(String(20), default=ContractStatus.DRAFT, index=True)
    revision: Mapped[int] = mapped_column(Integer, default=0)

    document: Mapped[str] = mapped_column(String(400), default="")  # PDF upload path
    document_docx: Mapped[str] = mapped_column(String(400), default="")  # DOCX upload path
    signed_document: Mapped[str] = mapped_column(String(400), default="")  # Signed PDF path

    sponsorship_id: Mapped[int | None] = mapped_column(ForeignKey("sponsorships.id",
                                                                   ondelete="SET NULL"),
                                                        unique=True, nullable=True)
    sponsorship: Mapped["Sponsorship | None"] = relationship("Sponsorship",
                                                             back_populates="contract")

    sponsor_info: Mapped[str] = mapped_column(Text, nullable=False)
    sponsor_contact: Mapped[str] = mapped_column(Text, nullable=False)

    benefits_list_raw: Mapped[str] = mapped_column(Text, nullable=False)
    benefits_list_markup_type: Mapped[str] = mapped_column(String(30), default="markdown")
    benefits_list_rendered: Mapped[str] = mapped_column(Text, nullable=False)

    legal_clauses_raw: Mapped[str] = mapped_column(Text, default="")
    legal_clauses_markup_type: Mapped[str] = mapped_column(String(30), default="markdown")
    legal_clauses_rendered: Mapped[str] = mapped_column(Text, default="")

    created_on: Mapped[date] = mapped_column(Date, default=func.current_date())
    last_update: Mapped[date] = mapped_column(Date, default=func.current_date(),
                                              onupdate=func.current_date())
    sent_on: Mapped[date | None] = mapped_column(Date, nullable=True)
```

### SponsorshipCurrentYear (Singleton)

**SQLAlchemy Mapping:**
```python
class SponsorshipCurrentYear(UUIDAuditBase):
    __tablename__ = "sponsorship_current_year"

    year: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("id = 1", name="singleton_check"),
    )
```

---

## Field Type Mappings

### Django → SQLAlchemy Field Conversion

| Django Field | SQLAlchemy Type | Notes |
|-------------|-----------------|-------|
| `models.CharField(max_length=N)` | `String(N)` | |
| `models.TextField()` | `Text` | |
| `models.IntegerField()` | `Integer` | |
| `models.PositiveIntegerField()` | `Integer` | Add CheckConstraint >= 0 |
| `models.PositiveSmallIntegerField()` | `SmallInteger` | Add CheckConstraint >= 0 |
| `models.BooleanField()` | `Boolean` | |
| `models.DateTimeField()` | `DateTime(timezone=True)` | Always use timezone-aware |
| `models.DateField()` | `Date` | |
| `models.EmailField()` | `String(254)` | Add email validation |
| `models.URLField()` | `String(200)` | Add URL validation |
| `models.SlugField()` | `String(50)` | Add slug validation |
| `models.JSONField()` | `JSON` | PostgreSQL JSON type |
| `models.DurationField()` | `Interval` | PostgreSQL interval |
| `models.FileField()` | `String(N)` | Store file path |
| `models.ImageField()` | `String(N)` | Store image path |
| `models.UUIDField()` | `UUID(as_uuid=True)` | |
| `MarkupField()` | 3 fields: `_raw`, `_markup_type`, `_rendered` | Custom handling |
| `CountryField()` | `String(2)` | ISO country code |
| `models.ForeignKey()` | `ForeignKey()` + `relationship()` | Bidirectional |
| `models.ManyToManyField()` | `Table()` + `relationship()` | Association table |
| `models.OneToOneField()` | `ForeignKey(unique=True)` + `relationship(uselist=False)` | |

### Default Values

| Django | SQLAlchemy |
|--------|------------|
| `default=timezone.now` | `default=func.now()` |
| `default=date.today` | `default=func.current_date()` |
| `auto_now=True` | `onupdate=func.now()` |
| `auto_now_add=True` | `default=func.now()` |
| `blank=True, null=True` | `nullable=True` |
| `blank=True` (no null) | `default=""` or `default=value` |

### Indexes

| Django | SQLAlchemy |
|--------|------------|
| `db_index=True` | `index=True` |
| `unique=True` | `unique=True` |
| `class Meta: indexes = [...]` | `__table_args__ = (Index(...),)` |

---

## Relationship Mappings

### ForeignKey (One-to-Many)

**Django:**
```python
class Child(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='children')
```

**SQLAlchemy:**
```python
class Parent(Base):
    children: Mapped[list["Child"]] = relationship("Child", back_populates="parent")

class Child(Base):
    parent_id: Mapped[int] = mapped_column(ForeignKey("parents.id", ondelete="CASCADE"))
    parent: Mapped["Parent"] = relationship("Parent", back_populates="children")
```

### OneToOneField

**Django:**
```python
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
```

**SQLAlchemy:**
```python
class User(Base):
    profile: Mapped["Profile | None"] = relationship("Profile", back_populates="user", uselist=False)

class Profile(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    user: Mapped["User"] = relationship("User", back_populates="profile")
```

### ManyToManyField

**Django:**
```python
class Article(models.Model):
    tags = models.ManyToManyField(Tag, related_name='articles')
```

**SQLAlchemy:**
```python
article_tags = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

class Article(Base):
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary=article_tags, back_populates="articles")

class Tag(Base):
    articles: Mapped[list["Article"]] = relationship("Article", secondary=article_tags, back_populates="tags")
```

### Self-Referential Relationships

**Django:**
```python
class Category(models.Model):
    parent = models.ForeignKey('self', null=True, on_delete=models.CASCADE, related_name='children')
```

**SQLAlchemy:**
```python
class Category(Base):
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=True)
    parent: Mapped["Category | None"] = relationship("Category", remote_side="Category.id",
                                                     back_populates="children")
    children: Mapped[list["Category"]] = relationship("Category", back_populates="parent")
```

### GenericForeignKey (Django ContentTypes)

**Django:**
```python
from django.contrib.contenttypes.fields import GenericForeignKey

class TaggedItem(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
```

**SQLAlchemy Alternative:**
```python
# Option 1: Separate foreign keys (recommended)
class TaggedItem(Base):
    article_id: Mapped[int | None] = mapped_column(ForeignKey("articles.id"), nullable=True)
    video_id: Mapped[int | None] = mapped_column(ForeignKey("videos.id"), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "(article_id IS NOT NULL AND video_id IS NULL) OR "
            "(article_id IS NULL AND video_id IS NOT NULL)",
            name="check_one_parent"
        ),
    )

# Option 2: Polymorphic associations (more complex)
# See: https://docs.sqlalchemy.org/en/20/orm/examples.html#generic-associations
```

---

## Special Handling Required

### 1. MarkupField

Django's `MarkupField` stores content with markup type and renders it.

**Conversion Strategy:**
```python
# Split into 3 fields
content_raw: Mapped[str] = mapped_column(Text, nullable=False)
content_markup_type: Mapped[str] = mapped_column(String(30), default="restructuredtext")
content_rendered: Mapped[str] = mapped_column(Text, nullable=False)

# Use SQLAlchemy events or service layer to render on save
@event.listens_for(MyModel, "before_insert")
@event.listens_for(MyModel, "before_update")
def render_content(mapper, connection, target):
    if target.content_raw:
        target.content_rendered = render_markup(
            target.content_raw,
            target.content_markup_type
        )
```

### 2. Django Signals

Replace Django signals with SQLAlchemy event listeners:

**Django:**
```python
@receiver(post_save, sender=Release)
def update_supernav(sender, instance, **kwargs):
    # Update logic
    pass
```

**SQLAlchemy:**
```python
from sqlalchemy import event

@event.listens_for(Release, "after_insert")
@event.listens_for(Release, "after_update")
def update_supernav(mapper, connection, target):
    # Update logic
    pass
```

### 3. Custom Managers/QuerySets

Replace Django managers with service layer methods or custom query builders:

**Django:**
```python
class ReleaseManager(models.Manager):
    def latest_python3(self):
        return self.filter(version=Release.PYTHON3, is_latest=True).first()
```

**SQLAlchemy:**
```python
# Service layer approach
class ReleaseService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_python3(self) -> Release | None:
        stmt = select(Release).where(
            Release.version == ReleaseVersion.PYTHON3,
            Release.is_latest == True
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
```

### 4. Polymorphic Models

Use SQLAlchemy's built-in polymorphic support:

**Django (django-polymorphic):**
```python
from polymorphic.models import PolymorphicModel

class Asset(PolymorphicModel):
    name = models.CharField(max_length=100)

class ImageAsset(Asset):
    image = models.ImageField()
```

**SQLAlchemy:**
```python
class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_type: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))

    __mapper_args__ = {
        "polymorphic_on": asset_type,
        "polymorphic_identity": "asset",
    }

class ImageAsset(Asset):
    __tablename__ = "image_assets"

    id: Mapped[int] = mapped_column(ForeignKey("assets.id"), primary_key=True)
    image: Mapped[str] = mapped_column(String(400))

    __mapper_args__ = {
        "polymorphic_identity": "image",
    }
```

### 5. Ordered Models

Replace `django-ordered-model` with custom implementation:

**Strategy:**
```python
class OrderedMixin:
    order: Mapped[int] = mapped_column(Integer, default=0, index=True)

    # Implement ordering methods in service layer
```

### 6. File Uploads

Django's `FileField` and `ImageField` need custom handling:

**Strategy:**
```python
# Store paths as strings
logo: Mapped[str] = mapped_column(String(400))

# Use Litestar's file upload handling
# https://docs.litestar.dev/latest/usage/requests.html#file-uploads

# Implement validators for file types/sizes
```

### 7. Slug Auto-Generation

Use SQLAlchemy events:

```python
from slugify import slugify

@event.listens_for(MyModel, "before_insert")
def generate_slug(mapper, connection, target):
    if not target.slug and target.name:
        target.slug = slugify(target.name)
```

### 8. Choices/Enums

Replace Django choices with Python enums:

**Django:**
```python
class Job(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_REVIEW = 'review'
    STATUS_CHOICES = (
        (STATUS_DRAFT, 'draft'),
        (STATUS_REVIEW, 'review'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
```

**SQLAlchemy:**
```python
from enum import StrEnum

class JobStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"

class Job(Base):
    status: Mapped[str] = mapped_column(String(20), default=JobStatus.DRAFT)
```

### 9. Validators

Replace Django field validators with Pydantic validators:

**Django:**
```python
from django.core.validators import RegexValidator

path = models.CharField(validators=[RegexValidator(regex=r'^[a-z0-9-]+$')])
```

**Litestar/Pydantic:**
```python
from pydantic import Field, field_validator

class PageCreate(TypedDict):
    path: Annotated[str, Field(pattern=r'^[a-z0-9-]+$')]
```

### 10. Meta Options

| Django Meta | SQLAlchemy Equivalent |
|------------|----------------------|
| `ordering = ('-created',)` | Query: `.order_by(Model.created.desc())` |
| `verbose_name = 'X'` | Not needed (use docstrings) |
| `get_latest_by = 'created'` | Service method |
| `permissions = [...]` | Implement in authorization layer |
| `unique_together` | `UniqueConstraint()` in `__table_args__` |
| `indexes = [...]` | `Index()` in `__table_args__` |

---

## Migration Strategy

### Phase 1: Core Models
1. User, Membership, UserGroup
2. Base mixins (ContentManageable, NameSlug)
3. Simple apps (Blogs, Pages)

### Phase 2: Content Models
1. Events (Calendar, Event, Rules, Alarms)
2. Downloads (OS, Release, ReleaseFile)
3. Jobs (JobType, JobCategory, Job)
4. Community (Post, Link, Photo, Video)
5. Success Stories (StoryCategory, Story)

### Phase 3: Complex Models
1. Sponsors base models (Sponsor, SponsorContact)
2. Sponsorship models (Package, Program, Sponsorship, Benefits)
3. Polymorphic assets (GenericAsset hierarchy)
4. Benefit features (polymorphic configurations)
5. Contracts and legal clauses

### Phase 4: Integration
1. Replace signals with event listeners
2. Implement service layer for business logic
3. Add caching strategies
4. Implement file upload handling
5. Add search functionality
6. Testing and validation

---

## Key Implementation Notes

1. **Always use async/await**: All database operations should be async
2. **Use UUID primary keys**: Following Litestar best practices
3. **Timezone awareness**: All datetime fields should be timezone-aware
4. **Type hints**: Use `Mapped[]` for all fields
5. **Relationships**: Always bidirectional with `back_populates`
6. **Lazy loading**: Consider `selectinload()` for eager loading
7. **Validation**: Move to Pydantic DTOs, not model level
8. **Business logic**: Keep in service layer, not models
9. **Caching**: Implement at service/repository layer
10. **File storage**: Use proper file storage backend (S3, etc.)

---

## Summary Statistics

- **Total Models:** ~50+
- **Polymorphic Hierarchies:** 2 (GenericAsset, BenefitFeature)
- **Many-to-Many Relationships:** ~15
- **MarkupFields to Convert:** ~25
- **Custom Managers:** ~10
- **Signal Handlers:** ~15
- **File Upload Fields:** ~10

---

**Document Version:** 1.0
**Last Updated:** 2025-11-25
**Author:** MODEL ANALYST Agent
