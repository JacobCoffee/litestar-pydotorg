"""SQLAdmin ModelView classes for all domain models."""

from __future__ import annotations

from sqladmin import ModelView
from sqladmin_litestar_plugin.ext.advanced_alchemy import AuditModelView

from pydotorg.domains.blogs.models import BlogEntry, Feed, FeedAggregate, RelatedBlog
from pydotorg.domains.events.models import Calendar, Event, EventCategory, EventLocation, EventOccurrence
from pydotorg.domains.jobs.models import Job, JobCategory, JobReviewComment, JobType
from pydotorg.domains.pages.models import DocumentFile, Image, Page
from pydotorg.domains.sponsors.models import Sponsor, Sponsorship, SponsorshipLevel
from pydotorg.domains.users.models import Membership, User, UserGroup


class UserAdmin(AuditModelView, model=User):
    """Admin view for User model."""

    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"

    column_list = [
        User.id,
        User.username,
        User.email,
        User.first_name,
        User.last_name,
        User.is_active,
        User.is_staff,
        User.is_superuser,
        User.email_verified,
        User.oauth_provider,
        User.date_joined,
        User.last_login,
    ]
    column_searchable_list = [User.username, User.email, User.first_name, User.last_name]
    column_sortable_list = [User.id, User.username, User.email, User.date_joined, User.last_login]
    column_default_sort = [(User.date_joined, True)]

    form_excluded_columns = [User.password_hash, User.sponsorships]


class MembershipAdmin(AuditModelView, model=Membership):
    """Admin view for Membership model."""

    name = "Membership"
    name_plural = "Memberships"
    icon = "fa-solid fa-id-card"

    column_list = [
        Membership.id,
        Membership.user_id,
        Membership.membership_type,
        Membership.legal_name,
        Membership.preferred_name,
        Membership.city,
        Membership.country,
        Membership.votes,
        Membership.last_vote_affirmation,
    ]
    column_searchable_list = [Membership.legal_name, Membership.preferred_name, Membership.city, Membership.country]
    column_sortable_list = [Membership.membership_type, Membership.last_vote_affirmation]


class UserGroupAdmin(AuditModelView, model=UserGroup):
    """Admin view for UserGroup model."""

    name = "User Group"
    name_plural = "User Groups"
    icon = "fa-solid fa-users-gear"

    column_list = [
        UserGroup.id,
        UserGroup.name,
        UserGroup.location,
        UserGroup.url_type,
        UserGroup.start_date,
        UserGroup.approved,
        UserGroup.trusted,
    ]
    column_searchable_list = [UserGroup.name, UserGroup.location]
    column_sortable_list = [UserGroup.name, UserGroup.start_date, UserGroup.approved]


class JobAdmin(ModelView, model=Job):
    """Admin view for Job model."""

    name = "Job"
    name_plural = "Jobs"
    icon = "fa-solid fa-briefcase"

    column_list = [
        Job.id,
        Job.company_name,
        Job.job_title,
        Job.city,
        Job.country,
        Job.status,
        Job.telecommuting,
        Job.expires,
        Job.created_at,
    ]
    column_searchable_list = [Job.company_name, Job.job_title, Job.city, Job.country]
    column_sortable_list = [Job.company_name, Job.job_title, Job.status, Job.expires, Job.created_at]
    column_default_sort = [(Job.created_at, True)]


class JobTypeAdmin(ModelView, model=JobType):
    """Admin view for JobType model."""

    name = "Job Type"
    name_plural = "Job Types"
    icon = "fa-solid fa-tag"

    column_list = [JobType.id, JobType.name, JobType.slug]
    column_searchable_list = [JobType.name, JobType.slug]
    column_sortable_list = [JobType.name]


class JobCategoryAdmin(ModelView, model=JobCategory):
    """Admin view for JobCategory model."""

    name = "Job Category"
    name_plural = "Job Categories"
    icon = "fa-solid fa-tags"

    column_list = [JobCategory.id, JobCategory.name, JobCategory.slug]
    column_searchable_list = [JobCategory.name, JobCategory.slug]
    column_sortable_list = [JobCategory.name]


class JobReviewCommentAdmin(ModelView, model=JobReviewComment):
    """Admin view for JobReviewComment model."""

    name = "Job Review Comment"
    name_plural = "Job Review Comments"
    icon = "fa-solid fa-comment"

    column_list = [
        JobReviewComment.id,
        JobReviewComment.job_id,
        JobReviewComment.creator_id,
        JobReviewComment.comment,
        JobReviewComment.created_at,
    ]
    column_searchable_list = [JobReviewComment.comment]
    column_sortable_list = [JobReviewComment.created_at]
    column_default_sort = [(JobReviewComment.created_at, True)]


