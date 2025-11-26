# Database Schema Design

## Overview

This document provides detailed database schema design for the Litestar python.org migration, mapping Django models to SQLAlchemy 2.0 async models.

## Schema Diagram

```
┌─────────────────┐
│     users       │──┐
│─────────────────│  │
│ id (PK)         │  │
│ username (UQ)   │  │
│ email (UQ)      │  │
│ password_hash   │  │
│ is_active       │  │
│ is_staff        │  │
└─────────────────┘  │
                     │
        ┌────────────┼──────────────┬──────────────┐
        │            │              │              │
┌───────▼────────┐  │   ┌──────────▼──────┐  ┌───▼──────────┐
│  memberships   │  │   │     pages       │  │   events     │
│────────────────│  │   │─────────────────│  │──────────────│
│ id (PK)        │  │   │ id (PK)         │  │ id (PK)      │
│ creator_id(FK)─┘  │   │ title           │  │ title        │
│ membership_type│  │   │ path (UQ)       │  │ calendar_id  │
│ legal_name     │  │   │ content         │  │ venue_id     │
└────────────────┘  │   │ is_published    │  │ description  │
                    │   │ creator_id (FK)─┘  │ featured     │
                    │   └─────────────────┘  └──────────────┘
                    │
        ┌───────────┼────────────┬─────────────┐
        │           │            │             │
┌───────▼─────┐  ┌─▼──────────┐ │  ┌──────────▼─────┐
│    jobs     │  │  releases  │ │  │   calendars    │
│─────────────│  │────────────│ │  │────────────────│
│ id (PK)     │  │ id (PK)    │ │  │ id (PK)        │
│ job_title   │  │ name       │ │  │ name           │
│ company_name│  │ slug (UQ)  │ │  │ slug (UQ)      │
│ category_id │  │ version    │ │  │ url            │
│ status      │  │ is_latest  │ │  │ creator_id(FK)─┘
│creator_id   │  │is_published│ │  └────────────────┘
└─────────────┘  └────────────┘ │
                                │
                     ┌──────────┴──────────┐
                     │                     │
              ┌──────▼──────┐      ┌──────▼────────┐
              │release_files│      │ operating_    │
              │─────────────│      │  systems      │
              │ id (PK)     │      │───────────────│
              │ release_id  │──┐   │ id (PK)       │
              │ os_id       │──┼───│ name          │
              │ url (UQ)    │  │   │ slug (UQ)     │
              │download_btn │  │   └───────────────┘
              └─────────────┘  │
                               └───(Many-to-One)
```

## Core Tables

### users

**Purpose**: User authentication and profile management

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY | Auto-increment |
| username | VARCHAR(150) | UNIQUE, NOT NULL, INDEX | Case-insensitive lookup |
| email | VARCHAR(254) | UNIQUE, NOT NULL, INDEX | Email validation |
| password_hash | VARCHAR(255) | NOT NULL | Argon2 or bcrypt hash |
| first_name | VARCHAR(150) | NULL | Optional |
| last_name | VARCHAR(150) | NULL | Optional |
| is_active | BOOLEAN | DEFAULT TRUE | Account status |
| is_staff | BOOLEAN | DEFAULT FALSE | Admin access |
| is_superuser | BOOLEAN | DEFAULT FALSE | Full privileges |
| bio | TEXT | NULL | Markdown content |
| bio_markup_type | VARCHAR(30) | DEFAULT 'markdown' | Markup format |
| search_visibility | INTEGER | DEFAULT 1 | 0=private, 1=public |
| email_privacy | INTEGER | DEFAULT 2 | 0=public, 1=logged-in, 2=never |
| public_profile | BOOLEAN | DEFAULT TRUE | Profile visibility |
| created | TIMESTAMP TZ | DEFAULT NOW(), INDEX | Creation time |
| updated | TIMESTAMP TZ | DEFAULT NOW() | Last update |

**Indexes**:
- `ix_users_username` (username)
- `ix_users_email` (email)
- `ix_users_created` (created)
- `ix_users_active` (is_active) WHERE is_active = TRUE

**SQLAlchemy Model**:

