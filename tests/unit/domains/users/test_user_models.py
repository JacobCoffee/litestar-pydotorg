"""Unit tests for User model."""

from __future__ import annotations

from pydotorg.domains.users.models import (
    EmailPrivacy,
    MembershipType,
    SearchVisibility,
    User,
    UserGroupType,
)


class TestUserModel:
    def test_create_user(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"

    def test_user_with_explicit_defaults(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            first_name="",
            last_name="",
            is_active=True,
            is_staff=False,
            is_superuser=False,
            email_verified=False,
            bio="",
            search_visibility=SearchVisibility.PUBLIC,
            email_privacy=EmailPrivacy.PRIVATE,
            public_profile=True,
        )
        assert user.first_name == ""
        assert user.last_name == ""
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.email_verified is False
        assert user.bio == ""
        assert user.search_visibility == SearchVisibility.PUBLIC
        assert user.email_privacy == EmailPrivacy.PRIVATE
        assert user.public_profile is True

    def test_full_name_with_both_names(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
        )
        assert user.full_name == "John Doe"

    def test_full_name_with_first_only(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            first_name="John",
            last_name="",
        )
        assert user.full_name == "John"

    def test_full_name_with_last_only(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            first_name="",
            last_name="Doe",
        )
        assert user.full_name == "Doe"

    def test_full_name_empty(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            first_name="",
            last_name="",
        )
        assert user.full_name == ""

    def test_full_name_with_whitespace(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            first_name="  John  ",
            last_name="  Doe  ",
        )
        assert user.full_name.strip() == "John     Doe"

    def test_has_membership_false(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
        )
        assert user.has_membership is False

    def test_search_visibility_explicit(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            search_visibility=SearchVisibility.PRIVATE,
        )
        assert user.search_visibility == SearchVisibility.PRIVATE

    def test_email_privacy_explicit(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            email_privacy=EmailPrivacy.NEVER,
        )
        assert user.email_privacy == EmailPrivacy.NEVER

    def test_oauth_fields(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            oauth_provider="github",
            oauth_id="12345",
        )
        assert user.oauth_provider == "github"
        assert user.oauth_id == "12345"

    def test_staff_and_superuser(self) -> None:
        user = User(
            username="admin",
            email="admin@example.com",
            is_staff=True,
            is_superuser=True,
        )
        assert user.is_staff is True
        assert user.is_superuser is True


class TestSearchVisibilityEnum:
    def test_enum_values(self) -> None:
        assert SearchVisibility.PUBLIC.value == "public"
        assert SearchVisibility.PRIVATE.value == "private"

    def test_enum_members(self) -> None:
        members = list(SearchVisibility)
        assert len(members) == 2
        assert SearchVisibility.PUBLIC in members
        assert SearchVisibility.PRIVATE in members


class TestEmailPrivacyEnum:
    def test_enum_values(self) -> None:
        assert EmailPrivacy.PUBLIC.value == "public"
        assert EmailPrivacy.PRIVATE.value == "private"
        assert EmailPrivacy.NEVER.value == "never"

    def test_enum_members(self) -> None:
        members = list(EmailPrivacy)
        assert len(members) == 3
        assert EmailPrivacy.PUBLIC in members
        assert EmailPrivacy.PRIVATE in members
        assert EmailPrivacy.NEVER in members


class TestMembershipTypeEnum:
    def test_enum_values(self) -> None:
        assert MembershipType.BASIC.value == "basic"
        assert MembershipType.SUPPORTING.value == "supporting"
        assert MembershipType.SPONSOR.value == "sponsor"
        assert MembershipType.MANAGING.value == "managing"
        assert MembershipType.CONTRIBUTING.value == "contributing"
        assert MembershipType.FELLOW.value == "fellow"

    def test_enum_members(self) -> None:
        members = list(MembershipType)
        assert len(members) == 6


class TestUserGroupTypeEnum:
    def test_enum_values(self) -> None:
        assert UserGroupType.MEETUP.value == "meetup"
        assert UserGroupType.DISTRIBUTION_LIST.value == "distribution_list"
        assert UserGroupType.OTHER.value == "other"

    def test_enum_members(self) -> None:
        members = list(UserGroupType)
        assert len(members) == 3