class EventAdmin(ModelView, model=Event):
    """Admin view for Event model."""

    name = "Event"
    name_plural = "Events"
    icon = "fa-solid fa-calendar"

    column_list = [
        Event.id,
        Event.title,
        Event.calendar_id,
        Event.venue_id,
        Event.featured,
        Event.created,
    ]
    column_searchable_list = [Event.title, Event.name]
    column_sortable_list = [Event.title, Event.created, Event.featured]
    column_default_sort = [(Event.created, True)]


class CalendarAdmin(ModelView, model=Calendar):
    """Admin view for Calendar model."""

    name = "Calendar"
    name_plural = "Calendars"
    icon = "fa-solid fa-calendar-days"

    column_list = [Calendar.id, Calendar.name, Calendar.slug, Calendar.created]
    column_searchable_list = [Calendar.name, Calendar.slug]
    column_sortable_list = [Calendar.name, Calendar.created]


class EventCategoryAdmin(ModelView, model=EventCategory):
    """Admin view for EventCategory model."""

    name = "Event Category"
    name_plural = "Event Categories"
    icon = "fa-solid fa-list"

    column_list = [EventCategory.id, EventCategory.name, EventCategory.slug, EventCategory.calendar_id]
    column_searchable_list = [EventCategory.name, EventCategory.slug]
    column_sortable_list = [EventCategory.name]


class EventLocationAdmin(ModelView, model=EventLocation):
    """Admin view for EventLocation model."""

    name = "Event Location"
    name_plural = "Event Locations"
    icon = "fa-solid fa-location-dot"

    column_list = [EventLocation.id, EventLocation.name, EventLocation.address, EventLocation.url]
    column_searchable_list = [EventLocation.name, EventLocation.address]
    column_sortable_list = [EventLocation.name]


class EventOccurrenceAdmin(ModelView, model=EventOccurrence):
    """Admin view for EventOccurrence model."""

    name = "Event Occurrence"
    name_plural = "Event Occurrences"
    icon = "fa-solid fa-calendar-check"

    column_list = [
        EventOccurrence.id,
        EventOccurrence.event_id,
        EventOccurrence.dt_start,
        EventOccurrence.dt_end,
        EventOccurrence.all_day,
    ]
    column_sortable_list = [EventOccurrence.dt_start, EventOccurrence.dt_end]
    column_default_sort = [(EventOccurrence.dt_start, True)]


class SponsorAdmin(ModelView, model=Sponsor):
    """Admin view for Sponsor model."""

    name = "Sponsor"
    name_plural = "Sponsors"
    icon = "fa-solid fa-handshake"

    column_list = [
        Sponsor.id,
        Sponsor.name,
        Sponsor.slug,
        Sponsor.city,
        Sponsor.country,
        Sponsor.created,
    ]
    column_searchable_list = [Sponsor.name, Sponsor.slug, Sponsor.city, Sponsor.country]
    column_sortable_list = [Sponsor.name, Sponsor.created]
    column_default_sort = [(Sponsor.created, True)]


class SponsorshipAdmin(ModelView, model=Sponsorship):
    """Admin view for Sponsorship model."""

    name = "Sponsorship"
    name_plural = "Sponsorships"
    icon = "fa-solid fa-file-contract"

    column_list = [
        Sponsorship.id,
        Sponsorship.sponsor_id,
        Sponsorship.level_id,
        Sponsorship.status,
        Sponsorship.start_date,
        Sponsorship.end_date,
        Sponsorship.year,
        Sponsorship.sponsorship_fee,
        Sponsorship.created,
    ]
    column_sortable_list = [Sponsorship.status, Sponsorship.start_date, Sponsorship.end_date, Sponsorship.created]
    column_default_sort = [(Sponsorship.created, True)]


class SponsorshipLevelAdmin(ModelView, model=SponsorshipLevel):
    """Admin view for SponsorshipLevel model."""

    name = "Sponsorship Level"
    name_plural = "Sponsorship Levels"
    icon = "fa-solid fa-layer-group"

    column_list = [
        SponsorshipLevel.id,
        SponsorshipLevel.name,
        SponsorshipLevel.slug,
        SponsorshipLevel.order,
        SponsorshipLevel.sponsorship_amount,
        SponsorshipLevel.logo_dimension,
    ]
    column_searchable_list = [SponsorshipLevel.name, SponsorshipLevel.slug]
    column_sortable_list = [SponsorshipLevel.order, SponsorshipLevel.sponsorship_amount]
    column_default_sort = [(SponsorshipLevel.order, False)]