```python
from sqlalchemy import String, Integer, Boolean, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    first_name: Mapped[str | None] = mapped_column(String(150))
    last_name: Mapped[str | None] = mapped_column(String(150))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    bio: Mapped[str | None] = mapped_column(Text)
    bio_markup_type: Mapped[str] = mapped_column(String(30), default="markdown")

    search_visibility: Mapped[int] = mapped_column(Integer, default=1)
    email_privacy: Mapped[int] = mapped_column(Integer, default=2)
    public_profile: Mapped[bool] = mapped_column(Boolean, default=True)

    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    membership: Mapped["Membership | None"] = relationship(back_populates="creator")

    __table_args__ = (
        Index('ix_users_active', 'is_active', postgresql_where=text('is_active = TRUE')),
    )
```

### memberships

**Purpose**: PSF membership information

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY | Auto-increment |
| creator_id | INTEGER | FK(users.id), UNIQUE | One-to-one with user |
| membership_type | INTEGER | DEFAULT 0 | 0-5 membership levels |
| legal_name | VARCHAR(100) | NOT NULL | Full legal name |
| preferred_name | VARCHAR(100) | NOT NULL | Display name |
| email_address | VARCHAR(100) | NOT NULL | Contact email |
| city | VARCHAR(100) | NULL | Location |
| region | VARCHAR(100) | NULL | State/province |
| country | VARCHAR(100) | NULL | Country |
| postal_code | VARCHAR(20) | NULL | ZIP/postal code |
| psf_code_of_conduct | BOOLEAN | NULL | CoC agreement |
| psf_announcements | BOOLEAN | NULL | Newsletter opt-in |
| votes | BOOLEAN | DEFAULT FALSE | Voting member |
| last_vote_affirmation | TIMESTAMP TZ | NULL | Last voting confirmation |
| created | TIMESTAMP TZ | DEFAULT NOW() | |
| updated | TIMESTAMP TZ | DEFAULT NOW() | |

**Constraints**:
- FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE
- UNIQUE (creator_id)

### pages

**Purpose**: CMS flat pages

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY | |
| title | VARCHAR(500) | NOT NULL | Page title |
| keywords | VARCHAR(1000) | NULL | SEO meta keywords |
| description | TEXT | NULL | SEO meta description |
| path | VARCHAR(500) | UNIQUE, NOT NULL, INDEX | URL path |
| content | TEXT | NOT NULL | Page content |
| content_markup_type | VARCHAR(30) | DEFAULT 'rst' | restructuredtext/markdown |
| is_published | BOOLEAN | DEFAULT TRUE, INDEX | Publication status |
| content_type | VARCHAR(150) | DEFAULT 'text/html' | MIME type |
| template_name | VARCHAR(100) | NULL | Custom template |
| creator_id | INTEGER | FK(users.id), NULL | Content creator |
| last_modified_by_id | INTEGER | FK(users.id), NULL | Last editor |
| created | TIMESTAMP TZ | DEFAULT NOW(), INDEX | |
| updated | TIMESTAMP TZ | DEFAULT NOW() | |

**Indexes**:
- `ix_pages_path` (path)
- `ix_pages_published` (is_published)
- `ix_pages_path_published` (path, is_published)

### releases

**Purpose**: Python release versions

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY | |
| name | VARCHAR(200) | NOT NULL | e.g., "Python 3.12.0" |
| slug | VARCHAR(200) | UNIQUE, NOT NULL | URL-safe identifier |
| version | INTEGER | DEFAULT 3 | 1=Python 1.x, 2=2.x, 3=3.x, 100=manager |
| is_latest | BOOLEAN | DEFAULT FALSE, INDEX | Latest in version |
| is_published | BOOLEAN | DEFAULT FALSE, INDEX | Published status |
| pre_release | BOOLEAN | DEFAULT FALSE, INDEX | Beta/RC flag |
| show_on_download_page | BOOLEAN | DEFAULT TRUE, INDEX | Visibility |
| release_date | TIMESTAMP TZ | NOT NULL | Release date |
| release_page_id | INTEGER | FK(pages.id), NULL | Related page |
| release_notes_url | VARCHAR(200) | NULL | External notes URL |
| content | TEXT | DEFAULT '' | Release content |
| content_markup_type | VARCHAR(30) | DEFAULT 'markdown' | |
| creator_id | INTEGER | FK(users.id), NULL | |
| created | TIMESTAMP TZ | DEFAULT NOW() | |
| updated | TIMESTAMP TZ | DEFAULT NOW() | |

**Indexes**:
- `ix_releases_version_latest` (version, is_latest)
- `ix_releases_published` (is_published)
- `ix_releases_show_on_download` (show_on_download_page)

