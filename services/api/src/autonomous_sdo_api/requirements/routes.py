from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.policy import Action, AuthorizationPolicy
from autonomous_sdo_api.requirements.models import (
    ClarificationNotFoundError,
    ClarificationRequest,
    CreateRequirementRequest,
    CreateRevisionRequest,
    RequestClarificationPayload,
    RequirementNotFoundError,
    RequirementRevision,
    ResolveClarificationRequest,
)
from autonomous_sdo_api.requirements.service import RequirementLifecycleService

router = APIRouter(prefix="/api/v1/requirements", tags=["Requirements"])

_AUTH_POLICY = AuthorizationPolicy()
_SERVICE = RequirementLifecycleService()


def get_requirement_service() -> RequirementLifecycleService:
    return _SERVICE


@router.post(
    "",
    response_model=RequirementRevision,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new requirement with initial version",
)
async def create_requirement(
    payload: CreateRequirementRequest,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    service: Annotated[RequirementLifecycleService, Depends(get_requirement_service)],
) -> RequirementRevision:
    _AUTH_POLICY.require(context.roles, Action.MANAGE_REQUIREMENTS)
    return service.create_requirement(
        org_id=context.organization_id,
        title=payload.title,
        description=payload.description,
        scope=payload.scope,
        criteria=payload.acceptance_criteria,
        author_id=context.actor_id,
    )


@router.get(
    "",
    response_model=list[RequirementRevision],
    summary="List all active requirements for organization",
)
async def list_requirements(
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    service: Annotated[RequirementLifecycleService, Depends(get_requirement_service)],
) -> list[RequirementRevision]:
    _AUTH_POLICY.require(context.roles, Action.READ_REQUIREMENTS)
    return service.list_all_requirements(context.organization_id)


@router.get(
    "/{requirement_id}",
    response_model=RequirementRevision,
    summary="Get latest revision of a requirement",
)
async def get_requirement(
    requirement_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    service: Annotated[RequirementLifecycleService, Depends(get_requirement_service)],
) -> RequirementRevision:
    _AUTH_POLICY.require(context.roles, Action.READ_REQUIREMENTS)
    try:
        return service.get_latest_revision(context.organization_id, requirement_id)
    except RequirementNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.get(
    "/{requirement_id}/revisions",
    response_model=list[RequirementRevision],
    summary="List all historical revisions of a requirement",
)
async def list_revisions(
    requirement_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    service: Annotated[RequirementLifecycleService, Depends(get_requirement_service)],
) -> list[RequirementRevision]:
    _AUTH_POLICY.require(context.roles, Action.READ_REQUIREMENTS)
    try:
        return service.list_revisions(context.organization_id, requirement_id)
    except RequirementNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post(
    "/{requirement_id}/revisions",
    response_model=RequirementRevision,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new version for an existing requirement",
)
async def create_revision(
    requirement_id: str,
    payload: CreateRevisionRequest,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    service: Annotated[RequirementLifecycleService, Depends(get_requirement_service)],
) -> RequirementRevision:
    _AUTH_POLICY.require(context.roles, Action.MANAGE_REQUIREMENTS)
    try:
        return service.create_revision(
            org_id=context.organization_id,
            requirement_id=requirement_id,
            title=payload.title,
            description=payload.description,
            scope=payload.scope,
            criteria=payload.acceptance_criteria,
            author_id=context.actor_id,
        )
    except RequirementNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post(
    "/{requirement_id}/clarifications",
    response_model=ClarificationRequest,
    status_code=status.HTTP_201_CREATED,
    summary="Request clarification on a requirement",
)
async def request_clarification(
    requirement_id: str,
    payload: RequestClarificationPayload,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    service: Annotated[RequirementLifecycleService, Depends(get_requirement_service)],
) -> ClarificationRequest:
    _AUTH_POLICY.require(context.roles, Action.MANAGE_REQUIREMENTS)
    try:
        return service.request_clarification(
            org_id=context.organization_id,
            requirement_id=requirement_id,
            question=payload.question,
            options=payload.options,
        )
    except RequirementNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.get(
    "/{requirement_id}/clarifications",
    response_model=list[ClarificationRequest],
    summary="List all clarification requests for a requirement",
)
async def list_clarifications(
    requirement_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    service: Annotated[RequirementLifecycleService, Depends(get_requirement_service)],
) -> list[ClarificationRequest]:
    _AUTH_POLICY.require(context.roles, Action.READ_REQUIREMENTS)
    try:
        return service.list_clarifications(context.organization_id, requirement_id)
    except RequirementNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post(
    "/{requirement_id}/clarifications/{clarification_id}/resolve",
    response_model=ClarificationRequest,
    summary="Resolve a pending clarification question",
)
async def resolve_clarification(
    requirement_id: str,
    clarification_id: str,
    payload: ResolveClarificationRequest,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    service: Annotated[RequirementLifecycleService, Depends(get_requirement_service)],
) -> ClarificationRequest:
    _AUTH_POLICY.require(context.roles, Action.MANAGE_REQUIREMENTS)
    try:
        return service.resolve_clarification(
            org_id=context.organization_id,
            requirement_id=requirement_id,
            clarification_id=clarification_id,
            response=payload.response,
        )
    except RequirementNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    except ClarificationNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
