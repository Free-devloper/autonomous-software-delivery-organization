"""FastAPI routes for code reviews and pull requests."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from autonomous_sdo_api.database.tenancy import (
    OrganizationContext,
    get_organization_context,
)
from autonomous_sdo_api.reviews.models import PullRequestModel, ReviewApprovalModel
from autonomous_sdo_api.reviews.service import ReviewService

review_router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

_review_service = ReviewService()


@review_router.post(
    "/pull-requests",
    response_model=PullRequestModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create a pull request",
)
async def create_pull_request(
    request: dict[str, Any],
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> PullRequestModel:
    pr = _review_service.create_pull_request(
        organization_id=context.organization_id,
        provider=request.get("provider", "github"),
        repository=request.get("repository", ""),
        title=request.get("title", ""),
        description=request.get("description", ""),
        source_branch=request.get("source_branch", ""),
        target_branch=request.get("target_branch", "main"),
        head_sha=request.get("head_sha", ""),
        author_id=str(context.actor_id),
    )
    return pr


@review_router.get(
    "/pull-requests",
    response_model=list[PullRequestModel],
    summary="List pull requests for organization",
)
async def list_pull_requests(
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> list[PullRequestModel]:
    return _review_service.list_pull_requests(context.organization_id)


@review_router.get(
    "/pull-requests/{pr_id}",
    response_model=PullRequestModel,
    summary="Get pull request by ID",
)
async def get_pull_request(
    pr_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> PullRequestModel:
    pr = _review_service.get_pull_request(pr_id, context.organization_id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pull request not found")
    return pr


@review_router.post(
    "/pull-requests/{pr_id}/comments",
    status_code=status.HTTP_201_CREATED,
    summary="Add a threaded comment to a PR",
)
async def add_comment(
    pr_id: str,
    request: dict[str, Any],
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> dict[str, str]:
    comment = _review_service.add_comment(
        pr_id,
        context.organization_id,
        author_id=str(context.actor_id),
        file_path=request.get("file_path", ""),
        line_number=request.get("line_number", 0),
        body=request.get("body", ""),
        parent_id=request.get("parent_id"),
    )
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pull request not found")
    return {"id": comment.id, "status": "created"}


@review_router.post(
    "/pull-requests/{pr_id}/approvals",
    response_model=ReviewApprovalModel,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a digest-bound approval",
)
async def submit_approval(
    pr_id: str,
    request: dict[str, Any],
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> ReviewApprovalModel:
    approval = _review_service.submit_approval(
        pr_id,
        context.organization_id,
        approver_id=str(context.actor_id),
        artifact_digest=request.get("artifact_digest", ""),
        scope=request.get("scope", ""),
        environment=request.get("environment", ""),
        expires_in_hours=request.get("expires_in_hours", 24),
    )
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot approve: PR not found, self-approval, or duplicate",
        )
    return approval


@review_router.post(
    "/pull-requests/{pr_id}/merge",
    response_model=PullRequestModel,
    summary="Merge a pull request",
)
async def merge_pull_request(
    pr_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> PullRequestModel:
    pr = _review_service.merge_pull_request(pr_id, context.organization_id)
    if not pr:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot merge: PR not found, already merged, no approvals, or duties violation",
        )
    return pr


@review_router.post(
    "/pull-requests/{pr_id}/check-staleness",
    summary="Check and invalidate stale approvals",
)
async def check_staleness(
    pr_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> dict[str, int]:
    count = _review_service.check_staleness(pr_id, context.organization_id)
    return {"stale_approvals_invalidated": count}
