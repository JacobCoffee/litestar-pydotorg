"""Workflow registry for managing workflow definitions."""

from __future__ import annotations

from litestar_workflows import WorkflowRegistry

# Global workflow registry instance
# All workflow definitions are registered here
workflow_registry = WorkflowRegistry()


def register_all_workflows() -> None:
    """Register all workflow definitions with the registry.

    This function is called during application startup to ensure
    all workflows are available before request handling begins.

    Workflows registered:
        - sponsor_contract: Contract lifecycle (draft → signature → executed)
        - sponsorship_approval: Sponsorship review (applied → approved/rejected → finalized)
        - job_posting: Job submission (draft → submitted → approved → published) [TODO]
        - event_submission: Community event moderation (submitted → approved/rejected) [TODO]
    """
    from pydotorg.core.workflows.definitions.sponsors import (
        SponsorContractWorkflow,
        SponsorshipApprovalWorkflow,
    )

    workflow_registry.register(SponsorContractWorkflow)
    workflow_registry.register(SponsorshipApprovalWorkflow)
