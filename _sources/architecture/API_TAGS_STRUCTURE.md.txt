:orphan:

# Optimal API Documentation Tag Structure

This document defines the recommended OpenAPI tag hierarchy for the Python.org API documentation, optimized for developer experience in Scalar UI.

## Design Principles

1. **Logical Grouping**: Related endpoints organized into coherent, discoverable categories
2. **User Journey**: Tags ordered by typical developer workflow (auth → users → content → discovery)
3. **Clarity**: Consistent naming with Title Case spaces for maximum readability in Scalar
4. **Admin Separation**: Administrative endpoints clearly separated and lower priority
5. **Exclusions**: Render controllers excluded from public API documentation

## Recommended Tag Structure

### Core API (Authentication & User Management)

#### 1. Authentication
- **Description**: User authentication, login, registration, and token management
- **Controllers**: `users/auth_controller.py`
- **Endpoints**: Login, register, token refresh, logout, password reset

#### 2. Users
- **Description**: User account management, profiles, and account operations
- **Controllers**: `users/controllers.py:UserController`
- **Endpoints**: List users, get user, create user, update user, deactivate/reactivate account

#### 3. User Memberships
- **Description**: User membership types and membership status management
- **Controllers**: `users/controllers.py:MembershipController`
- **Endpoints**: List memberships, get membership, create/update/delete membership

#### 4. User Groups
- **Description**: User group management, approval, and trust status
- **Controllers**: `users/controllers.py:UserGroupController`
- **Endpoints**: List groups, create/update/delete groups, approve/revoke approval, trust management

### Content Management

#### 5. Pages
- **Description**: Static pages and page management
- **Controllers**: `pages/controllers.py:PageController`
- **Endpoints**: List pages, get page by ID/slug, create/update/delete pages

#### 6. Documents
- **Description**: Documentation files and document management
- **Controllers**: `docs/controllers.py`
- **Endpoints**: List documents, get document, create/update/delete documents

#### 7. Images
- **Description**: Image assets and image management
- **Controllers**: `images/controllers.py` (if exists)
- **Endpoints**: List images, upload, delete images

#### 8. Banners
- **Description**: Website banners and promotional content
- **Controllers**: `banners/controllers.py`
- **Endpoints**: List banners, get banner, create/update/delete banners

#### 9. Code Samples
- **Description**: Code examples and sample snippets
- **Controllers**: `codesamples/controllers.py`
- **Endpoints**: List samples, get sample, create/update/delete samples

### Downloads & Releases

#### 10. Operating Systems
- **Description**: Supported operating systems for Python downloads
- **Controllers**: `downloads/controllers.py:OSController`
- **Endpoints**: List OS, get OS by ID/slug, create/delete OS

#### 11. Python Releases
- **Description**: Python version releases and release information
- **Controllers**: `downloads/controllers.py:ReleaseController`
- **Endpoints**: List releases, get release, create/update/delete releases, latest version endpoint

#### 12. Release Files
- **Description**: Download files associated with Python releases
- **Controllers**: `downloads/controllers.py:ReleaseFileController`
- **Endpoints**: List files, get file, upload/delete file

### Community & Events

#### 13. Events
- **Description**: Python events and conference information
- **Controllers**: `events/controllers.py:EventController` (public endpoints)
- **Endpoints**: List events, get event, upcoming events, event details

#### 14. Event Calendars
- **Description**: Event calendars and calendar management
- **Controllers**: `events/controllers.py:CalendarController`
- **Endpoints**: List calendars, get calendar by ID/slug, create/update/delete calendars

#### 15. Event Categories
- **Description**: Event type categories and classifications
- **Controllers**: `events/controllers.py:EventCategoryController`
- **Endpoints**: List categories, get category, create/update/delete categories

#### 16. Event Locations
- **Description**: Physical venues and event locations
- **Controllers**: `events/controllers.py:EventLocationController`
- **Endpoints**: List locations, get location, create/update/delete locations

#### 17. Event Occurrences
- **Description**: Specific event instances and scheduling
- **Controllers**: `events/controllers.py:EventOccurrenceController`
- **Endpoints**: List occurrences, get occurrence, create/update/delete occurrences

#### 18. User Groups & Communities
- **Description**: Community groups and member organizations
- **Controllers**: `community/controllers.py`
- **Endpoints**: List groups, get group, community discovery

#### 19. Community Content
- **Description**: Community-contributed content (posts, photos, videos, links)
- **Controllers**: `community/controllers.py` (multiple sub-controllers)
- **Endpoints**:
  - Community Posts: List/create/delete posts
  - Community Photos: List/upload/delete photos
  - Community Videos: List/add/delete videos
  - Community Links: List/submit/delete links

