"""User domain Pydantic schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from pydotorg.domains.users.models import EmailPrivacy, MembershipType, SearchVisibility, UserGroupType

if TYPE_CHECKING:
    import datetime
    from uuid import UUID

MIN_PASSWORD_LENGTH = 8


class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: Annotated[str, Field(min_length=1, max_length=150)]
    email: EmailStr
    first_name: Annotated[str, Field(max_length=150)] = ""
    last_name: Annotated[str, Field(max_length=150)] = ""
    bio: str = ""
    search_visibility: SearchVisibility = SearchVisibility.PUBLIC
    email_privacy: EmailPrivacy = EmailPrivacy.PRIVATE
    public_profile: bool = True


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: Annotated[str, Field(min_length=8, max_length=255)]

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < MIN_PASSWORD_LENGTH:
            msg = f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
            raise ValueError(msg)
        return v


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""

    email: EmailStr | None = None
    first_name: Annotated[str, Field(max_length=150)] | None = None
    last_name: Annotated[str, Field(max_length=150)] | None = None
    bio: str | None = None
    search_visibility: SearchVisibility | None = None
    email_privacy: EmailPrivacy | None = None
    public_profile: bool | None = None


class UserRead(UserBase):
    """Schema for reading user data."""

    id: UUID
    is_active: bool
    is_staff: bool
    is_superuser: bool
    date_joined: datetime.datetime
    last_login: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()


class UserPublic(BaseModel):
    """Public user schema with limited fields."""

    id: UUID
    username: str
    first_name: str
    last_name: str
    bio: str

    model_config = ConfigDict(from_attributes=True)

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()


class MembershipBase(BaseModel):
    """Base membership schema."""

    membership_type: MembershipType = MembershipType.BASIC
    legal_name: Annotated[str, Field(max_length=255)] = ""
    preferred_name: Annotated[str, Field(max_length=255)] = ""
    email_address: EmailStr | str = ""
    city: Annotated[str, Field(max_length=100)] = ""
    region: Annotated[str, Field(max_length=100)] = ""
    country: Annotated[str, Field(max_length=100)] = ""
    postal_code: Annotated[str, Field(max_length=20)] = ""
    psf_code_of_conduct: bool = False
    psf_announcements: bool = False
    votes: bool = False


class MembershipCreate(MembershipBase):
    """Schema for creating a new membership."""

    user_id: UUID


class MembershipUpdate(BaseModel):
    """Schema for updating a membership."""

    membership_type: MembershipType | None = None
    legal_name: Annotated[str, Field(max_length=255)] | None = None
    preferred_name: Annotated[str, Field(max_length=255)] | None = None
    email_address: EmailStr | str | None = None
    city: Annotated[str, Field(max_length=100)] | None = None
    region: Annotated[str, Field(max_length=100)] | None = None
    country: Annotated[str, Field(max_length=100)] | None = None
    postal_code: Annotated[str, Field(max_length=20)] | None = None
    psf_code_of_conduct: bool | None = None
    psf_announcements: bool | None = None
    votes: bool | None = None


class MembershipRead(MembershipBase):
    """Schema for reading membership data."""

    id: UUID
    user_id: UUID
    last_vote_affirmation: datetime.date | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class UserGroupBase(BaseModel):
    """Base user group schema."""

    name: Annotated[str, Field(max_length=255)]
    location: Annotated[str, Field(max_length=255)] = ""
    url: Annotated[str, Field(max_length=500)] = ""
    url_type: UserGroupType = UserGroupType.OTHER
    approved: bool = False
    trusted: bool = False


class UserGroupCreate(UserGroupBase):
    """Schema for creating a new user group."""

    start_date: datetime.date | None = None


class UserGroupUpdate(BaseModel):
    """Schema for updating a user group."""

    name: Annotated[str, Field(max_length=255)] | None = None
    location: Annotated[str, Field(max_length=255)] | None = None
    url: Annotated[str, Field(max_length=500)] | None = None
    url_type: UserGroupType | None = None
    start_date: datetime.date | None = None
    approved: bool | None = None
    trusted: bool | None = None


class UserGroupRead(UserGroupBase):
    """Schema for reading user group data."""

    id: UUID
    start_date: datetime.date | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
