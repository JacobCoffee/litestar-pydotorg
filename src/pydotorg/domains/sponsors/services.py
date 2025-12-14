"""Sponsors domain services for business logic."""

from __future__ import annotations

import datetime
from datetime import UTC
from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from pydotorg.domains.sponsors.models import (
    Contract,
    ContractStatus,
    LegalClause,
    Sponsor,
    Sponsorship,
    SponsorshipLevel,
    SponsorshipStatus,
)
from pydotorg.domains.sponsors.repositories import (
    ContractRepository,
    LegalClauseRepository,
    SponsorRepository,
    SponsorshipLevelRepository,
    SponsorshipRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

    from pydotorg.domains.sponsors.schemas import (
        SponsorCreate,
        SponsorshipCreate,
        SponsorshipLevelCreate,
    )


class InvalidContractStatusError(Exception):
    """Raised when a contract status transition is not valid."""


class SponsorshipLevelService(SQLAlchemyAsyncRepositoryService[SponsorshipLevel]):
    """Service for SponsorshipLevel business logic."""

    repository_type = SponsorshipLevelRepository
    match_fields = ["slug"]

    async def create_level(self, data: SponsorshipLevelCreate) -> SponsorshipLevel:
        """Create a new sponsorship level.

        Args:
            data: Sponsorship level creation data.

        Returns:
            The created sponsorship level instance.

        Raises:
            ValueError: If slug already exists.
        """
        if data.slug and await self.repository.exists_by_slug(data.slug):
            msg = f"Sponsorship level with slug {data.slug} already exists"
            raise ValueError(msg)

        level_data = data.model_dump()
        if not level_data.get("slug") and level_data.get("name"):
            level_data["slug"] = SponsorshipLevel.generate_slug(level_data["name"])

        return await self.create(level_data)

    async def get_by_slug(self, slug: str) -> SponsorshipLevel | None:
        """Get a sponsorship level by its slug.

        Args:
            slug: The slug to search for.

        Returns:
            The sponsorship level if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

    async def list_ordered(self, limit: int = 100, offset: int = 0) -> list[SponsorshipLevel]:
        """List sponsorship levels ordered by order field.

        Args:
            limit: Maximum number of levels to return.
            offset: Number of levels to skip.

        Returns:
            List of sponsorship levels ordered by order field.
        """
        return await self.repository.list_ordered(limit=limit, offset=offset)


class SponsorService(SQLAlchemyAsyncRepositoryService[Sponsor]):
    """Service for Sponsor business logic."""

    repository_type = SponsorRepository
    match_fields = ["slug"]

    async def create_sponsor(self, data: SponsorCreate) -> Sponsor:
        """Create a new sponsor.

        Args:
            data: Sponsor creation data.

        Returns:
            The created sponsor instance.

        Raises:
            ValueError: If slug already exists.
        """
        if data.slug and await self.repository.exists_by_slug(data.slug):
            msg = f"Sponsor with slug {data.slug} already exists"
            raise ValueError(msg)

        sponsor_data = data.model_dump()
        if not sponsor_data.get("slug") and sponsor_data.get("name"):
            sponsor_data["slug"] = Sponsor.generate_slug(sponsor_data["name"])

        return await self.create(sponsor_data)

    async def get_by_slug(self, slug: str) -> Sponsor | None:
        """Get a sponsor by its slug.

        Args:
            slug: The slug to search for.

        Returns:
            The sponsor if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

    async def list_with_active_sponsorships(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Sponsor]:
        """List sponsors with active sponsorships.

        Args:
            limit: Maximum number of sponsors to return.
            offset: Number of sponsors to skip.

        Returns:
            List of sponsors with active sponsorships.
        """
        return await self.repository.list_with_active_sponsorships(limit=limit, offset=offset)


class SponsorshipService(SQLAlchemyAsyncRepositoryService[Sponsorship]):
    """Service for Sponsorship business logic."""

    repository_type = SponsorshipRepository
    match_fields = ["sponsor_id", "level_id"]

    async def create_sponsorship(self, data: SponsorshipCreate) -> Sponsorship:
        """Create a new sponsorship.

        Args:
            data: Sponsorship creation data.

        Returns:
            The created sponsorship instance.
        """
        sponsorship_data = data.model_dump()
        if not sponsorship_data.get("applied_on"):
            sponsorship_data["applied_on"] = datetime.datetime.now(tz=UTC).date()

        return await self.create(sponsorship_data)

    async def list_by_sponsor_id(
        self,
        sponsor_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Sponsorship]:
        """List sponsorships for a specific sponsor.

        Args:
            sponsor_id: The sponsor ID to filter by.
            limit: Maximum number of sponsorships to return.
            offset: Number of sponsorships to skip.

        Returns:
            List of sponsorships for the sponsor.
        """
        return await self.repository.list_by_sponsor_id(sponsor_id, limit=limit, offset=offset)

    async def list_by_level_id(
        self,
        level_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Sponsorship]:
        """List sponsorships for a specific level.

        Args:
            level_id: The level ID to filter by.
            limit: Maximum number of sponsorships to return.
            offset: Number of sponsorships to skip.

        Returns:
            List of sponsorships for the level.
        """
        return await self.repository.list_by_level_id(level_id, limit=limit, offset=offset)

    async def list_by_status(
        self,
        status: SponsorshipStatus,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Sponsorship]:
        """List sponsorships by status.

        Args:
            status: The status to filter by.
            limit: Maximum number of sponsorships to return.
            offset: Number of sponsorships to skip.

        Returns:
            List of sponsorships with the given status.
        """
        return await self.repository.list_by_status(status, limit=limit, offset=offset)

    async def list_active(self, limit: int = 100, offset: int = 0) -> list[Sponsorship]:
        """List active sponsorships.

        Args:
            limit: Maximum number of sponsorships to return.
            offset: Number of sponsorships to skip.

        Returns:
            List of active sponsorships.
        """
        return await self.repository.list_active(limit=limit, offset=offset)

    async def approve(self, sponsorship_id: UUID) -> Sponsorship:
        """Approve a sponsorship.

        Args:
            sponsorship_id: The ID of the sponsorship to approve.

        Returns:
            The updated sponsorship instance.
        """
        return await self.update(
            sponsorship_id,
            {
                "status": SponsorshipStatus.APPROVED,
                "approved_on": datetime.datetime.now(tz=UTC).date(),
            },
        )

    async def reject(self, sponsorship_id: UUID) -> Sponsorship:
        """Reject a sponsorship.

        Args:
            sponsorship_id: The ID of the sponsorship to reject.

        Returns:
            The updated sponsorship instance.
        """
        return await self.update(
            sponsorship_id,
            {
                "status": SponsorshipStatus.REJECTED,
                "rejected_on": datetime.datetime.now(tz=UTC).date(),
            },
        )

    async def finalize(self, sponsorship_id: UUID) -> Sponsorship:
        """Finalize a sponsorship.

        Args:
            sponsorship_id: The ID of the sponsorship to finalize.

        Returns:
            The updated sponsorship instance.
        """
        return await self.update(
            sponsorship_id,
            {
                "status": SponsorshipStatus.FINALIZED,
                "finalized_on": datetime.datetime.now(tz=UTC).date(),
            },
        )

    async def approve_with_renewal(
        self,
        sponsorship_id: UUID,
        start_date: datetime.date,
        end_date: datetime.date,
        sponsorship_fee: int | None = None,
        *,
        is_renewal: bool = False,
    ) -> Sponsorship:
        """Approve a sponsorship with full approval data.

        Args:
            sponsorship_id: The ID of the sponsorship to approve.
            start_date: The sponsorship start date.
            end_date: The sponsorship end date.
            sponsorship_fee: Optional sponsorship fee override.
            is_renewal: Whether this is a renewal of a previous sponsorship.

        Returns:
            The updated sponsorship instance.
        """
        update_data: dict[str, datetime.date | int | bool | SponsorshipStatus] = {
            "status": SponsorshipStatus.APPROVED,
            "approved_on": datetime.datetime.now(tz=UTC).date(),
            "start_date": start_date,
            "end_date": end_date,
            "year": start_date.year,
            "renewal": is_renewal,
        }
        if sponsorship_fee is not None:
            update_data["sponsorship_fee"] = sponsorship_fee

        return await self.update(sponsorship_id, update_data)

    async def get_previous_sponsorship(self, sponsorship: Sponsorship) -> Sponsorship | None:
        """Get the previous sponsorship for the same sponsor.

        Used to determine previous effective date for renewal contracts.

        Args:
            sponsorship: The current sponsorship.

        Returns:
            The previous sponsorship if found, None otherwise.
        """
        return await self.repository.get_previous_for_sponsor(
            sponsor_id=sponsorship.sponsor_id,
            current_year=sponsorship.year,
        )

    async def list_expiring_soon(
        self,
        days: int = 90,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Sponsorship]:
        """List sponsorships expiring within the given number of days.

        Useful for sending renewal reminders.

        Args:
            days: Number of days until expiration.
            limit: Maximum number of sponsorships to return.
            offset: Number of sponsorships to skip.

        Returns:
            List of sponsorships expiring within the given timeframe.
        """
        return await self.repository.list_expiring_soon(days=days, limit=limit, offset=offset)

    async def create_renewal(
        self,
        previous_sponsorship: Sponsorship,
        level_id: UUID | None = None,
    ) -> Sponsorship:
        """Create a renewal sponsorship based on a previous one.

        Args:
            previous_sponsorship: The sponsorship being renewed.
            level_id: Optional new level ID (defaults to same level).

        Returns:
            The new renewal sponsorship instance.
        """
        return await self.create(
            {
                "sponsor_id": previous_sponsorship.sponsor_id,
                "level_id": level_id or previous_sponsorship.level_id,
                "status": SponsorshipStatus.APPLIED,
                "applied_on": datetime.datetime.now(tz=UTC).date(),
                "renewal": True,
            }
        )


class LegalClauseService(SQLAlchemyAsyncRepositoryService[LegalClause]):
    """Service for LegalClause business logic."""

    repository_type = LegalClauseRepository
    match_fields = ["slug"]

    async def get_by_slug(self, slug: str) -> LegalClause | None:
        """Get a legal clause by its slug.

        Args:
            slug: The slug to search for.

        Returns:
            The legal clause if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

    async def list_active(self, limit: int = 100, offset: int = 0) -> list[LegalClause]:
        """List active legal clauses ordered by order field.

        Args:
            limit: Maximum number of clauses to return.
            offset: Number of clauses to skip.

        Returns:
            List of active legal clauses.
        """
        return await self.repository.list_active(limit=limit, offset=offset)


class ContractService(SQLAlchemyAsyncRepositoryService[Contract]):
    """Service for Contract business logic and workflow management."""

    repository_type = ContractRepository

    async def create_contract(self, sponsorship_id: UUID) -> Contract:
        """Create a new contract for a sponsorship.

        Initializes a draft contract with sponsor information from the sponsorship.

        Args:
            sponsorship_id: The sponsorship ID to create contract for.

        Returns:
            The created contract instance.
        """
        sponsorship = await self.repository.session.get(Sponsorship, sponsorship_id)
        if not sponsorship:
            msg = f"Sponsorship {sponsorship_id} not found"
            raise ValueError(msg)

        sponsor = sponsorship.sponsor
        sponsor_info = f"{sponsor.name}"
        if sponsor.description:
            sponsor_info += f" - {sponsor.description}"

        sponsor_contact = sponsor.full_address
        if sponsor.primary_phone:
            sponsor_contact += f" | Phone: {sponsor.primary_phone}"

        return await self.create(
            {
                "sponsorship_id": sponsorship_id,
                "sponsor_info": sponsor_info,
                "sponsor_contact": sponsor_contact,
                "status": ContractStatus.DRAFT,
            }
        )

    async def get_by_sponsorship_id(self, sponsorship_id: UUID) -> Contract | None:
        """Get a contract by sponsorship ID.

        Args:
            sponsorship_id: The sponsorship ID to search for.

        Returns:
            The contract if found, None otherwise.
        """
        return await self.repository.get_by_sponsorship_id(sponsorship_id)

    async def list_by_status(
        self,
        status: ContractStatus,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Contract]:
        """List contracts by status.

        Args:
            status: The status to filter by.
            limit: Maximum number of contracts to return.
            offset: Number of contracts to skip.

        Returns:
            List of contracts with the given status.
        """
        return await self.repository.list_by_status(status, limit=limit, offset=offset)

    async def send_for_signature(
        self,
        contract_id: UUID,
        document_pdf: str = "",
        document_docx: str = "",
    ) -> Contract:
        """Send contract for signature.

        Transitions contract from DRAFT to AWAITING_SIGNATURE.

        Args:
            contract_id: The contract ID.
            document_pdf: Path to the unsigned PDF document.
            document_docx: Path to the unsigned DOCX document.

        Returns:
            The updated contract instance.

        Raises:
            InvalidContractStatusError: If transition is not valid.
        """
        contract = await self.get(contract_id)
        if not contract.can_send:
            msg = f"Cannot send contract in {contract.status} status for signature"
            raise InvalidContractStatusError(msg)

        contract.revision += 1
        return await self.update(
            contract_id,
            {
                "status": ContractStatus.AWAITING_SIGNATURE,
                "document_pdf": document_pdf,
                "document_docx": document_docx,
                "sent_on": datetime.datetime.now(tz=UTC).date(),
                "revision": contract.revision,
            },
        )

    async def execute_contract(
        self,
        contract_id: UUID,
        signed_document: str = "",
    ) -> Contract:
        """Execute a contract.

        Marks the contract as executed and finalizes the associated sponsorship.

        Args:
            contract_id: The contract ID.
            signed_document: Path to the signed document.

        Returns:
            The updated contract instance.

        Raises:
            InvalidContractStatusError: If transition is not valid.
        """
        contract = await self.get(contract_id)
        if not contract.can_execute:
            msg = f"Cannot execute contract in {contract.status} status"
            raise InvalidContractStatusError(msg)

        contract = await self.update(
            contract_id,
            {
                "status": ContractStatus.EXECUTED,
                "signed_document": signed_document,
                "executed_on": datetime.datetime.now(tz=UTC).date(),
            },
        )

        sponsorship = contract.sponsorship
        sponsorship.status = SponsorshipStatus.FINALIZED
        sponsorship.finalized_on = datetime.datetime.now(tz=UTC).date()
        sponsorship.locked = True
        await self.repository.session.commit()

        return contract

    async def nullify_contract(self, contract_id: UUID) -> Contract:
        """Nullify a contract.

        Args:
            contract_id: The contract ID.

        Returns:
            The updated contract instance.

        Raises:
            InvalidContractStatusError: If transition is not valid.
        """
        contract = await self.get(contract_id)
        if not contract.can_nullify:
            msg = f"Cannot nullify contract in {contract.status} status"
            raise InvalidContractStatusError(msg)

        return await self.update(
            contract_id,
            {"status": ContractStatus.NULLIFIED},
        )

    async def revert_to_draft(self, contract_id: UUID) -> Contract:
        """Revert a nullified contract back to draft.

        Args:
            contract_id: The contract ID.

        Returns:
            The updated contract instance.

        Raises:
            InvalidContractStatusError: If transition is not valid.
        """
        contract = await self.get(contract_id)
        if ContractStatus.DRAFT not in contract.next_statuses:
            msg = f"Cannot revert contract in {contract.status} status to draft"
            raise InvalidContractStatusError(msg)

        return await self.update(
            contract_id,
            {"status": ContractStatus.DRAFT},
        )

    async def update_benefits_and_clauses(
        self,
        contract_id: UUID,
        benefits_list: str,
        legal_clauses_text: str,
    ) -> Contract:
        """Update contract benefits list and legal clauses.

        Args:
            contract_id: The contract ID.
            benefits_list: Markdown formatted list of benefits.
            legal_clauses_text: Markdown formatted legal clauses.

        Returns:
            The updated contract instance.
        """
        contract = await self.get(contract_id)
        if not contract.is_draft:
            msg = "Can only update benefits and clauses on draft contracts"
            raise InvalidContractStatusError(msg)

        return await self.update(
            contract_id,
            {
                "benefits_list": benefits_list,
                "legal_clauses_text": legal_clauses_text,
            },
        )
