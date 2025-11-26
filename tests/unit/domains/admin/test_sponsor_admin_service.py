"""Unit tests for SponsorAdminService."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest

from pydotorg.domains.admin.services.sponsors import SponsorAdminService
from pydotorg.domains.sponsors.models import Sponsor, Sponsorship, SponsorshipLevel, SponsorshipStatus


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock async session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_sponsor() -> Mock:
    """Create a mock sponsor."""
    sponsor = Mock(spec=Sponsor)
    sponsor.id = uuid4()
    sponsor.name = "Test Sponsor"
    sponsor.slug = "test-sponsor"
    sponsor.description = "A test sponsor organization"
    sponsor.is_published = True
    sponsor.landing_page_url = "https://example.com"
    sponsor.primary_phone = "+1-555-1234"
    sponsor.created_at = datetime.now(tz=UTC)
    sponsor.updated_at = datetime.now(tz=UTC)
    sponsor.sponsorships = []
    return sponsor


@pytest.fixture
def mock_sponsorship_level() -> Mock:
    """Create a mock sponsorship level."""
    level = Mock(spec=SponsorshipLevel)
    level.id = uuid4()
    level.name = "Gold"
    level.slug = "gold"
    level.order = 1
    level.sponsorship_amount = 50000
    return level


@pytest.fixture
def mock_sponsorship(mock_sponsor: Mock, mock_sponsorship_level: Mock) -> Mock:
    """Create a mock sponsorship."""
    sponsorship = Mock(spec=Sponsorship)
    sponsorship.id = uuid4()
    sponsorship.sponsor_id = mock_sponsor.id
    sponsorship.level_id = mock_sponsorship_level.id
    sponsorship.status = SponsorshipStatus.APPLIED
    sponsorship.sponsor = mock_sponsor
    sponsorship.level = mock_sponsorship_level
    sponsorship.submitted_by = None
    sponsorship.start_date = None
    sponsorship.end_date = None
    sponsorship.approved_on = None
    sponsorship.rejected_on = None
    sponsorship.finalized_on = None
    sponsorship.created_at = datetime.now(tz=UTC)
    return sponsorship


@pytest.fixture
def service(mock_session: AsyncMock) -> SponsorAdminService:
    """Create a SponsorAdminService instance with mock session."""
    return SponsorAdminService(session=mock_session)


class TestListSponsorships:
    """Tests for SponsorAdminService.list_sponsorships."""

    async def test_list_sponsorships_returns_sponsorships_and_count(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
        mock_sponsorship: Mock,
    ) -> None:
        """Test that list_sponsorships returns sponsorships and total count."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_sponsorships_result = MagicMock()
        mock_sponsorships_result.scalars.return_value.all.return_value = [mock_sponsorship]

        mock_session.execute.side_effect = [mock_count_result, mock_sponsorships_result]

        sponsorships, total = await service.list_sponsorships()

        assert total == 1
        assert len(sponsorships) == 1
        assert sponsorships[0] == mock_sponsorship

    async def test_list_sponsorships_with_status_filter(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
        mock_sponsorship: Mock,
    ) -> None:
        """Test list_sponsorships with status filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_sponsorships_result = MagicMock()
        mock_sponsorships_result.scalars.return_value.all.return_value = [mock_sponsorship]

        mock_session.execute.side_effect = [mock_count_result, mock_sponsorships_result]

        _sponsorships, total = await service.list_sponsorships(status="applied")

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_sponsorships_with_search(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
        mock_sponsorship: Mock,
    ) -> None:
        """Test list_sponsorships with search filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_sponsorships_result = MagicMock()
        mock_sponsorships_result.scalars.return_value.all.return_value = [mock_sponsorship]

        mock_session.execute.side_effect = [mock_count_result, mock_sponsorships_result]

        _sponsorships, total = await service.list_sponsorships(search="Test")

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_sponsorships_with_pagination(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
        mock_sponsorship: Mock,
    ) -> None:
        """Test list_sponsorships with pagination."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 100

        mock_sponsorships_result = MagicMock()
        mock_sponsorships_result.scalars.return_value.all.return_value = [mock_sponsorship]

        mock_session.execute.side_effect = [mock_count_result, mock_sponsorships_result]

        sponsorships, total = await service.list_sponsorships(limit=10, offset=20)

        assert total == 100
        assert len(sponsorships) == 1

    async def test_list_sponsorships_empty_result(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test list_sponsorships with no results."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_sponsorships_result = MagicMock()
        mock_sponsorships_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_sponsorships_result]

        sponsorships, total = await service.list_sponsorships()

        assert total == 0
        assert len(sponsorships) == 0


class TestListSponsors:
    """Tests for SponsorAdminService.list_sponsors."""

    async def test_list_sponsors_returns_sponsors_and_count(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
        mock_sponsor: Mock,
    ) -> None:
        """Test that list_sponsors returns sponsors and total count."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_sponsors_result = MagicMock()
        mock_sponsors_result.scalars.return_value.all.return_value = [mock_sponsor]

        mock_session.execute.side_effect = [mock_count_result, mock_sponsors_result]

        sponsors, total = await service.list_sponsors()

        assert total == 1
        assert len(sponsors) == 1
        assert sponsors[0] == mock_sponsor

    async def test_list_sponsors_with_search(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
        mock_sponsor: Mock,
    ) -> None:
        """Test list_sponsors with search filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_sponsors_result = MagicMock()
        mock_sponsors_result.scalars.return_value.all.return_value = [mock_sponsor]

        mock_session.execute.side_effect = [mock_count_result, mock_sponsors_result]

        _sponsors, total = await service.list_sponsors(search="Test")

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_sponsors_empty_result(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test list_sponsors with no results."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_sponsors_result = MagicMock()
        mock_sponsors_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_sponsors_result]

        sponsors, total = await service.list_sponsors()

        assert total == 0
        assert len(sponsors) == 0


class TestGetSponsorship:
    """Tests for SponsorAdminService.get_sponsorship."""

    async def test_get_sponsorship_found(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
        mock_sponsorship: Mock,
    ) -> None:
        """Test get_sponsorship returns sponsorship when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sponsorship
        mock_session.execute.return_value = mock_result

        sponsorship = await service.get_sponsorship(mock_sponsorship.id)

        assert sponsorship == mock_sponsorship

    async def test_get_sponsorship_not_found(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_sponsorship returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        sponsorship = await service.get_sponsorship(uuid4())

        assert sponsorship is None


class TestGetSponsor:
    """Tests for SponsorAdminService.get_sponsor."""

    async def test_get_sponsor_found(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
        mock_sponsor: Mock,
    ) -> None:
        """Test get_sponsor returns sponsor when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sponsor
        mock_session.execute.return_value = mock_result

        sponsor = await service.get_sponsor(mock_sponsor.id)

        assert sponsor == mock_sponsor

    async def test_get_sponsor_not_found(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_sponsor returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        sponsor = await service.get_sponsor(uuid4())

        assert sponsor is None


class TestApproveSponsorship:
    """Tests for SponsorAdminService.approve_sponsorship."""

    async def test_approve_sponsorship_success(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
        mock_sponsorship: Mock,
    ) -> None:
        """Test approving an existing sponsorship."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sponsorship
        mock_session.execute.return_value = mock_result

        sponsorship = await service.approve_sponsorship(mock_sponsorship.id)

        assert sponsorship.status == SponsorshipStatus.APPROVED
        assert sponsorship.approved_on is not None
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_sponsorship)

    async def test_approve_sponsorship_not_found(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test approving non-existent sponsorship returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        sponsorship = await service.approve_sponsorship(uuid4())

        assert sponsorship is None
        mock_session.commit.assert_not_called()


class TestRejectSponsorship:
    """Tests for SponsorAdminService.reject_sponsorship."""

    async def test_reject_sponsorship_success(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
        mock_sponsorship: Mock,
    ) -> None:
        """Test rejecting an existing sponsorship."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sponsorship
        mock_session.execute.return_value = mock_result

        sponsorship = await service.reject_sponsorship(mock_sponsorship.id)

        assert sponsorship.status == SponsorshipStatus.REJECTED
        assert sponsorship.rejected_on is not None
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_sponsorship)

    async def test_reject_sponsorship_not_found(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test rejecting non-existent sponsorship returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        sponsorship = await service.reject_sponsorship(uuid4())

        assert sponsorship is None
        mock_session.commit.assert_not_called()


class TestFinalizeSponsorship:
    """Tests for SponsorAdminService.finalize_sponsorship."""

    async def test_finalize_sponsorship_success(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
        mock_sponsorship: Mock,
    ) -> None:
        """Test finalizing an existing sponsorship."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sponsorship
        mock_session.execute.return_value = mock_result

        sponsorship = await service.finalize_sponsorship(mock_sponsorship.id)

        assert sponsorship.status == SponsorshipStatus.FINALIZED
        assert sponsorship.finalized_on is not None
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_sponsorship)

    async def test_finalize_sponsorship_with_dates(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
        mock_sponsorship: Mock,
    ) -> None:
        """Test finalizing sponsorship with custom dates."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sponsorship
        mock_session.execute.return_value = mock_result

        start = datetime(2024, 1, 1, tzinfo=UTC)
        end = datetime(2024, 12, 31, tzinfo=UTC)

        sponsorship = await service.finalize_sponsorship(
            mock_sponsorship.id,
            start_date=start,
            end_date=end,
        )

        assert sponsorship.status == SponsorshipStatus.FINALIZED
        assert sponsorship.start_date == start.date()
        assert sponsorship.end_date == end.date()
        mock_session.commit.assert_called_once()

    async def test_finalize_sponsorship_not_found(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test finalizing non-existent sponsorship returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        sponsorship = await service.finalize_sponsorship(uuid4())

        assert sponsorship is None
        mock_session.commit.assert_not_called()


class TestGetStats:
    """Tests for SponsorAdminService.get_stats."""

    async def test_get_stats_returns_all_counts(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_stats returns all sponsor statistics."""
        mock_total_sponsors = MagicMock()
        mock_total_sponsors.scalar.return_value = 50

        mock_total_sponsorships = MagicMock()
        mock_total_sponsorships.scalar.return_value = 100

        mock_pending = MagicMock()
        mock_pending.scalar.return_value = 10

        mock_approved = MagicMock()
        mock_approved.scalar.return_value = 25

        mock_finalized = MagicMock()
        mock_finalized.scalar.return_value = 60

        mock_rejected = MagicMock()
        mock_rejected.scalar.return_value = 5

        mock_session.execute.side_effect = [
            mock_total_sponsors,
            mock_total_sponsorships,
            mock_pending,
            mock_approved,
            mock_finalized,
            mock_rejected,
        ]

        stats = await service.get_stats()

        assert stats["total_sponsors"] == 50
        assert stats["total_sponsorships"] == 100
        assert stats["pending_sponsorships"] == 10
        assert stats["approved_sponsorships"] == 25
        assert stats["finalized_sponsorships"] == 60
        assert stats["rejected_sponsorships"] == 5
        assert mock_session.execute.call_count == 6

    async def test_get_stats_empty_database(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_stats with no sponsors or sponsorships."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0

        mock_session.execute.return_value = mock_result

        stats = await service.get_stats()

        assert stats["total_sponsors"] == 0
        assert stats["total_sponsorships"] == 0
        assert stats["pending_sponsorships"] == 0
        assert stats["approved_sponsorships"] == 0
        assert stats["finalized_sponsorships"] == 0
        assert stats["rejected_sponsorships"] == 0


class TestListLevels:
    """Tests for SponsorAdminService.list_levels."""

    async def test_list_levels_returns_levels(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
        mock_sponsorship_level: Mock,
    ) -> None:
        """Test list_levels returns sponsorship levels."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sponsorship_level]
        mock_session.execute.return_value = mock_result

        levels = await service.list_levels()

        assert len(levels) == 1
        assert levels[0] == mock_sponsorship_level

    async def test_list_levels_empty(
        self,
        service: SponsorAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test list_levels with no levels."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        levels = await service.list_levels()

        assert len(levels) == 0
