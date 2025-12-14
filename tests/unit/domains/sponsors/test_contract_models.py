"""Unit tests for Contract and LegalClause models."""

from __future__ import annotations

import datetime
from uuid import uuid4

from pydotorg.domains.sponsors.models import (
    Contract,
    ContractStatus,
    LegalClause,
)


class TestContractStatusEnum:
    """Tests for ContractStatus enum."""

    def test_enum_values(self) -> None:
        """Test ContractStatus enum string values."""
        assert ContractStatus.DRAFT.value == "draft"
        assert ContractStatus.OUTDATED.value == "outdated"
        assert ContractStatus.AWAITING_SIGNATURE.value == "awaiting_signature"
        assert ContractStatus.EXECUTED.value == "executed"
        assert ContractStatus.NULLIFIED.value == "nullified"

    def test_enum_members(self) -> None:
        """Test ContractStatus has all expected members."""
        assert len(ContractStatus) == 5
        assert ContractStatus.DRAFT in ContractStatus
        assert ContractStatus.OUTDATED in ContractStatus
        assert ContractStatus.AWAITING_SIGNATURE in ContractStatus
        assert ContractStatus.EXECUTED in ContractStatus
        assert ContractStatus.NULLIFIED in ContractStatus


class TestLegalClauseModel:
    """Tests for LegalClause model."""

    def test_create_legal_clause(self) -> None:
        """Test creating a basic legal clause."""
        clause = LegalClause(
            id=uuid4(),
            name="Non-Compete",
            slug="non-compete",
            clause_text="Sponsor agrees to non-compete terms.",
        )
        assert clause.name == "Non-Compete"
        assert clause.slug == "non-compete"
        assert clause.clause_text == "Sponsor agrees to non-compete terms."

    def test_legal_clause_with_defaults(self) -> None:
        """Test LegalClause with explicitly set default values."""
        clause = LegalClause(
            id=uuid4(),
            name="Test Clause",
            slug="test-clause",
            clause_text="Test text.",
            notes="",
            order=0,
            is_active=True,
        )
        assert clause.notes == ""
        assert clause.order == 0
        assert clause.is_active is True

    def test_legal_clause_with_all_fields(self) -> None:
        """Test LegalClause with all fields populated."""
        clause = LegalClause(
            id=uuid4(),
            name="Confidentiality",
            slug="confidentiality",
            clause_text="All information shall be kept confidential.",
            notes="Required for enterprise sponsors",
            order=5,
            is_active=False,
        )
        assert clause.name == "Confidentiality"
        assert clause.notes == "Required for enterprise sponsors"
        assert clause.order == 5
        assert clause.is_active is False


class TestContractModel:
    """Tests for Contract model."""

    def test_create_contract(self) -> None:
        """Test creating a basic contract."""
        contract = Contract(
            id=uuid4(),
            sponsorship_id=uuid4(),
            status=ContractStatus.DRAFT,
            revision=0,
        )
        assert contract.status == ContractStatus.DRAFT
        assert contract.revision == 0

    def test_contract_with_defaults(self) -> None:
        """Test Contract with explicitly set default values."""
        contract = Contract(
            id=uuid4(),
            sponsorship_id=uuid4(),
            status=ContractStatus.DRAFT,
            revision=0,
            document_pdf="",
            document_docx="",
            signed_document="",
            sponsor_info="",
            sponsor_contact="",
            benefits_list="",
            legal_clauses_text="",
        )
        assert contract.document_pdf == ""
        assert contract.document_docx == ""
        assert contract.signed_document == ""
        assert contract.sponsor_info == ""
        assert contract.sponsor_contact == ""
        assert contract.benefits_list == ""
        assert contract.legal_clauses_text == ""
        assert contract.sent_on is None
        assert contract.executed_on is None

    def test_contract_is_draft(self) -> None:
        """Test is_draft property."""
        contract = Contract(id=uuid4(), sponsorship_id=uuid4(), status=ContractStatus.DRAFT)
        assert contract.is_draft is True

        contract.status = ContractStatus.AWAITING_SIGNATURE
        assert contract.is_draft is False

    def test_contract_is_awaiting_signature(self) -> None:
        """Test is_awaiting_signature property."""
        contract = Contract(id=uuid4(), sponsorship_id=uuid4(), status=ContractStatus.AWAITING_SIGNATURE)
        assert contract.is_awaiting_signature is True

        contract.status = ContractStatus.DRAFT
        assert contract.is_awaiting_signature is False

    def test_contract_is_executed(self) -> None:
        """Test is_executed property."""
        contract = Contract(id=uuid4(), sponsorship_id=uuid4(), status=ContractStatus.EXECUTED)
        assert contract.is_executed is True

        contract.status = ContractStatus.DRAFT
        assert contract.is_executed is False