### Blogs & Content Discovery

#### 20. Blogs
- **Description**: Blog posts and blog entries
- **Controllers**: `blogs/controllers.py`
- **Endpoints**: List blog entries, get entry, create/update/delete entries

#### 21. Blog Feeds
- **Description**: RSS feeds and feed aggregation
- **Controllers**: `blogs/controllers.py:FeedController`
- **Endpoints**: List feeds, get feed, create/update/delete feeds, feed aggregation

#### 22. Success Stories
- **Description**: User success stories and testimonials
- **Controllers**: `successstories/controllers.py`
- **Endpoints**: List stories, get story, create/update/delete stories

#### 23. Success Story Categories
- **Description**: Success story categories and classifications
- **Controllers**: `successstories/controllers.py`
- **Endpoints**: List categories, get category, create/update/delete categories

### Jobs & Opportunities

#### 24. Jobs
- **Description**: Python job listings and employment opportunities
- **Controllers**: `jobs/controllers.py:JobController`
- **Endpoints**: List jobs, get job, search jobs, post job listing

#### 25. Job Types
- **Description**: Job type categories (contract, full-time, part-time, etc.)
- **Controllers**: `jobs/controllers.py:JobTypeController`
- **Endpoints**: List types, get type, create/update/delete types

#### 26. Job Categories
- **Description**: Job industry and role categories
- **Controllers**: `jobs/controllers.py:JobCategoryController`
- **Endpoints**: List categories, get category, create/update/delete categories

#### 27. Job Review Comments
- **Description**: Job listing review comments and moderation
- **Controllers**: `jobs/controllers.py:JobReviewCommentController`
- **Endpoints**: List comments, get comment, add/delete comments

### Business & Sponsorship

#### 28. Sponsors
- **Description**: Python organizations and sponsor information
- **Controllers**: `sponsors/controllers.py:SponsorController`
- **Endpoints**: List sponsors, get sponsor, sponsor details

#### 29. Sponsorship Levels
- **Description**: Sponsorship tier definitions and benefits
- **Controllers**: `sponsors/controllers.py:SponsorshipLevelController`
- **Endpoints**: List levels, get level, create/update/delete levels

#### 30. Sponsorships
- **Description**: Active sponsorship relationships and agreements
- **Controllers**: `sponsors/controllers.py:SponsorshipController`
- **Endpoints**: List sponsorships, get sponsorship, create/update/delete sponsorships

#### 31. Companies
- **Description**: Company profiles and organization data
- **Controllers**: `companies/controllers.py`
- **Endpoints**: List companies, get company, company search

### Governance & Meetings

#### 32. Work Groups
- **Description**: Python Enhancement Proposal (PEP) work groups
- **Controllers**: `work_groups/controllers.py`
- **Endpoints**: List groups, get group, group membership

#### 33. Meeting Minutes
- **Description**: Meeting notes and minutes archives
- **Controllers**: `minutes/controllers.py`
- **Endpoints**: List minutes, get minutes, upload/archive minutes

#### 34. Nominations
- **Description**: Award nominations and election cycles
- **Controllers**: `nominations/controllers.py:NominationController`
- **Endpoints**: List nominations, get nomination, submit nomination

#### 35. Nominees
- **Description**: Nominated individuals and candidates
- **Controllers**: `nominations/controllers.py:NomineeController`
- **Endpoints**: List nominees, get nominee details

#### 36. Elections
- **Description**: Election information and voting
- **Controllers**: `nominations/controllers.py:ElectionController`
- **Endpoints**: List elections, get election, voting endpoints (if applicable)

### Discovery & Search

#### 37. Search
- **Description**: Full-text and faceted search across platform
- **Controllers**: `search/controllers.py:SearchController`
- **Endpoints**: Global search, faceted search, search suggestions, autocomplete

### Mailing & Notifications

#### 38. Mailing Lists
- **Description**: Email list subscriptions and management
- **Controllers**: `mailing/controllers.py`
- **Endpoints**: Subscribe, unsubscribe, list info, preference management

### Administration (Grouped Under Admin Umbrella)

#### 39. Admin Dashboard
- **Description**: Administrative dashboard and system overview
- **Controllers**: `admin/controllers/dashboard.py`
- **Endpoints**: Dashboard stats, system health, overview data

#### 40. Admin Users
- **Description**: Administrative user management
- **Controllers**: `admin/controllers/users.py`
- **Endpoints**: List/manage users, view user activity, permissions

#### 41. Admin Pages
- **Description**: Administrative page management
- **Controllers**: `admin/controllers/pages.py`
- **Endpoints**: Manage pages, bulk operations, publication control

