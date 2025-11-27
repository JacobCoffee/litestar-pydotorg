"""Unit tests for Membership model."""

from __future__ import annotations

import datetime
from datetime import date, timedelta
from uuid import uuid4

import time_machine

from pydotorg.domains.users.models import VOTE_AFFIRMATION_DAYS, Membership, MembershipType


class TestMembershipModel:
    def test_create_membership(self) -> None:
        user_id = uuid4()
        membership = Membership(
            user_id=user_id,
            membership_type=MembershipType.BASIC,
        )
        assert membership.user_id == user_id
        assert membership.membership_type == MembershipType.BASIC

    def test_membership_with_explicit_defaults(self) -> None:
        user_id = uuid4()
        membership = Membership(
            user_id=user_id,
            membership_type=MembershipType.BASIC,
            legal_name="",
            preferred_name="",
            email_address="",
            city="",
            region="",
            country="",
            postal_code="",
            psf_code_of_conduct=False,
            psf_announcements=False,
            votes=False,
        )
        assert membership.membership_type == MembershipType.BASIC
        assert membership.legal_name == ""
        assert membership.preferred_name == ""
        assert membership.email_address == ""
        assert membership.city == ""
        assert membership.region == ""
        assert membership.country == ""
        assert membership.postal_code == ""
        assert membership.psf_code_of_conduct is False
        assert membership.psf_announcements is False
        assert membership.votes is False
        assert membership.last_vote_affirmation is None

    def test_higher_level_member_basic(self) -> None:
        membership = Membership(
            user_id=uuid4(),
            membership_type=MembershipType.BASIC,
        )
        assert membership.higher_level_member is False

    def test_higher_level_member_supporting(self) -> None:
        membership = Membership(
            user_id=uuid4(),
            membership_type=MembershipType.SUPPORTING,
        )
        assert membership.higher_level_member is True

    def test_higher_level_member_sponsor(self) -> None:
        membership = Membership(
            user_id=uuid4(),
            membership_type=MembershipType.SPONSOR,
        )
        assert membership.higher_level_member is True

    def test_higher_level_member_managing(self) -> None:
        membership = Membership(
            user_id=uuid4(),
            membership_type=MembershipType.MANAGING,
        )
        assert membership.higher_level_member is True

    def test_higher_level_member_contributing(self) -> None:
        membership = Membership(
            user_id=uuid4(),
            membership_type=MembershipType.CONTRIBUTING,
        )
        assert membership.higher_level_member is True

    def test_higher_level_member_fellow(self) -> None:
        membership = Membership(
            user_id=uuid4(),
            membership_type=MembershipType.FELLOW,
        )
        assert membership.higher_level_member is True

    def test_needs_vote_affirmation_no_date(self) -> None:
        membership = Membership(
            user_id=uuid4(),
            membership_type=MembershipType.BASIC,
        )
        assert membership.needs_vote_affirmation is True

    def test_needs_vote_affirmation_recent_date(self) -> None:
        recent_date = date.today() - timedelta(days=30)
        membership = Membership(
            user_id=uuid4(),
            membership_type=MembershipType.BASIC,
            last_vote_affirmation=recent_date,
        )
        assert membership.needs_vote_affirmation is False

    def test_needs_vote_affirmation_old_date(self) -> None:
        old_date = date.today() - timedelta(days=VOTE_AFFIRMATION_DAYS + 1)
        membership = Membership(
            user_id=uuid4(),
            membership_type=MembershipType.BASIC,
            last_vote_affirmation=old_date,
        )
        assert membership.needs_vote_affirmation is True

    @time_machine.travel(datetime.datetime(2024, 6, 15, 12, 0, 0, tzinfo=datetime.UTC))
    def test_needs_vote_affirmation_exactly_at_threshold(self) -> None:
        today = datetime.datetime.now(tz=datetime.UTC).date()
        threshold_date = today - timedelta(days=VOTE_AFFIRMATION_DAYS)
        membership = Membership(
            user_id=uuid4(),
            membership_type=MembershipType.BASIC,
            last_vote_affirmation=threshold_date,
        )
        assert membership.needs_vote_affirmation is False

    def test_needs_vote_affirmation_one_day_past_threshold(self) -> None:
        past_threshold = date.today() - timedelta(days=VOTE_AFFIRMATION_DAYS + 1)
        membership = Membership(
            user_id=uuid4(),
            membership_type=MembershipType.BASIC,
            last_vote_affirmation=past_threshold,
        )
        assert membership.needs_vote_affirmation is True

    def test_membership_with_all_fields(self) -> None:
        user_id = uuid4()
        membership = Membership(
            user_id=user_id,
            membership_type=MembershipType.FELLOW,
            legal_name="John Doe",
            preferred_name="Johnny",
            email_address="john@example.com",
            city="New York",
            region="NY",
            country="USA",
            postal_code="10001",
            psf_code_of_conduct=True,
            psf_announcements=True,
            votes=True,
            last_vote_affirmation=date(2024, 1, 1),
        )
        assert membership.legal_name == "John Doe"
        assert membership.preferred_name == "Johnny"
        assert membership.email_address == "john@example.com"
        assert membership.city == "New York"
        assert membership.region == "NY"
        assert membership.country == "USA"
        assert membership.postal_code == "10001"
        assert membership.psf_code_of_conduct is True
        assert membership.psf_announcements is True
        assert membership.votes is True
        assert membership.last_vote_affirmation == date(2024, 1, 1)
