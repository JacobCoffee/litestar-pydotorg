"""SQLAdmin ModelView classes for all domain models."""

from __future__ import annotations

from sqladmin import ModelView
from sqladmin_litestar_plugin.ext.advanced_alchemy import AuditModelView

from pydotorg.domains.banners.models import Banner
from pydotorg.domains.blogs.models import BlogEntry, Feed, FeedAggregate, RelatedBlog
from pydotorg.domains.codesamples.models import CodeSample
from pydotorg.domains.community.models import Link, Photo, Post, Video
from pydotorg.domains.downloads.models import OS, DownloadStatistic, Release, ReleaseFile
from pydotorg.domains.events.models import Calendar, Event, EventCategory, EventLocation, EventOccurrence
from pydotorg.domains.jobs.models import Job, JobCategory, JobReviewComment, JobType
from pydotorg.domains.mailing.models import EmailLog, EmailTemplate
from pydotorg.domains.minutes.models import Minutes
from pydotorg.domains.nominations.models import Election, Nomination, Nominee
from pydotorg.domains.pages.models import DocumentFile, Image, Page
from pydotorg.domains.sponsors.models import Sponsor, Sponsorship, SponsorshipLevel
from pydotorg.domains.successstories.models import Story, StoryCategory
from pydotorg.domains.users.models import Membership, User, UserGroup
from pydotorg.domains.work_groups.models import WorkGroup


class UserAdmin(AuditModelView, model=User):
    """Admin view for User model."""

    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"
    category = "Users"

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
    category = "Users"

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
    category = "Users"

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
    category = "Jobs"

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
    category = "Jobs"

    column_list = [JobType.id, JobType.name, JobType.slug]
    column_searchable_list = [JobType.name, JobType.slug]
    column_sortable_list = [JobType.name]


class JobCategoryAdmin(ModelView, model=JobCategory):
    """Admin view for JobCategory model."""

    name = "Job Category"
    name_plural = "Job Categories"
    icon = "fa-solid fa-tags"
    category = "Jobs"

    column_list = [JobCategory.id, JobCategory.name, JobCategory.slug]
    column_searchable_list = [JobCategory.name, JobCategory.slug]
    column_sortable_list = [JobCategory.name]


class JobReviewCommentAdmin(ModelView, model=JobReviewComment):
    """Admin view for JobReviewComment model."""

    name = "Job Review Comment"
    name_plural = "Job Review Comments"
    icon = "fa-solid fa-comment"
    category = "Jobs"

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
    category = "Events"

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
    category = "Events"

    column_list = [Calendar.id, Calendar.name, Calendar.slug, Calendar.created]
    column_searchable_list = [Calendar.name, Calendar.slug]
    column_sortable_list = [Calendar.name, Calendar.created]


class EventCategoryAdmin(ModelView, model=EventCategory):
    """Admin view for EventCategory model."""

    name = "Event Category"
    name_plural = "Event Categories"
    icon = "fa-solid fa-list"
    category = "Events"

    column_list = [EventCategory.id, EventCategory.name, EventCategory.slug, EventCategory.calendar_id]
    column_searchable_list = [EventCategory.name, EventCategory.slug]
    column_sortable_list = [EventCategory.name]


class EventLocationAdmin(ModelView, model=EventLocation):
    """Admin view for EventLocation model."""

    name = "Event Location"
    name_plural = "Event Locations"
    icon = "fa-solid fa-location-dot"
    category = "Events"

    column_list = [EventLocation.id, EventLocation.name, EventLocation.address, EventLocation.url]
    column_searchable_list = [EventLocation.name, EventLocation.address]
    column_sortable_list = [EventLocation.name]


class EventOccurrenceAdmin(ModelView, model=EventOccurrence):
    """Admin view for EventOccurrence model."""

    name = "Event Occurrence"
    name_plural = "Event Occurrences"
    icon = "fa-solid fa-calendar-check"
    category = "Events"

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
    category = "Sponsors"

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
    category = "Sponsors"

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
    category = "Sponsors"

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
    category = "Content"

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
    category = "Content"

    column_list = [Image.id, Image.page_id, Image.image, Image.created_at]
    column_sortable_list = [Image.created_at]


class DocumentFileAdmin(ModelView, model=DocumentFile):
    """Admin view for DocumentFile model."""

    name = "Page Document"
    name_plural = "Page Documents"
    icon = "fa-solid fa-file-pdf"
    category = "Content"

    column_list = [DocumentFile.id, DocumentFile.page_id, DocumentFile.document, DocumentFile.created_at]
    column_sortable_list = [DocumentFile.created_at]


