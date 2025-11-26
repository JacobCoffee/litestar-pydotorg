"""Model unit tests."""

from __future__ import annotations

from datetime import date

from pydotorg.domains import (
    EmailPrivacy,
    Membership,
    MembershipType,
    PythonVersion,
    Release,
    SearchVisibility,
    User,
)


class TestUserModel:
    def test_full_name(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hash",  # noqa: S106
            first_name="John",
            last_name="Doe",
        )
        assert user.full_name == "John Doe"

    def test_full_name_first_only(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hash",  # noqa: S106
            first_name="John",
            last_name="",
        )
        assert user.full_name == "John"

    def test_has_membership_false(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hash",  # noqa: S106
        )
        assert user.has_membership is False

    def test_search_visibility_explicit(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hash",  # noqa: S106
            search_visibility=SearchVisibility.PUBLIC,
        )
        assert user.search_visibility == SearchVisibility.PUBLIC

    def test_email_privacy_explicit(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hash",  # noqa: S106
            email_privacy=EmailPrivacy.PRIVATE,
        )
        assert user.email_privacy == EmailPrivacy.PRIVATE


class TestMembershipModel:
    def test_higher_level_member_basic(self) -> None:
        membership = Membership(membership_type=MembershipType.BASIC)
        assert membership.higher_level_member is False

    def test_higher_level_member_supporting(self) -> None:
        membership = Membership(membership_type=MembershipType.SUPPORTING)
        assert membership.higher_level_member is True

    def test_needs_vote_affirmation_no_date(self) -> None:
        membership = Membership(membership_type=MembershipType.BASIC)
        assert membership.needs_vote_affirmation is True

    def test_needs_vote_affirmation_old_date(self) -> None:
        membership = Membership(
            membership_type=MembershipType.BASIC,
            last_vote_affirmation=date(2020, 1, 1),
        )
        assert membership.needs_vote_affirmation is True


class TestReleaseModel:
    def test_is_version_at_least(self) -> None:
        release = Release(
            name="3.12.0",
            slug="3-12-0",
            version=PythonVersion.PYTHON3,
        )
        assert release.is_version_at_least((3, 5)) is True
        assert release.is_version_at_least((3, 12)) is True
        assert release.is_version_at_least((3, 13)) is False

    def test_is_version_at_least_3_5(self) -> None:
        release = Release(name="3.12.0", slug="3-12-0", version=PythonVersion.PYTHON3)
        assert release.is_version_at_least_3_5 is True

    def test_is_version_at_least_3_9(self) -> None:
        release = Release(name="3.12.0", slug="3-12-0", version=PythonVersion.PYTHON3)
        assert release.is_version_at_least_3_9 is True

    def test_is_version_at_least_3_14(self) -> None:
        release = Release(name="3.12.0", slug="3-12-0", version=PythonVersion.PYTHON3)
        assert release.is_version_at_least_3_14 is False

    def test_is_version_at_least_invalid(self) -> None:
        release = Release(name="invalid", slug="invalid", version=PythonVersion.PYTHON3)
        assert release.is_version_at_least((3, 5)) is False
