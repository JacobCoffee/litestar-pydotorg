"""Sponsor workflow definitions.

Workflows:
    - sponsor_contract: Contract lifecycle from draft to execution
    - sponsorship_approval: Sponsorship application review and finalization
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar_workflows import (
    BaseHumanStep,
    BaseMachineStep,
    Edge,
    WorkflowDefinition,
)

if TYPE_CHECKING:
    from litestar_workflows import WorkflowContext


# =============================================================================
# Sponsor Contract Workflow Steps
# =============================================================================


class CreateContractStep(BaseMachineStep):
    """Initialize a new contract in DRAFT status."""

    async def execute(self, context: WorkflowContext) -> None:
        """Create contract record and set initial status."""
        context.set("contract_status", "draft")
        context.set("revision", 0)


class SendForSignatureStep(BaseMachineStep):
    """Transition contract to AWAITING_SIGNATURE status."""

    async def execute(self, context: WorkflowContext) -> None:
        """Update contract status to awaiting signature."""
        context.set("contract_status", "awaiting_signature")
        context.set("sent_at", "now")  # Will be replaced with actual timestamp


class NotifySponsorStep(BaseMachineStep):
    """Send email notification to sponsor about contract ready for signature."""

    async def execute(self, context: WorkflowContext) -> None:
        """Queue email notification for sponsor."""
        context.set(
            "_email_notification_notify_sponsor",
            {
                "template": "contract_ready_for_signature",
                "recipient": context.get("sponsor_email", ""),
                "context": {
                    "sponsor_name": context.get("sponsor_name"),
                    "contract_url": context.get("contract_url"),
                    "sponsorship_level": context.get("sponsorship_level"),
                },
            },
        )


class ExecuteContractStep(BaseMachineStep):
    """Finalize contract execution."""

    async def execute(self, context: WorkflowContext) -> None:
        """Update contract status to executed."""
        context.set("contract_status", "executed")
        context.set("executed_at", "now")  # Will be replaced with actual timestamp


class NotifyContractExecutedStep(BaseMachineStep):
    """Send confirmation email that contract is executed."""

    async def execute(self, context: WorkflowContext) -> None:
        """Queue email notification for contract execution."""
        context.set(
            "_email_notification_notify_executed",
            {
                "template": "contract_executed",
                "recipient": context.get("sponsor_email", ""),
                "context": {
                    "sponsor_name": context.get("sponsor_name"),
                    "sponsorship_level": context.get("sponsorship_level"),
                    "start_date": context.get("start_date"),
                    "end_date": context.get("end_date"),
                },
            },
        )


# =============================================================================
# Sponsorship Approval Workflow Steps
# =============================================================================


class SubmitApplicationStep(BaseMachineStep):
    """Record sponsorship application submission."""

    async def execute(self, context: WorkflowContext) -> None:
        """Mark application as submitted."""
        context.set("sponsorship_status", "applied")
        context.set("submitted_at", "now")


class ApproveApplicationStep(BaseMachineStep):
    """Process approval decision."""

    async def execute(self, context: WorkflowContext) -> None:
        """Update status based on approval decision."""
        approved = context.get("approved", False)
        if approved:
            context.set("sponsorship_status", "approved")
        else:
            context.set("sponsorship_status", "rejected")


class CompleteSponsorshipStep(BaseMachineStep):
    """Mark sponsorship as finalized."""

    async def execute(self, context: WorkflowContext) -> None:
        """Set final status."""
        context.set("sponsorship_status", "finalized")


# =============================================================================
# Form Schemas for Human Steps
# =============================================================================


DOCUMENT_UPLOAD_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "document_pdf": {
            "type": "string",
            "title": "Document",
            "description": "Upload or provide document URL",
            "format": "uri",
        },
        "notes": {
            "type": "string",
            "title": "Notes",
            "description": "Optional notes about this document",
        },
    },
    "required": ["document_pdf"],
}


SIGNED_DOCUMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "signed_document": {
            "type": "string",
            "title": "Signed Document",
            "description": "Upload the signed contract document",
            "format": "uri",
        },
        "notes": {
            "type": "string",
            "title": "Notes",
        },
    },
    "required": ["signed_document"],
}


APPROVAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "approved": {
            "type": "boolean",
            "title": "Approve",
            "description": "Approve or reject this request",
        },
        "comments": {
            "type": "string",
            "title": "Comments",
            "description": "Optional comments or feedback",
        },
    },
    "required": ["approved"],
}


FINALIZATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "approved": {
            "type": "boolean",
            "title": "Finalize",
            "description": "Confirm finalization",
            "default": True,
        },
        "start_date": {
            "type": "string",
            "title": "Start Date",
            "format": "date",
        },
        "end_date": {
            "type": "string",
            "title": "End Date",
            "format": "date",
        },
        "comments": {
            "type": "string",
            "title": "Notes",
        },
    },
    "required": ["approved", "start_date", "end_date"],
}


# =============================================================================
# Workflow Classes (implement Workflow protocol)
# =============================================================================


class SponsorContractWorkflow:
    """Sponsor contract lifecycle workflow.

    Workflow: DRAFT → prepare_contract (human) → send_for_signature →
              notify_sponsor → receive_signed (human) → execute_contract → notify_executed
    """

    name = "sponsor_contract"
    version = "1.0.0"
    description = "Sponsor contract lifecycle from draft to execution"

    @classmethod
    def get_definition(cls) -> WorkflowDefinition:
        """Get the workflow definition."""
        return WorkflowDefinition(
            name=cls.name,
            version=cls.version,
            description=cls.description,
            steps={
                "create_contract": CreateContractStep(
                    name="create_contract",
                    description="Create a new contract for the sponsorship",
                ),
                "prepare_contract": BaseHumanStep(
                    name="prepare_contract",
                    title="Prepare Contract Document",
                    description="Upload the prepared contract PDF for sponsor signature",
                    form_schema=DOCUMENT_UPLOAD_SCHEMA,
                ),
                "send_for_signature": SendForSignatureStep(
                    name="send_for_signature",
                    description="Send contract to sponsor for signature",
                ),
                "notify_sponsor": NotifySponsorStep(
                    name="notify_sponsor",
                    description="Email sponsor about contract ready for signature",
                ),
                "receive_signed": BaseHumanStep(
                    name="receive_signed",
                    title="Upload Signed Contract",
                    description="Upload the signed contract document from the sponsor",
                    form_schema=SIGNED_DOCUMENT_SCHEMA,
                ),
                "execute_contract": ExecuteContractStep(
                    name="execute_contract",
                    description="Mark contract as fully executed",
                ),
                "notify_executed": NotifyContractExecutedStep(
                    name="notify_executed",
                    description="Email confirmation of contract execution",
                ),
            },
            edges=[
                Edge("create_contract", "prepare_contract"),
                Edge("prepare_contract", "send_for_signature"),
                Edge("send_for_signature", "notify_sponsor"),
                Edge("notify_sponsor", "receive_signed"),
                Edge("receive_signed", "execute_contract"),
                Edge("execute_contract", "notify_executed"),
            ],
            initial_step="create_contract",
            terminal_steps={"notify_executed"},
        )


class SponsorshipApprovalWorkflow:
    """Sponsorship application approval workflow.

    Workflow: submit_application → review_application (human) → process_approval →
              finalize_sponsorship (human) → complete_sponsorship
    """

    name = "sponsorship_approval"
    version = "1.0.0"
    description = "Sponsorship application review and approval workflow"

    @classmethod
    def get_definition(cls) -> WorkflowDefinition:
        """Get the workflow definition."""
        return WorkflowDefinition(
            name=cls.name,
            version=cls.version,
            description=cls.description,
            steps={
                "submit_application": SubmitApplicationStep(
                    name="submit_application",
                    description="Submit sponsorship application for review",
                ),
                "review_application": BaseHumanStep(
                    name="review_application",
                    title="Review Sponsorship Application",
                    description="Review the sponsorship application and approve or reject",
                    form_schema=APPROVAL_SCHEMA,
                ),
                "process_approval": ApproveApplicationStep(
                    name="process_approval",
                    description="Process the approval decision",
                ),
                "finalize_sponsorship": BaseHumanStep(
                    name="finalize_sponsorship",
                    title="Finalize Sponsorship",
                    description="Set dates and finalize the sponsorship agreement",
                    form_schema=FINALIZATION_SCHEMA,
                ),
                "complete_sponsorship": CompleteSponsorshipStep(
                    name="complete_sponsorship",
                    description="Complete the sponsorship finalization",
                ),
            },
            edges=[
                Edge("submit_application", "review_application"),
                Edge("review_application", "process_approval"),
                Edge("process_approval", "finalize_sponsorship"),
                Edge("finalize_sponsorship", "complete_sponsorship"),
            ],
            initial_step="submit_application",
            terminal_steps={"complete_sponsorship"},
        )


__all__ = [
    "SponsorContractWorkflow",
    "SponsorshipApprovalWorkflow",
]
