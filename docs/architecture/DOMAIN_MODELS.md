# Domain Models Reference

## Overview

This document provides comprehensive documentation for all domain models in the Litestar Python.org project. The application follows a Domain-Driven Design (DDD) approach, organizing code into cohesive domain modules that encapsulate related business logic.

**Document Status**: Active
**Version**: 1.0
**Last Updated**: 2025-12-14

---

## Table of Contents

1. [Domain-Driven Design Approach](#domain-driven-design-approach)
2. [Core Infrastructure](#core-infrastructure)
3. [Domain Catalog](#domain-catalog)
   - [Users](#users-domain)
   - [Pages](#pages-domain)
   - [Downloads](#downloads-domain)
   - [Blogs](#blogs-domain)
   - [Jobs](#jobs-domain)
   - [Events](#events-domain)
   - [Sponsors](#sponsors-domain)
   - [Community](#community-domain)
   - [Success Stories](#success-stories-domain)
   - [Nominations](#nominations-domain)
   - [Code Samples](#code-samples-domain)
   - [Minutes](#minutes-domain)
   - [Banners](#banners-domain)
   - [Mailing](#mailing-domain)
   - [Work Groups](#work-groups-domain)
4. [Entity Relationships](#entity-relationships)
5. [Cross-Domain Dependencies](#cross-domain-dependencies)
6. [Database Tables Summary](#database-tables-summary)

---

## Domain-Driven Design Approach

### Architecture Philosophy

The project implements a modular domain-driven architecture where each domain:

1. **Encapsulates Business Logic**: Each domain contains its own models, services, controllers, and schemas
2. **Maintains Clear Boundaries**: Domains communicate through well-defined interfaces
3. **Follows Single Responsibility**: Each domain handles one cohesive area of functionality
4. **Enables Independent Development**: Domains can evolve independently with minimal coupling

### Domain Module Structure

Each domain follows a consistent internal structure:

```
domains/{domain_name}/
    __init__.py          # Domain exports
    models.py            # SQLAlchemy ORM models
    schemas.py           # Pydantic validation schemas
    services.py          # Business logic layer
    controllers.py       # HTTP route handlers
    repositories.py      # Data access layer (when needed)
    dependencies.py      # Domain-specific DI providers
```

### Base Classes and Mixins

All models inherit from shared base classes defined in `pydotorg.core.database.base`:

| Base Class | Description |
|------------|-------------|
| `Base` | Basic model with UUID primary key (from `UUIDBase`) |
| `AuditBase` | Adds `created_at` and `updated_at` timestamps (from `UUIDAuditBase`) |
| `SlugMixin` | Adds `slug` field with URL-friendly identifier |
| `NameSlugMixin` | Extends `SlugMixin` with `name` field and auto-slug generation |
| `ContentManageableMixin` | Adds content management fields: `creator_id`, `last_modified_by_id`, `created`, `updated` |

---

## Core Infrastructure

### Base Model Definitions

```python
class Base(UUIDBase):
    """Base for all models with UUID primary key."""
    __abstract__ = True

class AuditBase(UUIDAuditBase):
    """Base with automatic created/updated timestamps."""
    __abstract__ = True

class SlugMixin:
    """Adds URL-friendly slug field."""
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)

class NameSlugMixin(SlugMixin):
    """Adds name field with auto-generated slug."""
    name: Mapped[str] = mapped_column(String(200))

class ContentManageableMixin:
    """Adds content management tracking."""
    created: Mapped[datetime]
    updated: Mapped[datetime]
    creator_id: Mapped[UUID | None]
    last_modified_by_id: Mapped[UUID | None]
```

---

## Domain Catalog

### Users Domain

**Purpose**: User authentication, profile management, and PSF membership

**Location**: `src/pydotorg/domains/users/`

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `User` | `users` | Core user account with authentication and profile |
| `Membership` | `memberships` | PSF membership information linked to user |
| `UserGroup` | `user_groups` | Python user groups and meetups |

#### User Model

```python
class User(UUIDAuditBase):
    __tablename__ = "users"

    # Authentication
    username: Mapped[str]           # Unique, indexed
    email: Mapped[str]              # Unique, indexed
    password_hash: Mapped[str | None]
    email_verified: Mapped[bool]

    # Profile
    first_name: Mapped[str]
    last_name: Mapped[str]
    bio: Mapped[str]
    public_profile: Mapped[bool]

    # Status
    is_active: Mapped[bool]
    is_staff: Mapped[bool]
    is_superuser: Mapped[bool]

    # OAuth
    oauth_provider: Mapped[str | None]
    oauth_id: Mapped[str | None]

    # Privacy
    search_visibility: Mapped[SearchVisibility]
    email_privacy: Mapped[EmailPrivacy]

    # Relationships
    membership: Mapped[Membership | None]
    sponsorships: Mapped[list[Sponsorship]]
```

#### Membership Model

```python
class Membership(UUIDAuditBase):
    __tablename__ = "memberships"

    user_id: Mapped[UUID]               # FK to users, unique
    membership_type: Mapped[MembershipType]
    legal_name: Mapped[str]
    preferred_name: Mapped[str]
    email_address: Mapped[str]

    # Location
    city: Mapped[str]
    region: Mapped[str]
    country: Mapped[str]
    postal_code: Mapped[str]

    # PSF-specific
    psf_code_of_conduct: Mapped[bool]
    psf_announcements: Mapped[bool]
    votes: Mapped[bool]
    last_vote_affirmation: Mapped[date | None]
```

#### Enums

| Enum | Values |
|------|--------|
| `SearchVisibility` | `PUBLIC`, `PRIVATE` |
| `EmailPrivacy` | `PUBLIC`, `PRIVATE`, `NEVER` |
| `MembershipType` | `BASIC`, `SUPPORTING`, `SPONSOR`, `MANAGING`, `CONTRIBUTING`, `FELLOW` |
| `UserGroupType` | `MEETUP`, `DISTRIBUTION_LIST`, `OTHER` |

#### Services

- `UserService`: User CRUD, authentication, deactivation
- `MembershipService`: Membership management
- `UserGroupService`: User group approval and trust management
- `APIKeyService`: API key generation and revocation

---

### Pages Domain

**Purpose**: CMS flat pages and content management

**Location**: `src/pydotorg/domains/pages/`

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `Page` | `pages` | CMS pages with markup content |
| `Image` | `page_images` | Images attached to pages |
| `DocumentFile` | `page_documents` | Documents attached to pages |

#### Page Model

```python
class Page(AuditBase, ContentManageableMixin):
    __tablename__ = "pages"

    title: Mapped[str]
    keywords: Mapped[str]           # SEO meta keywords
    description: Mapped[str]        # SEO meta description
    path: Mapped[str]               # Unique URL path, indexed
    content: Mapped[str]            # Page content
    content_type: Mapped[ContentType]
    is_published: Mapped[bool]
    template_name: Mapped[str]      # Custom template override

    # Relationships
    images: Mapped[list[Image]]
    documents: Mapped[list[DocumentFile]]
```

#### Enums

| Enum | Values |
|------|--------|
| `ContentType` | `MARKDOWN`, `RESTRUCTUREDTEXT`, `HTML` |

#### Services

- `PageService`: Page CRUD and publishing workflow

---

### Downloads Domain

**Purpose**: Python release management and download file distribution

**Location**: `src/pydotorg/domains/downloads/`

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `OS` | `download_os` | Supported operating systems |
| `Release` | `releases` | Python version releases |
| `ReleaseFile` | `release_files` | Downloadable files for each release |
| `DownloadStatistic` | `download_statistics` | Daily download counts |

#### Release Model

```python
class Release(AuditBase, ContentManageableMixin, NameSlugMixin):
    __tablename__ = "releases"

    version: Mapped[PythonVersion]      # Python 1/2/3/manager
    status: Mapped[ReleaseStatus]       # prerelease/bugfix/security/eol
    is_latest: Mapped[bool]             # Latest in version series
    is_published: Mapped[bool]
    pre_release: Mapped[bool]           # Alpha/beta/RC flag
    show_on_download_page: Mapped[bool]
    release_date: Mapped[date | None]
    eol_date: Mapped[date | None]
    release_page_id: Mapped[UUID | None]  # FK to pages
    release_notes_url: Mapped[str]
    content: Mapped[str]

    # Relationships
    release_page: Mapped[Page | None]
    files: Mapped[list[ReleaseFile]]
```

#### ReleaseFile Model

```python
class ReleaseFile(AuditBase, ContentManageableMixin, NameSlugMixin):
    __tablename__ = "release_files"

    release_id: Mapped[UUID]        # FK to releases
    os_id: Mapped[UUID]             # FK to download_os
    description: Mapped[str]
    is_source: Mapped[bool]         # Source distribution
    url: Mapped[str]                # Download URL

    # Signatures and checksums
    gpg_signature_file: Mapped[str]
    sigstore_signature_file: Mapped[str]
    sigstore_cert_file: Mapped[str]
    sigstore_bundle_file: Mapped[str]
    sbom_spdx2_file: Mapped[str]
    md5_sum: Mapped[str]
    sha256_sum: Mapped[str]

    filesize: Mapped[int]
    download_button: Mapped[bool]   # Featured download button

    # Relationships
    release: Mapped[Release]
    os: Mapped[OS]
    statistics: Mapped[list[DownloadStatistic]]
```

#### Enums

| Enum | Values |
|------|--------|
| `PythonVersion` | `PYTHON1`, `PYTHON2`, `PYTHON3`, `PYMANAGER` |
| `ReleaseStatus` | `PRERELEASE`, `BUGFIX`, `SECURITY`, `EOL` |

#### Services

- `OSService`: Operating system management
- `ReleaseService`: Release management, version grouping, latest release tracking
- `ReleaseFileService`: File management and download tracking

---

### Blogs Domain

**Purpose**: Blog feed aggregation from external sources

**Location**: `src/pydotorg/domains/blogs/`

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `Feed` | `feeds` | RSS/Atom feed sources |
| `BlogEntry` | `blog_entries` | Individual blog posts from feeds |
| `FeedAggregate` | `feed_aggregates` | Named groups of feeds |
| `RelatedBlog` | `related_blogs` | Related blog references |

#### Feed Model

```python
class Feed(AuditBase):
    __tablename__ = "feeds"

    name: Mapped[str]
    website_url: Mapped[str]
    feed_url: Mapped[str]           # Unique
    last_fetched: Mapped[datetime | None]
    is_active: Mapped[bool]
    priority: Mapped[int]

    entries: Mapped[list[BlogEntry]]
```

#### BlogEntry Model

```python
class BlogEntry(AuditBase):
    __tablename__ = "blog_entries"

    feed_id: Mapped[UUID]           # FK to feeds
    title: Mapped[str]
    summary: Mapped[str | None]
    content: Mapped[str | None]
    url: Mapped[str]
    pub_date: Mapped[datetime]
    guid: Mapped[str]               # Unique identifier
    is_featured: Mapped[bool]

    feed: Mapped[Feed]
```

#### Association Table

- `feed_aggregate_feeds`: Many-to-many linking `feed_aggregates` to `feeds`

#### Services

- `FeedService`: Feed CRUD and fetching
- `BlogEntryService`: Entry management

---

### Jobs Domain

**Purpose**: Job board with submission, moderation, and publishing workflow

**Location**: `src/pydotorg/domains/jobs/`

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `Job` | `jobs` | Job listings |
| `JobType` | `job_types` | Job type categories (full-time, contract, etc.) |
| `JobCategory` | `job_categories` | Industry categories |
| `JobReviewComment` | `job_review_comments` | Moderation comments |

#### Job Model

```python
class Job(AuditBase):
    __tablename__ = "jobs"

    slug: Mapped[str]               # Unique, indexed
    creator_id: Mapped[UUID]        # FK to users
    company_name: Mapped[str]
    job_title: Mapped[str]

    # Location
    city: Mapped[str | None]
    region: Mapped[str | None]
    country: Mapped[str]

    # Content
    description: Mapped[str]
    requirements: Mapped[str | None]

    # Contact
    contact: Mapped[str | None]
    url: Mapped[str | None]
    email: Mapped[str]

    # Status
    status: Mapped[JobStatus]
    telecommuting: Mapped[bool]
    agencies: Mapped[bool]
    is_featured: Mapped[bool]
    expires: Mapped[date | None]

    category_id: Mapped[UUID | None]

    # Relationships
    creator: Mapped[User]
    job_types: Mapped[list[JobType]]
    category: Mapped[JobCategory | None]
    review_comments: Mapped[list[JobReviewComment]]
```

#### Enums

| Enum | Values |
|------|--------|
| `JobStatus` | `DRAFT`, `REVIEW`, `APPROVED`, `REJECTED`, `ARCHIVED`, `EXPIRED` |

#### Association Table

- `job_job_types`: Many-to-many linking `jobs` to `job_types`

#### Services

- `JobService`: Job CRUD, submission workflow, approval/rejection
- `JobTypeService`: Job type management
- `JobCategoryService`: Category management
- `JobReviewCommentService`: Moderation comments

---

### Events Domain

**Purpose**: Community event calendar with recurring event support

**Location**: `src/pydotorg/domains/events/`

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `Calendar` | `calendars` | Event calendars/categories |
| `Event` | `events` | Individual events |
| `EventCategory` | `event_categories` | Event categories |
| `EventLocation` | `event_locations` | Venues/locations |
| `EventOccurrence` | `event_occurrences` | Single event occurrences |
| `RecurringRule` | `event_recurring_rules` | Recurrence patterns |

#### Event Model

```python
class Event(AuditBase, ContentManageableMixin, NameSlugMixin):
    __tablename__ = "events"

    title: Mapped[str]
    description: Mapped[str | None]
    calendar_id: Mapped[UUID]       # FK to calendars
    venue_id: Mapped[UUID | None]   # FK to event_locations
    featured: Mapped[bool]

    # Relationships
    calendar: Mapped[Calendar]
    venue: Mapped[EventLocation | None]
    categories: Mapped[list[EventCategory]]
    occurrences: Mapped[list[EventOccurrence]]
    recurring_rules: Mapped[list[RecurringRule]]
```

#### RecurringRule Model

```python
class RecurringRule(Base):
    __tablename__ = "event_recurring_rules"

    event_id: Mapped[UUID]          # FK to events
    begin: Mapped[datetime]
    finish: Mapped[datetime]
    duration: Mapped[timedelta]
    interval: Mapped[int]           # e.g., every 2 weeks
    frequency: Mapped[int]          # YEARLY/MONTHLY/WEEKLY/DAILY
    all_day: Mapped[bool]

    event: Mapped[Event]
```

#### Enums

| Enum | Values (from dateutil.rrule) |
|------|------------------------------|
| `RecurrenceFrequency` | `YEARLY`, `MONTHLY`, `WEEKLY`, `DAILY` |

#### Association Table

- `event_event_categories`: Many-to-many linking `events` to `event_categories`

#### Services

- `EventService`: Event management
- `CalendarService`: Calendar management

---

### Sponsors Domain

**Purpose**: PSF sponsorship management with contract workflow

**Location**: `src/pydotorg/domains/sponsors/`

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `Sponsor` | `sponsors` | Sponsor organizations |
| `Sponsorship` | `sponsorships` | Individual sponsorship agreements |
| `SponsorshipLevel` | `sponsorship_levels` | Sponsorship tiers |
| `Contract` | `sponsor_contracts` | Contract documents |
| `LegalClause` | `sponsor_legal_clauses` | Contract legal clauses |

#### Sponsor Model

```python
class Sponsor(AuditBase, ContentManageableMixin, NameSlugMixin):
    __tablename__ = "sponsors"

    description: Mapped[str]
    landing_page_url: Mapped[str]
    twitter_handle: Mapped[str]
    linked_in_page_url: Mapped[str]

    # Logos
    web_logo: Mapped[str]
    print_logo: Mapped[str]

    # Contact
    primary_phone: Mapped[str]

    # Address
    mailing_address_line_1: Mapped[str]
    mailing_address_line_2: Mapped[str]
    city: Mapped[str]
    state: Mapped[str]
    postal_code: Mapped[str]
    country: Mapped[str]
    country_of_incorporation: Mapped[str]
    state_of_incorporation: Mapped[str]

    sponsorships: Mapped[list[Sponsorship]]
```

#### Sponsorship Model

```python
class Sponsorship(AuditBase, ContentManageableMixin):
    __tablename__ = "sponsorships"

    sponsor_id: Mapped[UUID]        # FK to sponsors
    level_id: Mapped[UUID]          # FK to sponsorship_levels
    submitted_by_id: Mapped[UUID | None]  # FK to users
    status: Mapped[SponsorshipStatus]
    locked: Mapped[bool]

    # Dates
    start_date: Mapped[date | None]
    end_date: Mapped[date | None]
    applied_on: Mapped[date | None]
    approved_on: Mapped[date | None]
    rejected_on: Mapped[date | None]
    finalized_on: Mapped[date | None]

    year: Mapped[int | None]
    sponsorship_fee: Mapped[Decimal]
    for_modified_package: Mapped[bool]
    renewal: Mapped[bool]

    # Relationships
    sponsor: Mapped[Sponsor]
    level: Mapped[SponsorshipLevel]
    submitted_by: Mapped[User | None]
    contract: Mapped[Contract | None]
```

#### Enums

| Enum | Values |
|------|--------|
| `SponsorshipStatus` | `APPLIED`, `REJECTED`, `APPROVED`, `FINALIZED` |
| `ContractStatus` | `DRAFT`, `OUTDATED`, `AWAITING_SIGNATURE`, `EXECUTED`, `NULLIFIED` |

#### Services

- `SponsorService`: Sponsor organization management
- `SponsorshipService`: Sponsorship lifecycle management
- `ContractService`: Contract workflow

---

### Community Domain

**Purpose**: Community-contributed content including posts, photos, videos, and links

**Location**: `src/pydotorg/domains/community/`

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `Post` | `community_posts` | Community blog posts |
| `Photo` | `community_photos` | Photo attachments |
| `Video` | `community_videos` | Video links |
| `Link` | `community_links` | External links |

#### Post Model

```python
class Post(AuditBase, SlugMixin):
    __tablename__ = "community_posts"

    title: Mapped[str]
    content: Mapped[str]
    content_type: Mapped[ContentType]
    creator_id: Mapped[UUID]        # FK to users
    is_published: Mapped[bool]

    # Relationships
    photos: Mapped[list[Photo]]
    videos: Mapped[list[Video]]
    links: Mapped[list[Link]]
```

#### Services

- `PostService`: Post management
- `PhotoService`: Photo management
- `VideoService`: Video management
- `LinkService`: Link management

---

### Success Stories Domain

**Purpose**: Python success stories and case studies

**Location**: `src/pydotorg/domains/successstories/`

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `Story` | `success_stories` | Success story content |
| `StoryCategory` | `story_categories` | Story categories |

#### Story Model

```python
class Story(AuditBase, SlugMixin):
    __tablename__ = "success_stories"

    name: Mapped[str]
    company_name: Mapped[str]
    company_url: Mapped[str | None]
    category_id: Mapped[UUID]       # FK to story_categories
    content: Mapped[str]
    content_type: Mapped[ContentType]
    is_published: Mapped[bool]
    featured: Mapped[bool]
    image: Mapped[str | None]
    creator_id: Mapped[UUID]        # FK to users

    category: Mapped[StoryCategory]
```

#### Services

- `StoryService`: Story CRUD and publishing

---

### Nominations Domain

**Purpose**: PSF election nominations and voting

**Location**: `src/pydotorg/domains/nominations/`

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `Election` | `elections` | PSF elections |
| `Nominee` | `nominees` | Election candidates |
| `Nomination` | `nominations` | Nominations with endorsements |

#### Election Model

```python
class Election(AuditBase, SlugMixin):
    __tablename__ = "elections"

    name: Mapped[str]
    description: Mapped[str | None]
    nominations_open: Mapped[date]
    nominations_close: Mapped[date]
    voting_open: Mapped[date]
    voting_close: Mapped[date]

    nominees: Mapped[list[Nominee]]

    @property
    def status(self) -> ElectionStatus:
        # Returns UPCOMING/NOMINATIONS_OPEN/VOTING_OPEN/CLOSED
```

#### Nominee Model

```python
class Nominee(AuditBase):
    __tablename__ = "nominees"

    election_id: Mapped[UUID]       # FK to elections
    user_id: Mapped[UUID]           # FK to users
    accepted: Mapped[bool]

    election: Mapped[Election]
    user: Mapped[User]
    nominations: Mapped[list[Nomination]]
```

#### Enums

| Enum | Values |
|------|--------|
| `ElectionStatus` | `UPCOMING`, `NOMINATIONS_OPEN`, `VOTING_OPEN`, `CLOSED` |

#### Services

- `ElectionService`: Election lifecycle management
- `NomineeService`: Nominee management
- `NominationService`: Nomination submissions

---

### Code Samples Domain

**Purpose**: Python code sample repository for education

**Location**: `src/pydotorg/domains/codesamples/`

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `CodeSample` | `code_samples` | Code snippets with descriptions |

#### CodeSample Model

```python
class CodeSample(AuditBase, SlugMixin):
    __tablename__ = "code_samples"

    code: Mapped[str]               # The code content
    description: Mapped[str]
    is_published: Mapped[bool]
    creator_id: Mapped[UUID]        # FK to users
```

#### Services

- `CodeSampleService`: Code sample management

---

### Minutes Domain

**Purpose**: PSF board meeting minutes

**Location**: `src/pydotorg/domains/minutes/`

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `Minutes` | `minutes` | Meeting minutes documents |

#### Minutes Model

```python
class Minutes(AuditBase, SlugMixin):
    __tablename__ = "minutes"

    date: Mapped[date]              # Meeting date, indexed
    content: Mapped[str]
    content_type: Mapped[ContentType]
    is_published: Mapped[bool]
    creator_id: Mapped[UUID]        # FK to users
```

#### Services

- `MinutesService`: Minutes CRUD and publishing

---

### Banners Domain

**Purpose**: Site-wide and targeted banners for announcements

**Location**: `src/pydotorg/domains/banners/`

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `Banner` | `banners` | Announcement banners |

#### Banner Model

```python
class Banner(AuditBase):
    __tablename__ = "banners"

    name: Mapped[str]               # Internal identifier
    title: Mapped[str]
    message: Mapped[str]
    link: Mapped[str | None]
    link_text: Mapped[str | None]
    banner_type: Mapped[str]        # info/success/warning/error
    target: Mapped[str]             # frontend/api
    paths: Mapped[str | None]       # Path patterns for targeting
    is_active: Mapped[bool]
    is_dismissible: Mapped[bool]
    is_sitewide: Mapped[bool]
    start_date: Mapped[date | None]
    end_date: Mapped[date | None]
```

#### Enums

| Enum | Values |
|------|--------|
| `BannerType` | `INFO`, `SUCCESS`, `WARNING`, `ERROR` |
| `BannerTarget` | `FRONTEND`, `API` |

#### Services

- `BannerService`: Banner management and targeting

---

### Mailing Domain

**Purpose**: Email templates and sending logs

**Location**: `src/pydotorg/domains/mailing/`

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `EmailTemplate` | `email_templates` | Jinja2 email templates |
| `EmailLog` | `email_logs` | Email sending audit log |

#### EmailTemplate Model

```python
class EmailTemplate(AuditBase):
    __tablename__ = "email_templates"

    internal_name: Mapped[str]      # Unique code identifier
    display_name: Mapped[str]
    description: Mapped[str | None]
    template_type: Mapped[EmailTemplateType]
    subject: Mapped[str]            # Jinja2 template
    content_text: Mapped[str]       # Plain text Jinja2 template
    content_html: Mapped[str | None]  # HTML Jinja2 template
    is_active: Mapped[bool]

    # Methods
    def render_subject(self, context) -> str
    def render_content_text(self, context) -> str
    def render_content_html(self, context) -> str | None
    def validate_templates(self) -> list[str]
```

#### Enums

| Enum | Values |
|------|--------|
| `EmailTemplateType` | `TRANSACTIONAL`, `NOTIFICATION`, `NEWSLETTER`, `MARKETING`, `SYSTEM` |

#### Services

- `EmailTemplateService`: Template management
- `EmailService`: Email sending with logging

---

### Work Groups Domain

**Purpose**: PSF working groups management

**Location**: `src/pydotorg/domains/work_groups/`

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `WorkGroup` | `work_groups` | PSF working groups |

#### WorkGroup Model

```python
class WorkGroup(AuditBase, SlugMixin):
    __tablename__ = "work_groups"

    name: Mapped[str]
    purpose: Mapped[str]
    active: Mapped[bool]
    url: Mapped[str | None]
    creator_id: Mapped[UUID]        # FK to users
```

#### Services

- `WorkGroupService`: Work group management

---

## Entity Relationships

### Complete Entity Relationship Diagram

```text
erDiagram
    %% Users Domain
    users ||--o| memberships : "has one"
    users ||--o{ sponsorships : "submits"
    users ||--o{ jobs : "creates"
    users ||--o{ community_posts : "creates"
    users ||--o{ success_stories : "creates"
    users ||--o{ nominations : "nominates"
    users ||--o{ nominees : "is nominated"
    users ||--o{ code_samples : "creates"
    users ||--o{ minutes : "creates"
    users ||--o{ work_groups : "creates"

    %% Downloads Domain
    releases ||--o{ release_files : "contains"
    releases ||--o| pages : "has release page"
    download_os ||--o{ release_files : "supports"
    release_files ||--o{ download_statistics : "tracks"

    %% Blogs Domain
    feeds ||--o{ blog_entries : "contains"
    feed_aggregates }o--o{ feeds : "groups"

    %% Jobs Domain
    jobs ||--o{ job_review_comments : "has"
    jobs }o--o{ job_types : "has"
    jobs }o--o| job_categories : "belongs to"

    %% Events Domain
    calendars ||--o{ events : "contains"
    events }o--o{ event_categories : "has"
    events }o--o| event_locations : "at"
    events ||--o{ event_occurrences : "occurs"
    events ||--o{ event_recurring_rules : "repeats"
    event_categories }o--|| calendars : "belongs to"

    %% Sponsors Domain
    sponsors ||--o{ sponsorships : "has"
    sponsorship_levels ||--o{ sponsorships : "defines"
    sponsorships ||--o| sponsor_contracts : "has"

    %% Community Domain
    community_posts ||--o{ community_photos : "has"
    community_posts ||--o{ community_videos : "has"
    community_posts ||--o{ community_links : "has"

    %% Success Stories Domain
    story_categories ||--o{ success_stories : "contains"

    %% Nominations Domain
    elections ||--o{ nominees : "has"
    nominees ||--o{ nominations : "receives"

    %% Pages Domain
    pages ||--o{ page_images : "has"
    pages ||--o{ page_documents : "has"
```

### Users Domain Relationships

```text
erDiagram
    users {
        uuid id PK
        string username UK
        string email UK
        string password_hash
        boolean is_active
        boolean is_staff
        boolean is_superuser
    }

    memberships {
        uuid id PK
        uuid user_id FK,UK
        enum membership_type
        string legal_name
        boolean votes
    }

    user_groups {
        uuid id PK
        string name
        string location
        boolean approved
        boolean trusted
    }

    users ||--o| memberships : "has"
```

### Downloads Domain Relationships

```text
erDiagram
    download_os {
        uuid id PK
        string name
        string slug UK
    }

    releases {
        uuid id PK
        string name
        string slug UK
        enum version
        enum status
        boolean is_latest
        boolean is_published
        date release_date
        uuid release_page_id FK
    }

    release_files {
        uuid id PK
        uuid release_id FK
        uuid os_id FK
        string url
        string md5_sum
        string sha256_sum
        bigint filesize
        boolean download_button
    }

    download_statistics {
        uuid id PK
        uuid release_file_id FK
        date date
        integer download_count
    }

    pages {
        uuid id PK
        string path UK
    }

    download_os ||--o{ release_files : "supports"
    releases ||--o{ release_files : "contains"
    releases ||--o| pages : "links to"
    release_files ||--o{ download_statistics : "tracks"
```

### Jobs Domain Relationships

```text
erDiagram
    jobs {
        uuid id PK
        string slug UK
        uuid creator_id FK
        uuid category_id FK
        string company_name
        string job_title
        enum status
    }

    job_types {
        uuid id PK
        string name
        string slug UK
    }

    job_categories {
        uuid id PK
        string name
        string slug UK
    }

    job_review_comments {
        uuid id PK
        uuid job_id FK
        uuid creator_id FK
        text comment
    }

    job_job_types {
        uuid job_id PK,FK
        uuid job_type_id PK,FK
    }

    jobs }o--o{ job_types : "has"
    jobs }o--|| job_categories : "in"
    jobs ||--o{ job_review_comments : "has"
```

### Events Domain Relationships

```text
erDiagram
    calendars {
        uuid id PK
        string name
        string slug UK
    }

    events {
        uuid id PK
        string title
        uuid calendar_id FK
        uuid venue_id FK
        boolean featured
    }

    event_categories {
        uuid id PK
        string name
        string slug UK
        uuid calendar_id FK
    }

    event_locations {
        uuid id PK
        string name
        string address
    }

    event_occurrences {
        uuid id PK
        uuid event_id FK
        datetime dt_start
        datetime dt_end
        boolean all_day
    }

    event_recurring_rules {
        uuid id PK
        uuid event_id FK
        datetime begin
        datetime finish
        interval duration
        integer frequency
    }

    calendars ||--o{ events : "contains"
    calendars ||--o{ event_categories : "has"
    events }o--o{ event_categories : "tagged"
    events }o--o| event_locations : "at"
    events ||--o{ event_occurrences : "occurs"
    events ||--o{ event_recurring_rules : "repeats"
```

### Sponsors Domain Relationships

```text
erDiagram
    sponsors {
        uuid id PK
        string name
        string slug UK
        string web_logo
    }

    sponsorship_levels {
        uuid id PK
        string name
        integer order
        integer sponsorship_amount
    }

    sponsorships {
        uuid id PK
        uuid sponsor_id FK
        uuid level_id FK
        uuid submitted_by_id FK
        enum status
        date start_date
        date end_date
    }

    sponsor_contracts {
        uuid id PK
        uuid sponsorship_id FK,UK
        enum status
        integer revision
    }

    sponsors ||--o{ sponsorships : "has"
    sponsorship_levels ||--o{ sponsorships : "defines"
    sponsorships ||--o| sponsor_contracts : "has"
```

---

## Cross-Domain Dependencies

### Dependency Graph

```text
graph TB
    subgraph Core["Core Domains (No Dependencies)"]
        USERS[users]
        PAGES[pages]
        BANNERS[banners]
        MAILING[mailing]
    end

    subgraph Content["Content Domains"]
        BLOGS[blogs]
        CODESAMPLES[codesamples]
        COMMUNITY[community]
        SUCCESSSTORIES[successstories]
        MINUTES[minutes]
        WORKGROUPS[work_groups]
    end

    subgraph Business["Business Domains"]
        DOWNLOADS[downloads]
        JOBS[jobs]
        EVENTS[events]
        SPONSORS[sponsors]
        NOMINATIONS[nominations]
    end

    %% User dependencies
    COMMUNITY --> USERS
    SUCCESSSTORIES --> USERS
    JOBS --> USERS
    SPONSORS --> USERS
    NOMINATIONS --> USERS
    CODESAMPLES --> USERS
    MINUTES --> USERS
    WORKGROUPS --> USERS

    %% Pages dependencies
    DOWNLOADS --> PAGES

    %% ContentType sharing
    COMMUNITY -.-> PAGES
    SUCCESSSTORIES -.-> PAGES
    MINUTES -.-> PAGES
```

### Dependency Matrix

| Domain | Depends On |
|--------|-----------|
| `users` | (none) |
| `pages` | (none) |
| `banners` | (none) |
| `mailing` | (none) |
| `downloads` | `pages` (release_page_id) |
| `blogs` | (none) |
| `jobs` | `users` (creator_id) |
| `events` | (none) |
| `sponsors` | `users` (submitted_by_id) |
| `community` | `users` (creator_id), `pages.ContentType` |
| `successstories` | `users` (creator_id), `pages.ContentType` |
| `nominations` | `users` (user_id, nominator_id) |
| `codesamples` | `users` (creator_id) |
| `minutes` | `users` (creator_id), `pages.ContentType` |
| `work_groups` | `users` (creator_id) |

---

## Database Tables Summary

### All Tables by Domain

| Domain | Tables | Count |
|--------|--------|-------|
| **users** | `users`, `memberships`, `user_groups` | 3 |
| **pages** | `pages`, `page_images`, `page_documents` | 3 |
| **downloads** | `download_os`, `releases`, `release_files`, `download_statistics` | 4 |
| **blogs** | `feeds`, `blog_entries`, `feed_aggregates`, `feed_aggregate_feeds`, `related_blogs` | 5 |
| **jobs** | `jobs`, `job_types`, `job_categories`, `job_job_types`, `job_review_comments` | 5 |
| **events** | `calendars`, `events`, `event_categories`, `event_locations`, `event_occurrences`, `event_recurring_rules`, `event_event_categories` | 7 |
| **sponsors** | `sponsors`, `sponsorships`, `sponsorship_levels`, `sponsor_contracts`, `sponsor_legal_clauses` | 5 |
| **community** | `community_posts`, `community_photos`, `community_videos`, `community_links` | 4 |
| **successstories** | `success_stories`, `story_categories` | 2 |
| **nominations** | `elections`, `nominees`, `nominations` | 3 |
| **codesamples** | `code_samples` | 1 |
| **minutes** | `minutes` | 1 |
| **banners** | `banners` | 1 |
| **mailing** | `email_templates`, `email_logs` | 2 |
| **work_groups** | `work_groups` | 1 |

**Total Tables**: 47

### Index Summary

Key indexed columns across all domains:

| Table | Indexed Columns |
|-------|-----------------|
| `users` | `username`, `email`, `oauth_provider`, `oauth_id` |
| `pages` | `path`, `is_published` |
| `releases` | `slug`, `is_latest`, `is_published` |
| `release_files` | `slug` |
| `download_statistics` | `release_file_id`, `date` |
| `feeds` | `is_active`, `priority` |
| `blog_entries` | `pub_date`, `is_featured` |
| `jobs` | `slug`, `status`, `is_featured` |
| `events` | `featured` |
| `event_occurrences` | `dt_start` |
| `event_recurring_rules` | `begin`, `finish` |
| `sponsorships` | `status` |
| `sponsor_contracts` | `status` |
| `elections` | `nominations_open`, `nominations_close`, `voting_open`, `voting_close` |
| `nominees` | `accepted` |
| `banners` | `banner_type`, `target`, `is_active`, `is_sitewide`, `start_date`, `end_date` |
| `email_templates` | `internal_name`, `template_type`, `is_active` |
| `email_logs` | `template_name`, `recipient_email`, `status` |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-14 | Documentation Agent | Initial domain models documentation |

---

## References

- [Architecture Overview](./ARCHITECTURE.md)
- [Database Schema](./DATABASE_SCHEMA.md)
- [Litestar Documentation](https://docs.litestar.dev/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [Advanced Alchemy](https://docs.advanced-alchemy.litestar.dev/)

---

**Document Path**: `/docs/architecture/DOMAIN_MODELS.md`