class BlogEntryAdmin(ModelView, model=BlogEntry):
    """Admin view for BlogEntry model."""

    name = "Blog Entry"
    name_plural = "Blog Entries"
    icon = "fa-solid fa-blog"
    category = "Blogs"

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
    category = "Blogs"

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
    category = "Blogs"

    column_list = [FeedAggregate.id, FeedAggregate.name, FeedAggregate.slug, FeedAggregate.created_at]
    column_searchable_list = [FeedAggregate.name, FeedAggregate.slug]
    column_sortable_list = [FeedAggregate.name]


class RelatedBlogAdmin(ModelView, model=RelatedBlog):
    """Admin view for RelatedBlog model."""

    name = "Related Blog"
    name_plural = "Related Blogs"
    icon = "fa-solid fa-link"
    category = "Blogs"

    column_list = [
        RelatedBlog.id,
        RelatedBlog.blog_name,
        RelatedBlog.blog_website,
        RelatedBlog.created_at,
    ]
    column_searchable_list = [RelatedBlog.blog_name, RelatedBlog.blog_website]
    column_sortable_list = [RelatedBlog.blog_name]


class BannerAdmin(AuditModelView, model=Banner):
    """Admin view for Banner model."""

    name = "Banner"
    name_plural = "Banners"
    icon = "fa-solid fa-flag"
    category = "Content"

    column_list = [
        Banner.id,
        Banner.name,
        Banner.title,
        Banner.banner_type,
        Banner.target,
        Banner.is_active,
        Banner.is_sitewide,
        Banner.start_date,
        Banner.end_date,
    ]
    column_searchable_list = [Banner.name, Banner.title, Banner.message]
    column_sortable_list = [Banner.name, Banner.is_active, Banner.start_date, Banner.end_date]
    column_default_sort = [(Banner.created_at, True)]


class CodeSampleAdmin(AuditModelView, model=CodeSample):
    """Admin view for CodeSample model."""

    name = "Code Sample"
    name_plural = "Code Samples"
    icon = "fa-solid fa-code"
    category = "Content"

    column_list = [
        CodeSample.id,
        CodeSample.slug,
        CodeSample.is_published,
        CodeSample.creator_id,
        CodeSample.created_at,
    ]
    column_searchable_list = [CodeSample.slug, CodeSample.description]
    column_sortable_list = [CodeSample.slug, CodeSample.is_published, CodeSample.created_at]
    column_default_sort = [(CodeSample.created_at, True)]


class CommunityPostAdmin(AuditModelView, model=Post):
    """Admin view for Community Post model."""

    name = "Community Post"
    name_plural = "Community Posts"
    icon = "fa-solid fa-comments"
    category = "Community"

    column_list = [
        Post.id,
        Post.title,
        Post.slug,
        Post.content_type,
        Post.is_published,
        Post.creator_id,
        Post.created_at,
    ]
    column_searchable_list = [Post.title, Post.content]
    column_sortable_list = [Post.title, Post.is_published, Post.created_at]
    column_default_sort = [(Post.created_at, True)]


class CommunityPhotoAdmin(ModelView, model=Photo):
    """Admin view for Community Photo model."""

    name = "Community Photo"
    name_plural = "Community Photos"
    icon = "fa-solid fa-camera"
    category = "Community"

    column_list = [
        Photo.id,
        Photo.post_id,
        Photo.image,
        Photo.caption,
        Photo.creator_id,
    ]
    column_searchable_list = [Photo.caption]


class CommunityVideoAdmin(ModelView, model=Video):
    """Admin view for Community Video model."""

    name = "Community Video"
    name_plural = "Community Videos"
    icon = "fa-solid fa-video"
    category = "Community"

    column_list = [
        Video.id,
        Video.post_id,
        Video.title,
        Video.url,
        Video.creator_id,
    ]
    column_searchable_list = [Video.title, Video.url]
    column_sortable_list = [Video.title]


class CommunityLinkAdmin(ModelView, model=Link):
    """Admin view for Community Link model."""

    name = "Community Link"
    name_plural = "Community Links"
    icon = "fa-solid fa-link"
    category = "Community"

    column_list = [
        Link.id,
        Link.post_id,
        Link.title,
        Link.url,
        Link.creator_id,
    ]
    column_searchable_list = [Link.title, Link.url]
    column_sortable_list = [Link.title]


