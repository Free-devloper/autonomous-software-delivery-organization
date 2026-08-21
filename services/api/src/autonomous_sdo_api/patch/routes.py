import os
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.patch.engine import PatchEngine
from autonomous_sdo_api.patch.models import (
    CreatePatchProposalRequest,
    PatchApplicationResult,
    PatchProposal,
    compute_patch_digest,
)

patch_router = APIRouter(prefix="/api/v1/patches", tags=["patches"])

# In-memory storage for patch proposals isolated by (organization_id, proposal_id)
_PROPOSALS: dict[tuple[UUID, str], PatchProposal] = {}


@patch_router.post(
    "/proposals",
    response_model=PatchProposal,
    status_code=status.HTTP_201_CREATED,
    summary="Create a content-addressed patch proposal",
)
async def create_patch_proposal(
    request: CreatePatchProposalRequest,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> PatchProposal:
    digest = compute_patch_digest(request.work_package_id, request.files)
    proposal = PatchProposal(
        organization_id=context.organization_id,
        work_package_id=request.work_package_id,
        summary=request.summary,
        digest_sha256=digest,
        files=request.files,
    )
    _PROPOSALS[(context.organization_id, proposal.id)] = proposal
    return proposal


@patch_router.get(
    "/proposals",
    response_model=list[PatchProposal],
    summary="List patch proposals for the current tenant",
)
async def list_patch_proposals(
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    work_package_id: str | None = Query(default=None),
) -> list[PatchProposal]:
    proposals = [p for (org_id, _), p in _PROPOSALS.items() if org_id == context.organization_id]
    if work_package_id:
        proposals = [p for p in proposals if p.work_package_id == work_package_id]
    return proposals


@patch_router.get(
    "/proposals/{proposal_id}",
    response_model=PatchProposal,
    summary="Get a patch proposal by ID",
)
async def get_patch_proposal(
    proposal_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> PatchProposal:
    proposal = _PROPOSALS.get((context.organization_id, proposal_id))
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patch proposal not found."
        )
    return proposal


@patch_router.post(
    "/proposals/{proposal_id}/apply",
    response_model=PatchApplicationResult,
    summary="Apply a patch proposal against the workspace",
)
async def apply_patch_proposal(
    proposal_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> PatchApplicationResult:
    proposal = _PROPOSALS.get((context.organization_id, proposal_id))
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patch proposal not found."
        )

    worktree_base = Path(os.getcwd()) / ".sandboxes" / "worktrees" / str(context.organization_id)
    worktree_base.mkdir(parents=True, exist_ok=True)

    result = PatchEngine.apply_proposal(worktree_base, proposal)
    return result