class TestContractWorkflowTransitions:
    """Tests for Contract workflow state transitions."""

    def test_draft_can_send(self) -> None:
        """Test DRAFT status can transition to AWAITING_SIGNATURE."""
        contract = Contract(id=uuid4(), sponsorship_id=uuid4(), status=ContractStatus.DRAFT)
        assert contract.can_send is True
        assert ContractStatus.AWAITING_SIGNATURE in contract.next_statuses

    def test_draft_can_execute_directly(self) -> None:
        """Test DRAFT status can transition directly to EXECUTED."""
        contract = Contract(id=uuid4(), sponsorship_id=uuid4(), status=ContractStatus.DRAFT)
        assert contract.can_execute is True
        assert ContractStatus.EXECUTED in contract.next_statuses

    def test_draft_cannot_nullify(self) -> None:
        """Test DRAFT status cannot be nullified."""
        contract = Contract(id=uuid4(), sponsorship_id=uuid4(), status=ContractStatus.DRAFT)
        assert contract.can_nullify is False
        assert ContractStatus.NULLIFIED not in contract.next_statuses

    def test_awaiting_signature_can_execute(self) -> None:
        """Test AWAITING_SIGNATURE can transition to EXECUTED."""
        contract = Contract(id=uuid4(), sponsorship_id=uuid4(), status=ContractStatus.AWAITING_SIGNATURE)
        assert contract.can_execute is True
        assert ContractStatus.EXECUTED in contract.next_statuses

    def test_awaiting_signature_can_nullify(self) -> None:
        """Test AWAITING_SIGNATURE can transition to NULLIFIED."""
        contract = Contract(id=uuid4(), sponsorship_id=uuid4(), status=ContractStatus.AWAITING_SIGNATURE)
        assert contract.can_nullify is True
        assert ContractStatus.NULLIFIED in contract.next_statuses

    def test_awaiting_signature_cannot_send(self) -> None:
        """Test AWAITING_SIGNATURE cannot send again."""
        contract = Contract(id=uuid4(), sponsorship_id=uuid4(), status=ContractStatus.AWAITING_SIGNATURE)
        assert contract.can_send is False

    def test_executed_no_transitions(self) -> None:
        """Test EXECUTED status is terminal."""
        contract = Contract(id=uuid4(), sponsorship_id=uuid4(), status=ContractStatus.EXECUTED)
        assert contract.can_send is False
        assert contract.can_execute is False
        assert contract.can_nullify is False
        assert contract.next_statuses == []

    def test_nullified_can_revert_to_draft(self) -> None:
        """Test NULLIFIED can transition back to DRAFT."""
        contract = Contract(id=uuid4(), sponsorship_id=uuid4(), status=ContractStatus.NULLIFIED)
        assert ContractStatus.DRAFT in contract.next_statuses

    def test_nullified_cannot_execute(self) -> None:
        """Test NULLIFIED cannot be executed."""
        contract = Contract(id=uuid4(), sponsorship_id=uuid4(), status=ContractStatus.NULLIFIED)
        assert contract.can_execute is False

    def test_outdated_no_transitions(self) -> None:
        """Test OUTDATED status has no valid transitions."""
        contract = Contract(id=uuid4(), sponsorship_id=uuid4(), status=ContractStatus.OUTDATED)
        assert contract.can_send is False
        assert contract.can_execute is False
        assert contract.can_nullify is False
        assert contract.next_statuses == []


class TestContractWithDocuments:
    """Tests for Contract with document fields."""

    def test_contract_with_documents(self) -> None:
        """Test contract with document paths."""
        contract = Contract(
            id=uuid4(),
            sponsorship_id=uuid4(),
            document_pdf="/contracts/2025/sponsor-acme-v1.pdf",
            document_docx="/contracts/2025/sponsor-acme-v1.docx",
            signed_document="/contracts/2025/sponsor-acme-v1-signed.pdf",
        )
        assert "sponsor-acme" in contract.document_pdf
        assert "sponsor-acme" in contract.document_docx
        assert "signed" in contract.signed_document

    def test_contract_with_sponsor_info(self) -> None:
        """Test contract with sponsor information."""
        contract = Contract(
            id=uuid4(),
            sponsorship_id=uuid4(),
            sponsor_info="ACME Corp - A leading technology company",
            sponsor_contact="123 Main St, City, State | Phone: 555-1234",
            benefits_list="- Logo on website\n- Conference booth\n- Newsletter mention",
            legal_clauses_text="## Terms\n\n1. Non-compete clause\n2. Confidentiality",
        )
        assert "ACME Corp" in contract.sponsor_info
        assert "555-1234" in contract.sponsor_contact
        assert "Logo on website" in contract.benefits_list
        assert "Non-compete" in contract.legal_clauses_text

    def test_contract_with_dates(self) -> None:
        """Test contract with date fields."""
        sent_date = datetime.date(2025, 1, 15)
        executed_date = datetime.date(2025, 1, 20)
        contract = Contract(
            id=uuid4(),
            sponsorship_id=uuid4(),
            status=ContractStatus.EXECUTED,
            sent_on=sent_date,
            executed_on=executed_date,
        )
        assert contract.sent_on == sent_date
        assert contract.executed_on == executed_date

    def test_contract_revision_tracking(self) -> None:
        """Test contract revision number tracking."""
        contract = Contract(
            id=uuid4(),
            sponsorship_id=uuid4(),
            revision=3,
        )
        assert contract.revision == 3