class OSAdmin(AuditModelView, model=OS):
    """Admin view for OS model."""

    name = "Operating System"
    name_plural = "Operating Systems"
    icon = "fa-solid fa-desktop"
    category = "Downloads"

    column_list = [
        OS.id,
        OS.name,
        OS.slug,
        OS.created_at,
    ]
    column_searchable_list = [OS.name, OS.slug]
    column_sortable_list = [OS.name]


class ReleaseAdmin(AuditModelView, model=Release):
    """Admin view for Release model."""

    name = "Release"
    name_plural = "Releases"
    icon = "fa-solid fa-download"
    category = "Downloads"

    column_list = [
        Release.id,
        Release.name,
        Release.slug,
        Release.version,
        Release.status,
        Release.is_latest,
        Release.is_published,
        Release.release_date,
        Release.eol_date,
    ]
    column_searchable_list = [Release.name, Release.slug]
    column_sortable_list = [Release.name, Release.is_latest, Release.is_published, Release.release_date]
    column_default_sort = [(Release.release_date, True)]


class ReleaseFileAdmin(AuditModelView, model=ReleaseFile):
    """Admin view for ReleaseFile model."""

    name = "Release File"
    name_plural = "Release Files"
    icon = "fa-solid fa-file-archive"
    category = "Downloads"

    column_list = [
        ReleaseFile.id,
        ReleaseFile.name,
        ReleaseFile.release_id,
        ReleaseFile.os_id,
        ReleaseFile.is_source,
        ReleaseFile.filesize,
        ReleaseFile.download_button,
    ]
    column_searchable_list = [ReleaseFile.name, ReleaseFile.url]
    column_sortable_list = [ReleaseFile.name, ReleaseFile.filesize]


class DownloadStatisticAdmin(AuditModelView, model=DownloadStatistic):
    """Admin view for DownloadStatistic model."""

    name = "Download Statistic"
    name_plural = "Download Statistics"
    icon = "fa-solid fa-chart-line"
    category = "Downloads"

    column_list = [
        DownloadStatistic.id,
        DownloadStatistic.release_file_id,
        DownloadStatistic.date,
        DownloadStatistic.download_count,
    ]
    column_sortable_list = [DownloadStatistic.date, DownloadStatistic.download_count]
    column_default_sort = [(DownloadStatistic.date, True)]


class EmailTemplateAdmin(AuditModelView, model=EmailTemplate):
    """Admin view for EmailTemplate model."""

    name = "Email Template"
    name_plural = "Email Templates"
    icon = "fa-solid fa-envelope-open-text"
    category = "Email"

    column_list = [
        EmailTemplate.id,
        EmailTemplate.internal_name,
        EmailTemplate.display_name,
        EmailTemplate.template_type,
        EmailTemplate.is_active,
        EmailTemplate.created_at,
    ]
    column_searchable_list = [EmailTemplate.internal_name, EmailTemplate.display_name, EmailTemplate.subject]
    column_sortable_list = [EmailTemplate.internal_name, EmailTemplate.template_type, EmailTemplate.is_active]
    column_default_sort = [(EmailTemplate.created_at, True)]


class EmailLogAdmin(AuditModelView, model=EmailLog):
    """Admin view for EmailLog model."""

    name = "Email Log"
    name_plural = "Email Logs"
    icon = "fa-solid fa-envelope"
    category = "Email"

    column_list = [
        EmailLog.id,
        EmailLog.template_name,
        EmailLog.recipient_email,
        EmailLog.subject,
        EmailLog.status,
        EmailLog.created_at,
    ]
    column_searchable_list = [EmailLog.template_name, EmailLog.recipient_email, EmailLog.subject]
    column_sortable_list = [EmailLog.template_name, EmailLog.status, EmailLog.created_at]
    column_default_sort = [(EmailLog.created_at, True)]


class MinutesAdmin(AuditModelView, model=Minutes):
    """Admin view for Minutes model."""

    name = "Minutes"
    name_plural = "Minutes"
    icon = "fa-solid fa-clipboard-list"
    category = "PSF"

    column_list = [
        Minutes.id,
        Minutes.slug,
        Minutes.date,
        Minutes.content_type,
        Minutes.is_published,
        Minutes.creator_id,
    ]
    column_searchable_list = [Minutes.slug, Minutes.content]
    column_sortable_list = [Minutes.slug, Minutes.date, Minutes.is_published]
    column_default_sort = [(Minutes.date, True)]


