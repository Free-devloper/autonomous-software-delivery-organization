"""FastAPI routes for Coordinator Agent orchestration."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from autonomous_sdo_api.coordinator.models import MultiAgentPipelineRun
from autonomous_sdo_api.coordinator.service import CoordinatorAgentService
from autonomous_sdo_api.database.tenancy import (
    OrganizationContext,
    get_organization_context,
)

coordinator_router = APIRouter(prefix="/api/v1/coordinator", tags=["coordinator"])

_coordinator_service = CoordinatorAgentService()


@coordinator_router.post(
    "/pipelines",
    response_model=MultiAgentPipelineRun,
    status_code=status.HTTP_201_CREATED,
    summary="Start an orchestrated multi-specialist delivery pipeline",
)
async def start_pipeline(
    request: dict[str, Any],
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> MultiAgentPipelineRun:
    return _coordinator_service.start_pipeline(
        organization_id=context.organization_id,
        title=request.get("title", "End-to-End Autonomous Delivery"),
        requirement_id=request.get("requirement_id", "req-001"),
    )


@coordinator_router.get(
    "/pipelines",
    response_model=list[MultiAgentPipelineRun],
    summary="List all multi-agent pipeline executions",
)
async def list_pipelines(
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> list[MultiAgentPipelineRun]:
    return _coordinator_service.list_pipelines(context.organization_id)


@coordinator_router.get(
    "/pipelines/{pipeline_id}",
    response_model=MultiAgentPipelineRun,
    summary="Get a multi-agent pipeline execution by ID",
)
async def get_pipeline(
    pipeline_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> MultiAgentPipelineRun:
    run = _coordinator_service.get_pipeline(pipeline_id, context.organization_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found",
        )
    return run
