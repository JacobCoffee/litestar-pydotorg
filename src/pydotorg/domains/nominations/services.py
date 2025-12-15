"""Nominations domain services for business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from slugify import slugify

from pydotorg.domains.nominations.models import Election, ElectionStatus, Nomination, Nominee
from pydotorg.domains.nominations.repositories import (
    ElectionRepository,
    NominationRepository,
    NomineeRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

    from pydotorg.domains.nominations.schemas import ElectionCreate


class ElectionService(SQLAlchemyAsyncRepositoryService[Election]):
    """Service for Election business logic."""

    repository_type = ElectionRepository
    match_fields = ["slug"]

    async def create_election(self, data: ElectionCreate) -> Election:
        """Create a new election.

        Args:
            data: Election creation data.

        Returns:
            The created election instance.
        """
        election_data = data.model_dump()
        if not election_data.get("slug"):
            election_data["slug"] = slugify(data.name, max_length=200)

        return await self.create(election_data)

    async def get_by_slug(self, slug: str) -> Election | None:
        """Get an election by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The election if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

    async def get_active_elections(self, limit: int = 100, offset: int = 0) -> list[Election]:
        """Get elections that are currently active.

        Args:
            limit: Maximum number of elections to return.
            offset: Number of elections to skip.

        Returns:
            List of active elections.
        """
        return await self.repository.get_active_elections(limit, offset)

    async def get_by_status(
        self,
        status: ElectionStatus,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Election]:
        """Get elections by status.

        Args:
            status: The election status to filter by.
            limit: Maximum number of elections to return.
            offset: Number of elections to skip.

        Returns:
            List of elections with the specified status.
        """
        return await self.repository.get_by_status(status, limit, offset)


class NomineeService(SQLAlchemyAsyncRepositoryService[Nominee]):
    """Service for Nominee business logic."""

    repository_type = NomineeRepository

    async def create_nominee(self, election_id: UUID, user_id: UUID) -> Nominee:
        """Create a new nominee.

        Args:
            election_id: The election ID.
            user_id: The user ID to nominate.

        Returns:
            The created nominee instance.

        Raises:
            ValueError: If nominee already exists.
        """
        existing = await self.repository.get_by_election_and_user(election_id, user_id)
        if existing:
            msg = "Nominee already exists for this election"
            raise ValueError(msg)

        return await self.create({"election_id": election_id, "user_id": user_id, "accepted": False})

    async def accept_nomination(self, nominee_id: UUID) -> Nominee:
        """Accept a nomination.

        Args:
            nominee_id: The nominee ID.

        Returns:
            The updated nominee instance.

        Raises:
            ValueError: If nominee is already accepted.
        """
        nominee = await self.get(nominee_id)
        if nominee.accepted:
            msg = "Nomination already accepted"
            raise ValueError(msg)

        return await self.update({"accepted": True}, item_id=nominee_id)

    async def decline_nomination(self, nominee_id: UUID) -> None:
        """Decline a nomination by deleting the nominee.

        Args:
            nominee_id: The nominee ID.
        """
        await self.delete(nominee_id)

    async def get_by_election(
        self,
        election_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Nominee]:
        """Get nominees for an election.

        Args:
            election_id: The election ID.
            limit: Maximum number of nominees to return.
            offset: Number of nominees to skip.

        Returns:
            List of nominees for the election.
        """
        return await self.repository.get_by_election(election_id, limit, offset)

    async def get_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Nominee]:
        """Get nominees by user.

        Args:
            user_id: The user ID.
            limit: Maximum number of nominees to return.
            offset: Number of nominees to skip.

        Returns:
            List of nominees for the user.
        """
        return await self.repository.get_by_user(user_id, limit, offset)

    async def get_accepted_nominees(
        self,
        election_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Nominee]:
        """Get accepted nominees for an election.

        Args:
            election_id: The election ID.
            limit: Maximum number of nominees to return.
            offset: Number of nominees to skip.

        Returns:
            List of accepted nominees.
        """
        return await self.repository.get_accepted_nominees(election_id, limit, offset)


class NominationService(SQLAlchemyAsyncRepositoryService[Nomination]):
    """Service for Nomination business logic."""

    repository_type = NominationRepository

    async def create_nomination(
        self,
        nominee_id: UUID,
        nominator_id: UUID,
        endorsement: str | None = None,
    ) -> Nomination:
        """Create a new nomination.

        Args:
            nominee_id: The nominee ID.
            nominator_id: The nominator user ID.
            endorsement: Optional endorsement text.

        Returns:
            The created nomination instance.
        """
        return await self.create(
            {
                "nominee_id": nominee_id,
                "nominator_id": nominator_id,
                "endorsement": endorsement,
            }
        )

    async def get_by_nominee(
        self,
        nominee_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Nomination]:
        """Get nominations for a nominee.

        Args:
            nominee_id: The nominee ID.
            limit: Maximum number of nominations to return.
            offset: Number of nominations to skip.

        Returns:
            List of nominations for the nominee.
        """
        return await self.repository.get_by_nominee(nominee_id, limit, offset)

    async def get_by_nominator(
        self,
        nominator_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Nomination]:
        """Get nominations by nominator.

        Args:
            nominator_id: The nominator user ID.
            limit: Maximum number of nominations to return.
            offset: Number of nominations to skip.

        Returns:
            List of nominations by the nominator.
        """
        return await self.repository.get_by_nominator(nominator_id, limit, offset)

    async def count_by_nominee(self, nominee_id: UUID) -> int:
        """Count nominations for a nominee.

        Args:
            nominee_id: The nominee ID.

        Returns:
            Number of nominations for the nominee.
        """
        return await self.repository.count_by_nominee(nominee_id)
