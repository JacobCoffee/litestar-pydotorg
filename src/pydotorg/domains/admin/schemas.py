"""Admin domain Pydantic schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, EmailStr

if TYPE_CHECKING:
    import datetime
    from uuid import UUID

    from pydotorg.domains.users.models import EmailPrivacy, SearchVisibility


class DashboardStats(BaseModel):
    """Dashboard statistics schema."""

    total_users: int
    active_users: int
    staff_users: int
    total_jobs: int
    pending_jobs: int
    approved_jobs: int
    total_events: int
    upcoming_events: int
    total_sponsors: int
    active_sponsors: int

    model_config = ConfigDict(from_attributes=True)


class PendingModeration(BaseModel):
    """Pending moderation items summary."""

    pending_jobs_count: int
    pending_events_count: int
    pending_sponsors_count: int
    recent_signups_count: int

    model_config = ConfigDict(from_attributes=True)


class RecentActivity(BaseModel):
    """Recent activity item."""

    id: UUID
    activity_type: str
    description: str
    timestamp: datetime.datetime
    user_id: UUID | None = None
    username: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminUserRead(BaseModel):
    """Full user data schema for admin panel."""

    id: UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    is_staff: bool
    is_superuser: bool
    email_verified: bool
    oauth_provider: str | None
    oauth_id: str | None
    date_joined: datetime.datetime
    last_login: datetime.datetime | None
    bio: str
    search_visibility: SearchVisibility
    email_privacy: EmailPrivacy
    public_profile: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()


class UserStaffUpdate(BaseModel):
    """Schema for updating user staff/admin status."""

    is_active: bool | None = None
    is_staff: bool | None = None
    is_superuser: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class SystemInfo(BaseModel):
    """System information schema."""

    python_version: str
    litestar_version: str
    database_version: str
    total_database_size: str | None
    cache_status: str
    uptime: str

    model_config = ConfigDict(from_attributes=True)


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    import datetime as _datetime
    from uuid import UUID as _UUID

    from pydotorg.domains.users.models import EmailPrivacy as _EmailPrivacy
    from pydotorg.domains.users.models import SearchVisibility as _SearchVisibility

    _types = {
        "UUID": _UUID,
        "datetime": _datetime,
        "EmailPrivacy": _EmailPrivacy,
        "SearchVisibility": _SearchVisibility,
    }
    RecentActivity.model_rebuild(_types_namespace=_types)
    AdminUserRead.model_rebuild(_types_namespace=_types)


_rebuild_models()