#### 42. Admin Events
- **Description**: Administrative event management
- **Controllers**: `admin/controllers/events.py`
- **Endpoints**: Manage events, approve submissions, moderate content

#### 43. Admin Jobs
- **Description**: Administrative job listing management
- **Controllers**: `admin/controllers/jobs.py`
- **Endpoints**: Moderate listings, approve jobs, manage postings

#### 44. Admin Sponsors
- **Description**: Administrative sponsor management
- **Controllers**: `admin/controllers/sponsors.py`
- **Endpoints**: Manage sponsors, sponsorships, agreements

#### 45. Admin Blogs
- **Description**: Administrative blog management
- **Controllers**: `admin/controllers/blogs.py`
- **Endpoints**: Manage blog entries, moderate comments, publishing control

#### 46. Admin Logs
- **Description**: System logging and audit trails
- **Controllers**: `admin/controllers/logs.py`
- **Endpoints**: View logs, audit trails, activity history

#### 47. Admin Email Templates
- **Description**: Email template management and customization
- **Controllers**: `admin/controllers/email_templates.py` (or via logs controller)
- **Endpoints**: List templates, get template, create/update/delete templates, preview

#### 48. Admin Email Logs
- **Description**: Email delivery logs and status tracking
- **Controllers**: `admin/controllers/email_logs.py` (or via logs controller)
- **Endpoints**: View email logs, delivery status, resend emails

#### 49. Admin Tasks
- **Description**: Background task management and scheduling
- **Controllers**: `admin/controllers/tasks.py`
- **Endpoints**: List tasks, get task status, trigger tasks, view results

#### 50. Admin Settings
- **Description**: System configuration and application settings
- **Controllers**: `admin/controllers/settings.py`
- **Endpoints**: Get settings, update settings, reset to defaults

## Implementation Guidelines

### OpenAPI Tag Definition Structure

Each tag should be defined in the Litestar OpenAPI configuration with:

```python
Tag(
    name="Tag Name",
    description="Concise description of what endpoints in this group do",
    external_docs=ExternalDocumentation(
        url="https://docs.python.org/path/to/docs",
        description="Learn more about this feature"
    ) if applicable
)
```

### Controller Implementation

Update controller tags from the current structure:

```python
# Before (too granular)
class JobTypeController(Controller):
    tags = ["job-types"]

# After (grouped under primary resource)
class JobTypeController(Controller):
    tags = ["Job Types"]
```

### Hide Render Endpoints from Public API

Mark render controllers to exclude from public documentation:

```python
# Render controllers should NOT appear in public API docs
class JobRenderController(Controller):
    tags = ["internal"]  # or use OpenAPI exclude mechanism
```

## Ordering Strategy for Scalar UI

Tags are presented to users in the order they appear in the OpenAPI tags array. Recommended order:

1. **Authentication** - Required first by developers
2. **Users** → **User Memberships** → **User Groups** - User management flow
3. **Pages** → **Documents** → **Images** → **Banners** → **Code Samples** - Content resources
4. **Operating Systems** → **Python Releases** → **Release Files** - Download-related
5. **Events** → **Calendars** → **Categories** → **Locations** → **Occurrences** - Event management flow
6. **User Groups & Communities** → **Community Content** - Community discovery
7. **Blogs** → **Blog Feeds** → **Success Stories** - Content discovery
8. **Jobs** → **Job Types** → **Job Categories** → **Job Review Comments** - Job management
9. **Sponsors** → **Sponsorship Levels** → **Sponsorships** → **Companies** - Sponsorship flow
10. **Work Groups** → **Meeting Minutes** → **Nominations** → **Nominees** → **Elections** - Governance
11. **Search** - Aggregate discovery
12. **Mailing Lists** - Communication
13. **Admin Dashboard** → **Admin Users** → **Admin Pages** → ... - Administrative tools

## Benefits of This Structure

- **Reduced Cognitive Load**: Developers see 50 focused tags instead of 100+ fragmented ones
- **Logical Flow**: Follows typical developer journey from auth → content → features
- **Related Grouping**: Sub-resources (e.g., Event → Calendar → Category) are adjacent
- **Admin Isolated**: Administrative endpoints clearly separated and deprioritized
- **Render Excluded**: Internal render controllers hidden from public documentation
- **Scalable**: Easy to add new tags to appropriate categories as platform grows
- **Readable**: Title Case with spaces much more readable in Scalar UI than kebab-case

## Migration Notes

1. Update all controller `tags` assignments to match this structure
2. Configure OpenAPI tags list in main application config
3. Add `include_in_schema=False` to render controllers or mark them "internal"
4. Test in Scalar UI to verify grouping and ordering
5. Consider adding brief external documentation links where applicable
6. Monitor usage patterns to validate grouping logic