class PageAdmin(ModelView, model=Page):
    """Admin view for Page model."""

    name = "Page"
    name_plural = "Pages"
    icon = "fa-solid fa-file"

    column_list = [
        Page.id,
        Page.title,
        Page.path,
        Page.content_type,
        Page.is_published,
        Page.created,
        Page.updated,
    ]
    column_searchable_list = [Page.title, Page.path, Page.keywords]
    column_sortable_list = [Page.title, Page.path, Page.created, Page.updated]
    column_default_sort = [(Page.updated, True)]


class ImageAdmin(ModelView, model=Image):
    """Admin view for Image model."""

    name = "Page Image"
    name_plural = "Page Images"
    icon = "fa-solid fa-image"

    column_list = [Image.id, Image.page_id, Image.image, Image.created_at]
    column_sortable_list = [Image.created_at]


class DocumentFileAdmin(ModelView, model=DocumentFile):
    """Admin view for DocumentFile model."""

    name = "Page Document"
    name_plural = "Page Documents"
    icon = "fa-solid fa-file-pdf"

    column_list = [DocumentFile.id, DocumentFile.page_id, DocumentFile.document, DocumentFile.created_at]
    column_sortable_list = [DocumentFile.created_at]


class BlogEntryAdmin(ModelView, model=BlogEntry):
    """Admin view for BlogEntry model."""

    name = "Blog Entry"
    name_plural = "Blog Entries"
    icon = "fa-solid fa-blog"

    column_list = [
        BlogEntry.id,
        BlogEntry.title,
        BlogEntry.feed_id,
        BlogEntry.url,
        BlogEntry.pub_date,
        BlogEntry.created_at,
    ]
    column_searchable_list = [BlogEntry.title, BlogEntry.summary]
    column_sortable_list = [BlogEntry.title, BlogEntry.pub_date, BlogEntry.created_at]
    column_default_sort = [(BlogEntry.pub_date, True)]


class FeedAdmin(ModelView, model=Feed):
    """Admin view for Feed model."""

    name = "Feed"
    name_plural = "Feeds"
    icon = "fa-solid fa-rss"

    column_list = [
        Feed.id,
        Feed.name,
        Feed.website_url,
        Feed.feed_url,
        Feed.last_fetched,
        Feed.is_active,
        Feed.created_at,
    ]
    column_searchable_list = [Feed.name, Feed.website_url, Feed.feed_url]
    column_sortable_list = [Feed.name, Feed.last_fetched, Feed.is_active]


class FeedAggregateAdmin(ModelView, model=FeedAggregate):
    """Admin view for FeedAggregate model."""

    name = "Feed Aggregate"
    name_plural = "Feed Aggregates"
    icon = "fa-solid fa-layer-group"

    column_list = [FeedAggregate.id, FeedAggregate.name, FeedAggregate.slug, FeedAggregate.created_at]
    column_searchable_list = [FeedAggregate.name, FeedAggregate.slug]
    column_sortable_list = [FeedAggregate.name]


class RelatedBlogAdmin(ModelView, model=RelatedBlog):
    """Admin view for RelatedBlog model."""

    name = "Related Blog"
    name_plural = "Related Blogs"
    icon = "fa-solid fa-link"

    column_list = [
        RelatedBlog.id,
        RelatedBlog.blog_name,
        RelatedBlog.blog_website,
        RelatedBlog.created_at,
    ]
    column_searchable_list = [RelatedBlog.blog_name, RelatedBlog.blog_website]
    column_sortable_list = [RelatedBlog.blog_name]


__all__ = [
    "BlogEntryAdmin",
    "CalendarAdmin",
    "DocumentFileAdmin",
    "EventAdmin",
    "EventCategoryAdmin",
    "EventLocationAdmin",
    "EventOccurrenceAdmin",
    "FeedAdmin",
    "FeedAggregateAdmin",
    "ImageAdmin",
    "JobAdmin",
    "JobCategoryAdmin",
    "JobReviewCommentAdmin",
    "JobTypeAdmin",
    "MembershipAdmin",
    "PageAdmin",
    "RelatedBlogAdmin",
    "SponsorAdmin",
    "SponsorshipAdmin",
    "SponsorshipLevelAdmin",
    "UserAdmin",
    "UserGroupAdmin",
]
