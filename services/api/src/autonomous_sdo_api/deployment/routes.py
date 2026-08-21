"""FastAPI routes for deployment, canary validation, and rollback."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from autonomous_sdo_api.database.tenancy import (
    OrganizationContext,
    get_organization_context,
)
from autonomous_sdo_api.deployment.models import (
    DeploymentApprovalModel,
    ReleasePlanModel,
)
from autonomous_sdo_api.deployment.service import DeploymentService

deployment_router = APIRouter(prefix="/api/v1/deployment", tags=["deployment"])

_deployment_service = DeploymentService()


@deployment_router.post(
    "/plans",
    response_model=ReleasePlanModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create a release plan",
)
async def create_release_plan(
    request: dict[str, Any],
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> ReleasePlanModel:
    plan = _deployment_service.create_release_plan(
        organization_id=context.organization_id,
        title=request.get("title", ""),
        version=request.get("version", ""),
        artifact_digest=request.get("artifact_digest", ""),
        artifact_image=request.get("artifact_image", ""),
        strategy=request.get("strategy", "rolling"),
        target_environment=request.get("target_environment", "staging"),
        created_by=str(context.actor_id),
        migrations=request.get("migrations"),
        canary_weight_percentage=request.get("canary_weight_percentage", 10),
        canary_duration_seconds=request.get("canary_duration_seconds", 300),
        slo_gates=request.get("slo_gates"),
    )
    return plan


@deployment_router.get(
    "/plans",
    response_model=list[ReleasePlanModel],
    summary="List all release plans for current organization",
)
async def list_release_plans(
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> list[ReleasePlanModel]:
    return _deployment_service.list_release_plans(context.organization_id)


@deployment_router.get(
    "/plans/{plan_id}",
    response_model=ReleasePlanModel,
    summary="Get a release plan by ID",
)
async def get_release_plan(
    plan_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> ReleasePlanModel:
    plan = _deployment_service.get_release_plan(plan_id, context.organization_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Release plan not found",
        )
    return plan


@deployment_router.post(
    "/plans/{plan_id}/approvals",
    response_model=DeploymentApprovalModel,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a purpose-bound deploy or rollback approval",
)
async def submit_approval(
    plan_id: str,
    request: dict[str, Any],
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> DeploymentApprovalModel:
    try:
        approval = _deployment_service.submit_approval(
            plan_id=plan_id,
            organization_id=context.organization_id,
            approver_id=str(context.actor_id),
            purpose=request.get("purpose", "deploy"),
            artifact_digest=request.get("artifact_digest", ""),
            notes=request.get("notes", ""),
            expires_in_hours=request.get("expires_in_hours", 24),
        )
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Release plan not found",
            )
        return approval
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


@deployment_router.post(
    "/plans/{plan_id}/deploy",
    response_model=ReleasePlanModel,
    summary="Start deployment execution",
)
async def start_deployment(
    plan_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> ReleasePlanModel:
    try:
        plan = _deployment_service.start_deployment(plan_id, context.organization_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Release plan not found",
            )
        return plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


@deployment_router.post(
    "/plans/{plan_id}/promote-canary",
    response_model=ReleasePlanModel,
    summary="Promote canary after SLO gates pass",
)
async def promote_canary(
    plan_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> ReleasePlanModel:
    try:
        plan = _deployment_service.promote_canary(plan_id, context.organization_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Release plan not found",
            )
        return plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


@deployment_router.post(
    "/plans/{plan_id}/rollback-request",
    response_model=ReleasePlanModel,
    summary="Request a separate rollback",
)
async def request_rollback(
    plan_id: str,
    request: dict[str, Any],
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> ReleasePlanModel:
    plan = _deployment_service.request_rollback(
        plan_id=plan_id,
        organization_id=context.organization_id,
        target_digest=request.get("target_digest", ""),
        requested_by=str(context.actor_id),
        reason=request.get("reason", "Rollback requested"),
    )
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Release plan not found",
        )
    return plan


@deployment_router.post(
    "/plans/{plan_id}/rollback-execute",
    response_model=ReleasePlanModel,
    summary="Execute rollback with distinct approval",
)
async def execute_rollback(
    plan_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> ReleasePlanModel:
    try:
        plan = _deployment_service.execute_rollback(plan_id, context.organization_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Release plan not found",
            )
        return plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
