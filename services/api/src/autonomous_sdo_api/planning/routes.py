from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.planning.models import (
    ApprovePlanRequest,
    ArchitecturePlan,
    BudgetExceededError,
    CreatePlanRequest,
    CyclicDependencyError,
    PlanningError,
    PlanNotFoundError,
)
from autonomous_sdo_api.planning.service import ArchitecturePlanningService
from autonomous_sdo_api.policy import Action, AuthorizationPolicy

router = APIRouter(prefix="/api/v1/planning/plans", tags=["Planning"])

_AUTH_POLICY = AuthorizationPolicy()
_SERVICE = ArchitecturePlanningService()


def get_planning_service() -> ArchitecturePlanningService:
    return _SERVICE


@router.post(
    "",
    response_model=ArchitecturePlan,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new architecture plan",
)
async def create_plan(
    payload: CreatePlanRequest,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    service: Annotated[ArchitecturePlanningService, Depends(get_planning_service)],
) -> ArchitecturePlan:
    _AUTH_POLICY.require(context.roles, Action.MANAGE_PLANS)
    try:
        return service.create_plan(
            org_id=context.organization_id,
            requirement_id=payload.requirement_id,
            revision_id=payload.revision_id,
            summary=payload.summary,
            work_packages=payload.work_packages,
            edges=payload.edges,
        )
    except (CyclicDependencyError, PlanningError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    except BudgetExceededError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err)
        ) from err


@router.get(
    "/{plan_id}",
    response_model=ArchitecturePlan,
    summary="Get architecture plan by ID",
)
async def get_plan(
    plan_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    service: Annotated[ArchitecturePlanningService, Depends(get_planning_service)],
) -> ArchitecturePlan:
    _AUTH_POLICY.require(context.roles, Action.READ_PLANS)
    try:
        return service.get_plan(context.organization_id, plan_id)
    except PlanNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.get(
    "",
    response_model=list[ArchitecturePlan],
    summary="List plans for a requirement",
)
async def list_plans(
    requirement_id: Annotated[str, Query(min_length=1)],
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    service: Annotated[ArchitecturePlanningService, Depends(get_planning_service)],
) -> list[ArchitecturePlan]:
    _AUTH_POLICY.require(context.roles, Action.READ_PLANS)
    return service.list_plans_for_requirement(context.organization_id, requirement_id)


@router.post(
    "/{plan_id}/approve",
    response_model=ArchitecturePlan,
    summary="Approve an architecture plan",
)
async def approve_plan(
    plan_id: str,
    payload: ApprovePlanRequest,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    service: Annotated[ArchitecturePlanningService, Depends(get_planning_service)],
) -> ArchitecturePlan:
    _AUTH_POLICY.require(context.roles, Action.MANAGE_PLANS)
    try:
        return service.approve_plan(
            org_id=context.organization_id,
            plan_id=plan_id,
            rationale=payload.rationale,
            approver_id=context.actor_id,
        )
    except PlanNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
