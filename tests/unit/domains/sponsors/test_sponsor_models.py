"""Unit tests for Sponsor models."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

from pydotorg.domains.sponsors.models import Sponsor, Sponsorship, SponsorshipLevel, SponsorshipStatus


class TestSponsorshipStatusEnum:
    def test_enum_values(self) -> None:
        assert SponsorshipStatus.APPLIED.value == "applied"
        assert SponsorshipStatus.REJECTED.value == "rejected"
        assert SponsorshipStatus.APPROVED.value == "approved"
        assert SponsorshipStatus.FINALIZED.value == "finalized"

    def test_enum_members(self) -> None:
        members = list(SponsorshipStatus)
        assert len(members) == 4
        assert SponsorshipStatus.APPLIED in members
        assert SponsorshipStatus.REJECTED in members
        assert SponsorshipStatus.APPROVED in members
        assert SponsorshipStatus.FINALIZED in members


class TestSponsorshipLevelModel:
    def test_create_sponsorship_level(self) -> None:
        level = SponsorshipLevel(name="Gold", slug="gold")
        assert level.name == "Gold"
        assert level.slug == "gold"

    def test_sponsorship_level_with_explicit_defaults(self) -> None:
        level = SponsorshipLevel(name="Silver", slug="silver", order=0, sponsorship_amount=0)
        assert level.order == 0
        assert level.sponsorship_amount == 0
        assert level.logo_dimension is None

    def test_sponsorship_level_with_all_fields(self) -> None:
        level = SponsorshipLevel(
            name="Platinum",
            slug="platinum",
            order=1,
            sponsorship_amount=100000,
            logo_dimension=500,
        )
        assert level.name == "Platinum"
        assert level.order == 1
        assert level.sponsorship_amount == 100000
        assert level.logo_dimension == 500


class TestSponsorModel:
    def test_create_sponsor(self) -> None:
        sponsor = Sponsor(name="ACME Corp", slug="acme-corp")
        assert sponsor.name == "ACME Corp"
        assert sponsor.slug == "acme-corp"

    def test_sponsor_with_explicit_defaults(self) -> None:
        sponsor = Sponsor(
            name="Test Co",
            slug="test-co",
            description="",
            landing_page_url="",
            twitter_handle="",
            linked_in_page_url="",
            web_logo="",
            print_logo="",
            primary_phone="",
            mailing_address_line_1="",
            mailing_address_line_2="",
            city="",
            state="",
            postal_code="",
            country="",
            country_of_incorporation="",
            state_of_incorporation="",
        )
        assert sponsor.description == ""
        assert sponsor.landing_page_url == ""
        assert sponsor.twitter_handle == ""
        assert sponsor.linked_in_page_url == ""
        assert sponsor.web_logo == ""
        assert sponsor.print_logo == ""
        assert sponsor.primary_phone == ""
        assert sponsor.mailing_address_line_1 == ""
        assert sponsor.mailing_address_line_2 == ""
        assert sponsor.city == ""
        assert sponsor.state == ""
        assert sponsor.postal_code == ""
        assert sponsor.country == ""
        assert sponsor.country_of_incorporation == ""
        assert sponsor.state_of_incorporation == ""

    def test_sponsor_with_basic_info(self) -> None:
        sponsor = Sponsor(
            name="Tech Startup",
            slug="tech-startup",
            description="A leading tech company",
            landing_page_url="https://techstartup.com",
            twitter_handle="@techstartup",
            linked_in_page_url="https://linkedin.com/company/techstartup",
        )
        assert sponsor.description == "A leading tech company"
        assert sponsor.landing_page_url == "https://techstartup.com"
        assert sponsor.twitter_handle == "@techstartup"
        assert sponsor.linked_in_page_url == "https://linkedin.com/company/techstartup"

    def test_sponsor_full_address_all_fields(self) -> None:
        sponsor = Sponsor(
            name="Test Co",
            slug="test-co",
            mailing_address_line_1="123 Main St",
            mailing_address_line_2="Suite 100",
            city="San Francisco",
            state="CA",
            postal_code="94102",
            country="USA",
        )
        assert sponsor.full_address == "123 Main St, Suite 100, San Francisco, CA, 94102, USA"

    def test_sponsor_full_address_partial_fields(self) -> None:
        sponsor = Sponsor(
            name="Test Co",
            slug="test-co",
            mailing_address_line_1="123 Main St",
            city="San Francisco",
            country="USA",
        )
        assert sponsor.full_address == "123 Main St, San Francisco, USA"

    def test_sponsor_full_address_empty(self) -> None:
        sponsor = Sponsor(name="Test Co", slug="test-co")
        assert sponsor.full_address == ""

    def test_sponsor_full_address_single_field(self) -> None:
        sponsor = Sponsor(
            name="Test Co",
            slug="test-co",
            city="New York",
        )
        assert sponsor.full_address == "New York"

    def test_sponsor_with_logos(self) -> None:
        sponsor = Sponsor(
            name="Tech Co",
            slug="tech-co",
            web_logo="/media/logos/tech-co-web.png",
            print_logo="/media/logos/tech-co-print.png",
        )
        assert sponsor.web_logo == "/media/logos/tech-co-web.png"
        assert sponsor.print_logo == "/media/logos/tech-co-print.png"


class TestSponsorshipModel:
    def test_create_sponsorship(self) -> None:
        sponsor_id = uuid4()
        level_id = uuid4()
        sponsorship = Sponsorship(
            sponsor_id=sponsor_id,
            level_id=level_id,
        )
        assert sponsorship.sponsor_id == sponsor_id
        assert sponsorship.level_id == level_id

    def test_sponsorship_with_explicit_defaults(self) -> None:
        sponsorship = Sponsorship(
            sponsor_id=uuid4(),
            level_id=uuid4(),
            status=SponsorshipStatus.APPLIED,
            locked=False,
            sponsorship_fee=0,
            for_modified_package=False,
            renewal=False,
        )
        assert sponsorship.submitted_by_id is None
        assert sponsorship.status == SponsorshipStatus.APPLIED
        assert sponsorship.locked is False
        assert sponsorship.start_date is None
        assert sponsorship.end_date is None
        assert sponsorship.applied_on is None
        assert sponsorship.approved_on is None
        assert sponsorship.rejected_on is None
        assert sponsorship.finalized_on is None
        assert sponsorship.year is None
        assert sponsorship.sponsorship_fee == 0
        assert sponsorship.for_modified_package is False
        assert sponsorship.renewal is False

    def test_is_active_without_dates(self) -> None:
        sponsorship = Sponsorship(
            sponsor_id=uuid4(),
            level_id=uuid4(),
            status=SponsorshipStatus.FINALIZED,
        )
        assert sponsorship.is_active is False

    def test_is_active_with_valid_dates(self) -> None:
        start_date = date.today() - timedelta(days=30)
        end_date = date.today() + timedelta(days=30)
        sponsorship = Sponsorship(
            sponsor_id=uuid4(),
            level_id=uuid4(),
            status=SponsorshipStatus.FINALIZED,
            start_date=start_date,
            end_date=end_date,
        )
        assert sponsorship.is_active is True

    def test_is_active_future_dates(self) -> None:
        start_date = date.today() + timedelta(days=10)
        end_date = date.today() + timedelta(days=40)
        sponsorship = Sponsorship(
            sponsor_id=uuid4(),
            level_id=uuid4(),
            status=SponsorshipStatus.FINALIZED,
            start_date=start_date,
            end_date=end_date,
        )
        assert sponsorship.is_active is False

    def test_is_active_past_dates(self) -> None:
        start_date = date.today() - timedelta(days=60)
        end_date = date.today() - timedelta(days=30)
        sponsorship = Sponsorship(
            sponsor_id=uuid4(),
            level_id=uuid4(),
            status=SponsorshipStatus.FINALIZED,
            start_date=start_date,
            end_date=end_date,
        )
        assert sponsorship.is_active is False

    def test_is_active_not_finalized(self) -> None:
        start_date = date.today() - timedelta(days=30)
        end_date = date.today() + timedelta(days=30)
        sponsorship = Sponsorship(
            sponsor_id=uuid4(),
            level_id=uuid4(),
            status=SponsorshipStatus.APPROVED,
            start_date=start_date,
            end_date=end_date,
        )
        assert sponsorship.is_active is False

    def test_is_active_on_start_date(self) -> None:
        start_date = date.today()
        end_date = date.today() + timedelta(days=30)
        sponsorship = Sponsorship(
            sponsor_id=uuid4(),
            level_id=uuid4(),
            status=SponsorshipStatus.FINALIZED,
            start_date=start_date,
            end_date=end_date,
        )
        assert sponsorship.is_active is True

    def test_is_active_on_end_date(self) -> None:
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        sponsorship = Sponsorship(
            sponsor_id=uuid4(),
            level_id=uuid4(),
            status=SponsorshipStatus.FINALIZED,
            start_date=start_date,
            end_date=end_date,
        )
        assert sponsorship.is_active is True

    def test_sponsorship_status_flow(self) -> None:
        sponsorship = Sponsorship(
            sponsor_id=uuid4(),
            level_id=uuid4(),
            status=SponsorshipStatus.APPLIED,
        )
        assert sponsorship.status == SponsorshipStatus.APPLIED

        sponsorship.status = SponsorshipStatus.APPROVED
        assert sponsorship.status == SponsorshipStatus.APPROVED

        sponsorship.status = SponsorshipStatus.FINALIZED
        assert sponsorship.status == SponsorshipStatus.FINALIZED

    def test_sponsorship_with_submitted_by(self) -> None:
        user_id = uuid4()
        sponsorship = Sponsorship(
            sponsor_id=uuid4(),
            level_id=uuid4(),
            submitted_by_id=user_id,
        )
        assert sponsorship.submitted_by_id == user_id

    def test_sponsorship_renewal(self) -> None:
        sponsorship = Sponsorship(
            sponsor_id=uuid4(),
            level_id=uuid4(),
            renewal=True,
        )
        assert sponsorship.renewal is True

    def test_sponsorship_modified_package(self) -> None:
        sponsorship = Sponsorship(
            sponsor_id=uuid4(),
            level_id=uuid4(),
            for_modified_package=True,
        )
        assert sponsorship.for_modified_package is True
