"""Nominations domain repositories for database access."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select

from pydotorg.domains.nominations.models import Election, ElectionStatus, Nomination, Nominee

if TYPE_CHECKING:
    from uuid import UUID


class ElectionRepository(SQLAlchemyAsyncRepository[Election]):
    """Repository for Election database operations."""

    model_type = Election

    async def get_by_slug(self, slug: str) -> Election | None:
        """Get an election by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The election if found, None otherwise.
        """
        statement = select(Election).where(Election.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_active_elections(self, limit: int = 100, offset: int = 0) -> list[Election]:
        """Get elections that are currently active.

        Args:
            limit: Maximum number of elections to return.
            offset: Number of elections to skip.

        Returns:
            List of active elections.
        """
        today = datetime.datetime.now(tz=datetime.UTC).date()
        statement = (
            select(Election)
            .where(
                Election.nominations_open <= today,
                Election.voting_close >= today,
            )
            .order_by(Election.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

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
        today = datetime.datetime.now(tz=datetime.UTC).date()
        statement = select(Election).order_by(Election.created_at.desc()).limit(limit).offset(offset)

        if status == ElectionStatus.UPCOMING:
            statement = statement.where(Election.nominations_open > today)
        elif status == ElectionStatus.NOMINATIONS_OPEN:
            statement = statement.where(
                Election.nominations_open <= today,
                Election.nominations_close >= today,
            )
        elif status == ElectionStatus.VOTING_OPEN:
            statement = statement.where(
                Election.voting_open <= today,
                Election.voting_close >= today,
            )
        elif status == ElectionStatus.CLOSED:
            statement = statement.where(Election.voting_close < today)

        result = await self.session.execute(statement)
        return list(result.scalars().all())


class NomineeRepository(SQLAlchemyAsyncRepository[Nominee]):
    """Repository for Nominee database operations."""

    model_type = Nominee

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
        statement = (
            select(Nominee)
            .where(Nominee.election_id == election_id)
            .order_by(Nominee.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

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
        statement = (
            select(Nominee)
            .where(Nominee.user_id == user_id)
            .order_by(Nominee.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

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
        statement = (
            select(Nominee)
            .where(Nominee.election_id == election_id, Nominee.accepted.is_(True))
            .order_by(Nominee.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_election_and_user(self, election_id: UUID, user_id: UUID) -> Nominee | None:
        """Get a nominee by election and user.

        Args:
            election_id: The election ID.
            user_id: The user ID.

        Returns:
            The nominee if found, None otherwise.
        """
        statement = select(Nominee).where(Nominee.election_id == election_id, Nominee.user_id == user_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()


class NominationRepository(SQLAlchemyAsyncRepository[Nomination]):
    """Repository for Nomination database operations."""

    model_type = Nomination

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
        statement = (
            select(Nomination)
            .where(Nomination.nominee_id == nominee_id)
            .order_by(Nomination.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

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
        statement = (
            select(Nomination)
            .where(Nomination.nominator_id == nominator_id)
            .order_by(Nomination.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def count_by_nominee(self, nominee_id: UUID) -> int:
        """Count nominations for a nominee.

        Args:
            nominee_id: The nominee ID.

        Returns:
            Number of nominations for the nominee.
        """
        statement = select(Nomination).where(Nomination.nominee_id == nominee_id)
        result = await self.session.execute(statement)
        return len(list(result.scalars().all()))