class ElectionAdmin(AuditModelView, model=Election):
    """Admin view for Election model."""

    name = "Election"
    name_plural = "Elections"
    icon = "fa-solid fa-vote-yea"
    category = "PSF"

    column_list = [
        Election.id,
        Election.name,
        Election.slug,
        Election.nominations_open,
        Election.nominations_close,
        Election.voting_open,
        Election.voting_close,
    ]
    column_searchable_list = [Election.name, Election.description]
    column_sortable_list = [Election.name, Election.nominations_open, Election.voting_open]
    column_default_sort = [(Election.voting_close, True)]


class NomineeAdmin(AuditModelView, model=Nominee):
    """Admin view for Nominee model."""

    name = "Nominee"
    name_plural = "Nominees"
    icon = "fa-solid fa-user-check"
    category = "PSF"

    column_list = [
        Nominee.id,
        Nominee.election_id,
        Nominee.user_id,
        Nominee.accepted,
        Nominee.created_at,
    ]
    column_sortable_list = [Nominee.accepted, Nominee.created_at]
    column_default_sort = [(Nominee.created_at, True)]


class NominationAdmin(AuditModelView, model=Nomination):
    """Admin view for Nomination model."""

    name = "Nomination"
    name_plural = "Nominations"
    icon = "fa-solid fa-hand-point-up"
    category = "PSF"

    column_list = [
        Nomination.id,
        Nomination.nominee_id,
        Nomination.nominator_id,
        Nomination.created_at,
    ]
    column_searchable_list = [Nomination.endorsement]
    column_sortable_list = [Nomination.created_at]
    column_default_sort = [(Nomination.created_at, True)]


class StoryCategoryAdmin(ModelView, model=StoryCategory):
    """Admin view for StoryCategory model."""

    name = "Story Category"
    name_plural = "Story Categories"
    icon = "fa-solid fa-folder"
    category = "Success Stories"

    column_list = [
        StoryCategory.id,
        StoryCategory.name,
        StoryCategory.slug,
    ]
    column_searchable_list = [StoryCategory.name, StoryCategory.slug]
    column_sortable_list = [StoryCategory.name]


class StoryAdmin(AuditModelView, model=Story):
    """Admin view for Story model."""

    name = "Success Story"
    name_plural = "Success Stories"
    icon = "fa-solid fa-star"
    category = "Success Stories"

    column_list = [
        Story.id,
        Story.name,
        Story.slug,
        Story.company_name,
        Story.category_id,
        Story.is_published,
        Story.featured,
        Story.created_at,
    ]
    column_searchable_list = [Story.name, Story.company_name, Story.content]
    column_sortable_list = [Story.name, Story.company_name, Story.is_published, Story.featured]
    column_default_sort = [(Story.created_at, True)]


class WorkGroupAdmin(AuditModelView, model=WorkGroup):
    """Admin view for WorkGroup model."""

    name = "Work Group"
    name_plural = "Work Groups"
    icon = "fa-solid fa-people-group"
    category = "PSF"

    column_list = [
        WorkGroup.id,
        WorkGroup.name,
        WorkGroup.slug,
        WorkGroup.active,
        WorkGroup.url,
        WorkGroup.creator_id,
    ]
    column_searchable_list = [WorkGroup.name, WorkGroup.purpose]
    column_sortable_list = [WorkGroup.name, WorkGroup.active]
    column_default_sort = [(WorkGroup.created_at, True)]


__all__ = [
    "BannerAdmin",
    "BlogEntryAdmin",
    "CalendarAdmin",
    "CodeSampleAdmin",
    "CommunityLinkAdmin",
    "CommunityPhotoAdmin",
    "CommunityPostAdmin",
    "CommunityVideoAdmin",
    "DocumentFileAdmin",
    "DownloadStatisticAdmin",
    "ElectionAdmin",
    "EmailLogAdmin",
    "EmailTemplateAdmin",
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
    "MinutesAdmin",
    "NominationAdmin",
    "NomineeAdmin",
    "OSAdmin",
    "PageAdmin",
    "RelatedBlogAdmin",
    "ReleaseAdmin",
    "ReleaseFileAdmin",
    "SponsorAdmin",
    "SponsorshipAdmin",
    "SponsorshipLevelAdmin",
    "StoryAdmin",
    "StoryCategoryAdmin",
    "UserAdmin",
    "UserGroupAdmin",
    "WorkGroupAdmin",
]