### release_files

**Purpose**: Downloadable release files

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY | |
| name | VARCHAR(200) | NOT NULL | File description |
| slug | VARCHAR(200) | UNIQUE, NOT NULL | URL identifier |
| os_id | INTEGER | FK(operating_systems.id), NOT NULL | Target OS |
| release_id | INTEGER | FK(releases.id), NOT NULL | Parent release |
| description | TEXT | NULL | File description |
| is_source | BOOLEAN | DEFAULT FALSE | Source distribution |
| url | VARCHAR(500) | UNIQUE, NOT NULL, INDEX | Download URL |
| gpg_signature_file | VARCHAR(500) | NULL | GPG signature URL |
| sigstore_signature_file | VARCHAR(500) | NULL | Sigstore signature |
| sigstore_cert_file | VARCHAR(500) | NULL | Sigstore cert |
| sigstore_bundle_file | VARCHAR(500) | NULL | Sigstore bundle |
| sbom_spdx2_file | VARCHAR(500) | NULL | SBOM file |
| md5_sum | VARCHAR(200) | NULL | MD5 checksum |
| filesize | INTEGER | DEFAULT 0 | File size in bytes |
| download_button | BOOLEAN | DEFAULT FALSE | Show in download button |
| creator_id | INTEGER | FK(users.id), NULL | |
| created | TIMESTAMP TZ | DEFAULT NOW() | |
| updated | TIMESTAMP TZ | DEFAULT NOW() | |

**Constraints**:
- UNIQUE (os_id, release_id) WHERE download_button = TRUE
- Only one download_button per OS per release

### events

**Purpose**: Community events

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY | |
| uid | VARCHAR(200) | NULL | iCal UID |
| title | VARCHAR(200) | NOT NULL | Event title |
| calendar_id | INTEGER | FK(calendars.id), NOT NULL | Parent calendar |
| venue_id | INTEGER | FK(event_locations.id), NULL | Event location |
| description | TEXT | NOT NULL | Event description |
| description_markup_type | VARCHAR(30) | DEFAULT 'rst' | |
| featured | BOOLEAN | DEFAULT FALSE, INDEX | Featured status |
| creator_id | INTEGER | FK(users.id), NULL | |
| created | TIMESTAMP TZ | DEFAULT NOW() | |
| updated | TIMESTAMP TZ | DEFAULT NOW() | |

**Relations**:
- One-to-One with OccurringRule (single occurrence)
- One-to-Many with RecurringRule (recurring events)
- Many-to-Many with EventCategory

### jobs

**Purpose**: Job board listings

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY | |
| category_id | INTEGER | FK(job_categories.id), NOT NULL | Job category |
| other_job_type | VARCHAR(100) | NULL | Custom type |
| company_name | VARCHAR(100) | NOT NULL | Employer |
| company_description | TEXT | NULL | Company info |
| company_description_markup_type | VARCHAR(30) | DEFAULT 'rst' | |
| job_title | VARCHAR(100) | NOT NULL | Position title |
| city | VARCHAR(100) | NOT NULL | Location city |
| region | VARCHAR(100) | NULL | State/province |
| country | VARCHAR(100) | NOT NULL, INDEX | Country |
| location_slug | VARCHAR(350) | | Generated slug |
| country_slug | VARCHAR(100) | | Generated slug |
| description | TEXT | NOT NULL | Job description |
| description_markup_type | VARCHAR(30) | DEFAULT 'rst' | |
| requirements | TEXT | NOT NULL | Job requirements |
| requirements_markup_type | VARCHAR(30) | DEFAULT 'rst' | |
| contact | VARCHAR(100) | NULL | Contact name |
| email | VARCHAR(254) | NOT NULL | Contact email |
| url | VARCHAR(500) | NOT NULL | Job URL |
| submitted_by_id | INTEGER | FK(users.id), NULL | Submitter |
| status | VARCHAR(20) | DEFAULT 'review', INDEX | Job status |
| expires | TIMESTAMP TZ | NULL | Expiration date |
| telecommuting | BOOLEAN | DEFAULT FALSE | Remote allowed |
| agencies | BOOLEAN | DEFAULT TRUE | Agencies OK |
| is_featured | BOOLEAN | DEFAULT FALSE, INDEX | Featured job |
| creator_id | INTEGER | FK(users.id), NULL | |
| created | TIMESTAMP TZ | DEFAULT NOW(), INDEX | |
| updated | TIMESTAMP TZ | DEFAULT NOW() | |

