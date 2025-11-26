"""Unit tests for UserGroup model."""

from __future__ import annotations

from datetime import date

from pydotorg.domains.users.models import UserGroup, UserGroupType


class TestUserGroupModel:
    def test_create_user_group(self) -> None:
        group = UserGroup(name="Python NYC Meetup")
        assert group.name == "Python NYC Meetup"

    def test_user_group_with_explicit_defaults(self) -> None:
        group = UserGroup(
            name="Test Group",
            location="",
            url="",
            url_type=UserGroupType.OTHER,
            approved=False,
            trusted=False,
        )
        assert group.location == ""
        assert group.url == ""
        assert group.url_type == UserGroupType.OTHER
        assert group.start_date is None
        assert group.approved is False
        assert group.trusted is False

    def test_user_group_with_all_fields(self) -> None:
        group = UserGroup(
            name="Python SF Meetup",
            location="San Francisco, CA",
            url="https://pythonsf.com",
            url_type=UserGroupType.MEETUP,
            start_date=date(2020, 1, 1),
            approved=True,
            trusted=True,
        )
        assert group.name == "Python SF Meetup"
        assert group.location == "San Francisco, CA"
        assert group.url == "https://pythonsf.com"
        assert group.url_type == UserGroupType.MEETUP
        assert group.start_date == date(2020, 1, 1)
        assert group.approved is True
        assert group.trusted is True

    def test_user_group_meetup_type(self) -> None:
        group = UserGroup(
            name="Test Meetup",
            url_type=UserGroupType.MEETUP,
        )
        assert group.url_type == UserGroupType.MEETUP

    def test_user_group_distribution_list_type(self) -> None:
        group = UserGroup(
            name="Test List",
            url_type=UserGroupType.DISTRIBUTION_LIST,
        )
        assert group.url_type == UserGroupType.DISTRIBUTION_LIST

    def test_user_group_other_type(self) -> None:
        group = UserGroup(
            name="Test Other",
            url_type=UserGroupType.OTHER,
        )
        assert group.url_type == UserGroupType.OTHER

    def test_user_group_approval_flow(self) -> None:
        group = UserGroup(name="New Group", approved=False, trusted=False)
        assert group.approved is False
        assert group.trusted is False

        group.approved = True
        assert group.approved is True

        group.trusted = True
        assert group.trusted is True