**Status Values**:
- draft
- review
- approved
- rejected
- archived
- removed
- expired

**Indexes**:
- `ix_jobs_status` (status)
- `ix_jobs_country` (country)
- `ix_jobs_featured` (is_featured)
- `ix_jobs_created` (created DESC)

## Association Tables

### event_category_associations

**Purpose**: Many-to-many events to categories

| Column | Type | Constraints |
|--------|------|-------------|
| event_id | INTEGER | FK(events.id), PRIMARY KEY |
| category_id | INTEGER | FK(event_categories.id), PRIMARY KEY |

### job_type_associations

**Purpose**: Many-to-many jobs to types

| Column | Type | Constraints |
|--------|------|-------------|
| job_id | INTEGER | FK(jobs.id), PRIMARY KEY |
| job_type_id | INTEGER | FK(job_types.id), PRIMARY KEY |

## Migration Notes

### Django to SQLAlchemy Field Mapping

| Django Field | SQLAlchemy Type | Notes |
|--------------|----------------|-------|
| AutoField | Integer, primary_key=True | Auto-increment |
| CharField(max_length=N) | String(N) | |
| TextField | Text | |
| BooleanField | Boolean | |
| DateTimeField | DateTime(timezone=True) | Always use timezone-aware |
| IntegerField | Integer | |
| EmailField | String(254) | Max email length per RFC |
| URLField | String(500) | Or Text for unlimited |
| SlugField | String(200) | With unique=True |
| ForeignKey | ForeignKey() + relationship() | |
| ManyToManyField | Association table + relationship() | |
| JSONField | JSON | PostgreSQL native JSON |

### Default Value Migration

```python
# Django
created = models.DateTimeField(default=timezone.now)

# SQLAlchemy (server-side default)
created: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now()
)

# Django
is_active = models.BooleanField(default=True)

# SQLAlchemy (application default)
is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

### Index Migration

```python
# Django
class Meta:
    indexes = [
        models.Index(fields=['path', 'is_published']),
    ]

# SQLAlchemy
__table_args__ = (
    Index('ix_pages_path_published', 'path', 'is_published'),
)
```

### Unique Constraint Migration

```python
# Django
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['os', 'release'],
            condition=models.Q(download_button=True),
            name="only_one_download_per_os_per_release"
        ),
    ]

# SQLAlchemy
__table_args__ = (
    UniqueConstraint(
        'os_id', 'release_id',
        name='uq_one_download_per_os_per_release',
        postgresql_where=text('download_button = true')
    ),
)
```

## Schema Evolution Strategy

### Phase 1: Core Tables
1. users
2. memberships
3. auth_tokens
4. sessions

### Phase 2: Content Tables
1. pages
2. page_images
3. page_documents
4. boxes

### Phase 3: Feature Tables
1. releases
2. operating_systems
3. release_files
4. calendars
5. events
6. event_locations
7. event_categories

### Phase 4: Community Tables
1. jobs
2. job_categories
3. job_types
4. posts (community)
5. photos
6. videos

### Phase 5: Organization Tables
1. sponsors
2. sponsorships
3. benefits
4. nominations
5. minutes
6. work_groups

## Performance Optimization

### Strategic Indexes

```sql
-- High-traffic queries
CREATE INDEX ix_releases_latest ON releases (version, is_latest) WHERE is_published = TRUE;
CREATE INDEX ix_jobs_approved ON jobs (created DESC) WHERE status = 'approved';
CREATE INDEX ix_events_upcoming ON events (id) WHERE featured = TRUE;

-- Full-text search (PostgreSQL)
CREATE INDEX ix_pages_content_fts ON pages USING gin(to_tsvector('english', content));
CREATE INDEX ix_jobs_description_fts ON jobs USING gin(to_tsvector('english', description));
```

### Query Patterns

```python
# Efficient eager loading
from sqlalchemy.orm import selectinload

stmt = (
    select(Release)
    .options(selectinload(Release.files))
    .where(Release.is_latest == True)
)

# Pagination with count
from sqlalchemy import func

stmt = select(Job).where(Job.status == 'approved').limit(20).offset(0)
count_stmt = select(func.count()).select_from(Job).where(Job.status == 'approved')
```

---

**Document Path**: `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/docs/architecture/DATABASE_SCHEMA.md`
